import smtplib
import ssl
from email.message import EmailMessage

import requests
from flask import current_app
from redis import Redis

from internal.exception import FailException


_ACCESS_TOKEN_KEY = "smtp:oauth:access_token"
_REFRESH_TOKEN_KEY = "smtp:oauth:refresh_token"


def _as_text(value: bytes | str | None) -> str | None:
    if value is None:
        return None
    return value.decode("utf-8") if isinstance(value, bytes) else value


def _get_oauth_access_token(redis_client: Redis) -> str:
    config = current_app.config
    cached_token = _as_text(redis_client.get(_ACCESS_TOKEN_KEY))
    if cached_token:
        return cached_token

    client_id = config.get("SMTP_CLIENT_ID")
    if not client_id:
        raise FailException("Outlook 邮件尚未配置，请填写 SMTP_CLIENT_ID。")

    refresh_token = _as_text(redis_client.get(_REFRESH_TOKEN_KEY))
    refresh_token = refresh_token or config.get("SMTP_REFRESH_TOKEN")
    if not refresh_token:
        raise FailException(
            "Outlook 邮件尚未授权，请运行 scripts/configure_outlook_oauth.py 完成授权。"
        )

    tenant = config.get("SMTP_TENANT") or "consumers"
    token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
    try:
        response = requests.post(
            token_url,
            data={
                "client_id": client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": "offline_access https://outlook.office.com/SMTP.Send",
            },
            timeout=15,
        )
        token_response = response.json()
    except (requests.RequestException, ValueError) as error:
        raise FailException("无法连接 Microsoft OAuth 服务，请稍后重试。") from error

    if not isinstance(token_response, dict):
        raise FailException("Microsoft OAuth 返回了无法识别的授权结果。")
    access_token = token_response.get("access_token")
    if response.status_code >= 400 or not access_token:
        # Do not include Microsoft's response body: it can contain credential details.
        raise FailException(
            "Outlook OAuth 授权已失效或配置不正确，请重新运行 Outlook 授权脚本。"
        )

    try:
        expires_in = int(token_response.get("expires_in", 3600))
    except (TypeError, ValueError):
        expires_in = 3600
    if expires_in > 60:
        redis_client.set(_ACCESS_TOKEN_KEY, access_token, ex=expires_in - 60)

    # Microsoft can rotate refresh tokens. Keep the newest one in Redis so a
    # container restart does not require a new interactive authorization.
    rotated_refresh_token = token_response.get("refresh_token")
    if rotated_refresh_token:
        redis_client.set(_REFRESH_TOKEN_KEY, rotated_refresh_token)

    return access_token


def _send_with_oauth2(
    smtp: smtplib.SMTP, username: str, access_token: str
) -> None:
    xoauth2 = f"user={username}\x01auth=Bearer {access_token}\x01\x01".encode(
        "utf-8"
    )
    smtp.auth("XOAUTH2", lambda _challenge=None: xoauth2)


def send_email(
    to_email: str, subject: str, body: str, redis_client: Redis
) -> None:
    """Send a plain-text email using password SMTP or Outlook OAuth2."""
    config = current_app.config
    common_settings = (
        "SMTP_SERVER",
        "SMTP_PORT",
        "SENDER_EMAIL",
        "SMTP_USERNAME",
    )
    missing_settings = [key for key in common_settings if not config.get(key)]
    auth_method = config.get("SMTP_AUTH_METHOD", "password").lower()
    if auth_method == "oauth2":
        if not config.get("SMTP_CLIENT_ID"):
            missing_settings.append("SMTP_CLIENT_ID")
        if not config.get("SMTP_REFRESH_TOKEN") and not redis_client.get(
            _REFRESH_TOKEN_KEY
        ):
            missing_settings.append("SMTP_REFRESH_TOKEN")
    elif auth_method == "password":
        if not config.get("SMTP_PASSWORD"):
            missing_settings.append("SMTP_PASSWORD")
    else:
        raise FailException("SMTP_AUTH_METHOD 只支持 password 或 oauth2。")

    if missing_settings:
        raise FailException(
            "邮件服务尚未配置，请检查 docker/.env 中的 SMTP 服务地址、发件邮箱和认证配置。"
        )

    message = EmailMessage()
    message["From"] = config["SENDER_EMAIL"]
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    try:
        access_token = (
            _get_oauth_access_token(redis_client) if auth_method == "oauth2" else None
        )
        if config["SMTP_USE_SSL"]:
            with smtplib.SMTP_SSL(
                config["SMTP_SERVER"],
                config["SMTP_PORT"],
                timeout=15,
                context=context,
            ) as smtp:
                if auth_method == "oauth2":
                    _send_with_oauth2(smtp, config["SMTP_USERNAME"], access_token)
                else:
                    smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
                smtp.send_message(message)
            return

        with smtplib.SMTP(
            config["SMTP_SERVER"], config["SMTP_PORT"], timeout=15
        ) as smtp:
            smtp.ehlo()
            if config["SMTP_USE_TLS"]:
                smtp.starttls(context=context)
                smtp.ehlo()
            if auth_method == "oauth2":
                _send_with_oauth2(smtp, config["SMTP_USERNAME"], access_token)
            else:
                smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, requests.RequestException) as error:
        current_app.logger.error("Failed to send verification email")
        raise FailException("验证码邮件发送失败，请检查 SMTP 服务配置后重试。") from error
