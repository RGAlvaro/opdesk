"""Shared metadata normalization and validation helpers for SPEC-308."""

import re
from decimal import Decimal
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.api.errors import APIError

LOCALE_PATTERN = re.compile(r"^[A-Za-z]{2,3}(?:[-_][A-Za-z0-9]{2,8})*$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def optional_string(value: str | None, *, max_length: int, code: str, field: str) -> str | None:
    """Trim optional text, convert blanks to null, and enforce max length."""
    if value is None:
        return None
    normalized = value.strip()
    if normalized == "":
        return None
    if len(normalized) > max_length:
        raise APIError(400, code, f"{field} must be {max_length} characters or fewer.")
    return normalized


def optional_url(value: str | None, *, code: str, field: str) -> str | None:
    """Accept only http and https URL metadata while allowing null values."""
    normalized = optional_string(value, max_length=2048, code=code, field=field)
    if normalized is None:
        return None
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise APIError(400, code, f"{field} must be an http or https URL.")
    return normalized


def optional_email(value: str | None, *, code: str, field: str) -> str | None:
    """Normalize optional email fields to lowercase with a practical shape check."""
    normalized = optional_string(value, max_length=320, code=code, field=field)
    if normalized is None:
        return None
    email = normalized.lower()
    if EMAIL_PATTERN.fullmatch(email) is None:
        raise APIError(400, code, f"{field} must be a valid email address.")
    return email


def optional_timezone(value: str | None) -> str | None:
    """Validate optional IANA timezone names for profile metadata."""
    normalized = optional_string(value, max_length=120, code="invalid_profile", field="timezone")
    if normalized is None:
        return None
    try:
        ZoneInfo(normalized)
    except ZoneInfoNotFoundError as exc:
        raise APIError(400, "invalid_profile", "Timezone must be a valid IANA name.") from exc
    return normalized


def optional_locale(value: str | None) -> str | None:
    """Validate optional locale tags with a conservative BCP-47-style pattern."""
    normalized = optional_string(value, max_length=40, code="invalid_profile", field="locale")
    if normalized is None:
        return None
    if LOCALE_PATTERN.fullmatch(normalized) is None:
        raise APIError(400, "invalid_profile", "Locale must be a valid language tag.")
    return normalized.replace("_", "-")


def non_negative_decimal(value: Decimal | None, *, code: str, field: str) -> Decimal | None:
    """Validate optional decimal quantities that cannot be negative."""
    if value is None:
        return None
    if value < 0:
        raise APIError(400, code, f"{field} must be non-negative.")
    return value


def currency_code(value: str | None, *, required: bool) -> str | None:
    """Normalize optional project currency codes to three uppercase letters."""
    normalized = optional_string(
        value, max_length=3, code="invalid_project", field="budget_currency"
    )
    if normalized is None:
        if required:
            raise APIError(
                400,
                "invalid_project",
                "Budget currency is required when budget amount is provided.",
            )
        return None
    currency = normalized.upper()
    if len(currency) != 3 or not currency.isalpha():
        raise APIError(400, "invalid_project", "Budget currency must be three letters.")
    return currency
