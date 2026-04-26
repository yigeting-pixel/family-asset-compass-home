
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def export_family_snapshot(path: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def import_family_snapshot(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


PRIVACY_STATEMENT = """
家庭版默认本地运行，输入数据保存在本机或浏览器会话中，不需要上传到第三方服务器。
如果未来发布小程序版，建议提供“本地演示模式”和“云端同步模式”两个选项，并清楚告知用户数据用途。
"""
