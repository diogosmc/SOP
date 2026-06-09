"""Tests for Telegram message formatting."""

from app.telegram.formatter import (
    format_telegram_reply,
    markdown_to_telegram_html,
    telegram_reply_kwargs,
)


def test_markdown_bold_to_html() -> None:
    html = markdown_to_telegram_html("**Amanhã — seu dia:**")
    assert html == "<b>Amanhã — seu dia:</b>"


def test_markdown_list_item_bold() -> None:
    html = markdown_to_telegram_html("1. **06:20** — Acordar (alarme)")
    assert "<b>06:20</b>" in html
    assert "Acordar" in html


def test_markdown_escapes_user_html() -> None:
    html = markdown_to_telegram_html("Use a <tag> & **negrito**")
    assert "&lt;tag&gt;" in html
    assert "<b>negrito</b>" in html


def test_telegram_reply_kwargs_includes_parse_mode() -> None:
    kwargs = telegram_reply_kwargs("**Olá**")
    assert kwargs["parse_mode"] == "HTML"
    assert "<b>Olá</b>" in kwargs["text"]


def test_format_telegram_reply_plain() -> None:
    assert format_telegram_reply("  texto  ") == "texto"
