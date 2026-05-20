from __future__ import annotations

import importlib
from typing import Any


def dynamic_import(module_path: str, attr_name: str) -> Any:
    """
    动态导入模块属性。

    对齐 internal.lib.helper.dynamic_import 行为：
    - import module
    - getattr attr
    """

    module = importlib.import_module(module_path)
    return getattr(module, attr_name)
