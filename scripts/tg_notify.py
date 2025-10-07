"""Telegram notification helper for marine ingest workflows."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Optional

import requests

API_BASE = "https://api.telegram.org/bot{token}/{method}"
DEFAULT_TIMEOUT = 20


class TelegramError(RuntimeError):
    """Raised when Telegram API responses indicate failure."""


def _get_credentials() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        missing = [name for name, value in [("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id)] if not value]
        raise TelegramError(f"Missing environment variables: {', '.join(missing)}")
    return token, chat_id


def send_message(text: str, html: bool = False, disable_preview: bool = True) -> dict:
    token, chat_id = _get_credentials()
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_preview,
    }
    if html:
        payload["parse_mode"] = "HTML"
    response = requests.post(
        API_BASE.format(token=token, method="sendMessage"),
        json=payload,
        timeout=DEFAULT_TIMEOUT,
    )
    return _handle_response(response)


def send_document(path: Path, caption: Optional[str] = None) -> dict:
    token, chat_id = _get_credentials()
    if not path.exists():
        raise TelegramError(f"Document not found: {path}")
    files = {"document": (path.name, path.open("rb"))}
    data = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    try:
        response = requests.post(
            API_BASE.format(token=token, method="sendDocument"),
            data=data,
            files=files,
            timeout=DEFAULT_TIMEOUT,
        )
    finally:
        files["document"][1].close()
    return _handle_response(response)


def _handle_response(response: requests.Response) -> dict:
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        raise TelegramError(f"HTTP error: {exc}") from exc
    data = response.json()
    if not data.get("ok", False):
        raise TelegramError(f"Telegram API error: {data}")
    return data


def _load_text(source: str) -> str:
    path = Path(source)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send Telegram notifications.")
    parser.add_argument(
        "--text",
        dest="text_source",
        help="Inline text or path to file containing message body",
    )
    parser.add_argument(
        "--html",
        action="store_true",
        help="Enable HTML parse_mode for the message",
    )
    parser.add_argument(
        "--document",
        dest="document",
        help="Optional document to upload",
    )
    parser.add_argument(
        "--caption",
        dest="caption",
        help="Caption to accompany uploaded document",
    )
    parser.add_argument(
        "--skip-message",
        action="store_true",
        help="Only send document without text message",
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if not args.skip_message:
            if not args.text_source:
                raise TelegramError("--text is required unless --skip-message is used")
            body = _load_text(args.text_source)
            send_message(body, html=args.html)
        if args.document:
            send_document(Path(args.document), caption=args.caption)
    except TelegramError as exc:
        print(f"[TELEGRAM] {exc}", file=sys.stderr)
        return 1
    except requests.exceptions.RequestException as exc:
        print(f"[TELEGRAM] Request failed: {exc}", file=sys.stderr)
        return 2
    print("[TELEGRAM] Notification sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
