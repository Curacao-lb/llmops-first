#!/usr/bin/env python3
"""Authorize a personal Outlook.com account for SMTP and save credentials locally."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "docker" / ".env"
AUTHORITY = "https://login.microsoftonline.com/consumers/oauth2/v2.0"
SCOPES = "offline_access https://outlook.office.com/SMTP.Send"


def post_form(url: str, values: dict[str, str]) -> dict:
    request = Request(
        url,
        data=urlencode(values).encode("ascii"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            payload = json.loads(error.read().decode("utf-8"))
            detail = payload.get("error_description") or payload.get("error")
        except (ValueError, AttributeError):
            detail = None
        raise RuntimeError(detail or f"Microsoft returned HTTP {error.code}.") from None
    except (URLError, TimeoutError, ValueError) as error:
        raise RuntimeError("Could not reach Microsoft sign-in: " + str(error)) from None
    if not isinstance(payload, dict):
        raise RuntimeError("Microsoft returned an unexpected response.")
    return payload


def read_env() -> list[str]:
    if not ENV_FILE.is_file():
        raise RuntimeError(
            "docker/.env does not exist. Copy docker/.env.example to docker/.env first."
        )
    return ENV_FILE.read_text(encoding="utf-8").splitlines()


def env_value(lines: list[str], key: str) -> str:
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=(.*)$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip("\"'")
    return ""


def write_env(values: dict[str, str]) -> None:
    lines = read_env()
    pending = dict(values)
    result: list[str] = []
    for line in lines:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        key = match.group(1) if match else None
        if key in pending:
            result.append(f"{key}={pending.pop(key)}")
        elif key in values:
            # Do not leave duplicate active entries; Compose's dotenv parser
            # would otherwise choose one depending on which copy comes last.
            continue
        else:
            result.append(line)
    if pending:
        if result and result[-1]:
            result.append("")
        result.extend(f"{key}={value}" for key, value in pending.items())

    ENV_FILE.write_text("\n".join(result) + "\n", encoding="utf-8")
    os.chmod(ENV_FILE, stat.S_IRUSR | stat.S_IWUSR)


def request_user_value(prompt: str, existing_value: str = "") -> str:
    if existing_value:
        return existing_value
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This value is required.")


def acquire_refresh_token(client_id: str) -> str:
    device = post_form(
        f"{AUTHORITY}/devicecode",
        {"client_id": client_id, "scope": SCOPES},
    )
    device_code = device.get("device_code")
    user_code = device.get("user_code")
    verification_uri = device.get("verification_uri")
    if not all((device_code, user_code, verification_uri)):
        raise RuntimeError("Microsoft did not return a device sign-in code.")

    print("\n在浏览器打开这个微软登录页面：")
    print(verification_uri)
    print("输入一次性设备码：" + user_code)
    print("使用发件 Outlook 账号登录并同意 SMTP.Send 权限。\n")

    expires_at = time.monotonic() + int(device.get("expires_in", 900))
    interval = max(1, int(device.get("interval", 5)))
    while time.monotonic() < expires_at:
        time.sleep(interval)
        try:
            token = post_form(
                f"{AUTHORITY}/token",
                {
                    "client_id": client_id,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                },
            )
        except RuntimeError as error:
            error_code = str(error)
            if "authorization_pending" in error_code:
                continue
            if "slow_down" in error_code:
                interval += 5
                continue
            raise

        refresh_token = token.get("refresh_token")
        if refresh_token:
            return refresh_token
        if token.get("error") == "authorization_pending":
            continue
        raise RuntimeError("Microsoft sign-in completed without a refresh token.")

    raise RuntimeError("The device sign-in code expired. Run this script again.")


def main() -> int:
    try:
        lines = read_env()
        client_id = request_user_value(
            "Microsoft Entra Application (client) ID: ",
            env_value(lines, "SMTP_CLIENT_ID"),
        )
        sender_email = request_user_value(
            "Outlook.com sender email address: ", env_value(lines, "SENDER_EMAIL")
        )
        refresh_token = acquire_refresh_token(client_id)
        write_env(
            {
                "SMTP_SERVER": "smtp-mail.outlook.com",
                "SMTP_PORT": "587",
                "SENDER_EMAIL": sender_email,
                "SMTP_USERNAME": sender_email,
                "SMTP_PASSWORD": "",
                "SMTP_AUTH_METHOD": "oauth2",
                "SMTP_CLIENT_ID": client_id,
                "SMTP_REFRESH_TOKEN": refresh_token,
                "SMTP_TENANT": "consumers",
                "SMTP_USE_SSL": "false",
                "SMTP_USE_TLS": "true",
            }
        )
    except (RuntimeError, OSError, KeyboardInterrupt) as error:
        if isinstance(error, KeyboardInterrupt):
            print("\nAuthorization cancelled.", file=sys.stderr)
        else:
            print(f"Outlook setup failed: {error}", file=sys.stderr)
        return 1

    print("\nOutlook OAuth settings saved in docker/.env (file permissions set to 600).")
    print("Recreate the API and worker containers to load the new settings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
