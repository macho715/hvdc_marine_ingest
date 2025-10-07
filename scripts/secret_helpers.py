"""KR: 시크릿 로드/마스킹 유틸 / EN: Helpers to load and mask secrets."""
from __future__ import annotations

import os
from typing import Final

MISSING_MARK: Final[str] = "[missing]"


def load_secret(name: str, allow_empty: bool = False) -> str:
    """KR: 환경 시크릿 로드 / EN: Load secret from environment."""
    value = os.getenv(name, "").strip()
    if value:
        return value
    if allow_empty:
        return ""
    raise RuntimeError(
        f"환경 변수 {name}이(가) 설정되지 않았습니다. "
        "GitHub Secrets 또는 .env 파일을 확인하세요."
    )


def mask_secret(value: str) -> str:
    """KR: 시크릿 마스킹 / EN: Mask secret for logs."""
    if not value:
        return MISSING_MARK
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"

