"""Shared helpers for Conversation Brain."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from app.core.config import get_settings


def local_today() -> date:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz).date()


def coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return None


def parse_relative_datetime(text: str) -> datetime | None:
    lowered = text.lower()
    tz = ZoneInfo(get_settings().timezone)
    today = local_today()

    if "amanhã" in lowered or "amanha" in lowered:
        target = today + timedelta(days=1)
        return datetime(target.year, target.month, target.day, 9, 0, tzinfo=tz)
    if "hoje" in lowered:
        return datetime(today.year, today.month, today.day, 18, 0, tzinfo=tz)
    return None


def extract_expense_details(text: str, entities: dict[str, Any]) -> tuple[Decimal, str, str]:
    amount = entities.get("amount")
    if amount is None:
        match = re.search(r"(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", text, re.IGNORECASE)
        if match:
            amount = float(match.group(1).replace(",", "."))
    if amount is None:
        amount = 0

    lowered = text.lower()
    category = "outros"
    for keyword, cat in (
        ("lanche", "alimentação"),
        ("almoço", "alimentação"),
        ("almoco", "alimentação"),
        ("jantar", "alimentação"),
        ("mercado", "alimentação"),
        ("uber", "transporte"),
        ("ônibus", "transporte"),
        ("onibus", "transporte"),
        ("gasolina", "transporte"),
    ):
        if keyword in lowered:
            category = cat
            break

    description = text.strip()[:500] or "Gasto registrado"
    return Decimal(str(amount)), category, description
