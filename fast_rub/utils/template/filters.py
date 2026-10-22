from __future__ import annotations

import html
import json
from collections.abc import Mapping
from typing import Any, Callable


Filter = Callable[..., Any]


def _default(value: Any, fallback: Any = "", use_for_falsey: bool = False) -> Any:
    if value is None or getattr(value, "is_undefined", False):
        return fallback
    if use_for_falsey and not value:
        return fallback
    return value


def _join(value: Any, separator: str = "") -> str:
    if value is None or getattr(value, "is_undefined", False):
        return ""
    return str(separator).join(str(item) for item in value)


def _length(value: Any) -> int:
    try:
        return len(value)
    except (TypeError, AttributeError):
        return 0


def _items(value: Any) -> list[tuple[Any, Any]]:
    if isinstance(value, Mapping):
        return list(value.items())
    return []


def _tojson(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


DEFAULT_FILTERS: dict[str, Filter] = {
    "default": _default,
    "d": _default,
    "upper": lambda value: str(value).upper(),
    "lower": lambda value: str(value).lower(),
    "title": lambda value: str(value).title(),
    "capitalize": lambda value: str(value).capitalize(),
    "trim": lambda value: str(value).strip(),
    "length": _length,
    "count": _length,
    "join": _join,
    "first": lambda value: next(iter(value), "") if value is not None else "",
    "last": lambda value: next(reversed(value), "") if value else "",
    "replace": lambda value, old, new: str(value).replace(str(old), str(new)),
    "int": lambda value, default=0: _safe_number(value, int, default),
    "float": lambda value, default=0.0: _safe_number(value, float, default),
    "string": lambda value: str(value),
    "list": lambda value: list(value) if value is not None else [],
    "sort": lambda value: sorted(value) if value is not None else [],
    "reverse": lambda value: list(reversed(value)) if value is not None else [],
    "items": _items,
    "escape": lambda value: html.escape(str(value), quote=True),
    "e": lambda value: html.escape(str(value), quote=True),
    "tojson": _tojson,
}


def _safe_number(value: Any, converter: Callable[[Any], Any], fallback: Any) -> Any:
    try:
        return converter(value)
    except (TypeError, ValueError, OverflowError):
        return fallback


def split_filter_chain(expression: str) -> list[str]:
    """Split at top-level pipes without splitting strings or nested arguments"""
    parts: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    depth = 0
    for index, char in enumerate(expression):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        elif char == "|" and depth == 0:
            parts.append(expression[start:index].strip())
            start = index + 1
    parts.append(expression[start:].strip())
    return parts


def split_arguments(value: str) -> list[str]:
    if not value.strip():
        return []
    parts: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    depth = 0
    for index, char in enumerate(value):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(value[start:index].strip())
            start = index + 1
    parts.append(value[start:].strip())
    return parts
