"""Composable filters for outgoing JSON/API requests."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


class RequestFilter:
    """A synchronous predicate that decides whether a request hook should run

    Filters can be composed with ``&`` (AND), ``|`` (OR), and ``~`` (NOT)
    A filter never changes the request payload; it only returns a boolean
    """

    def __init__(
        self,
        predicate: Callable[[Mapping[str, Any]], bool],
        *,
        name: str | None = None,
    ) -> None:
        if not callable(predicate):
            raise TypeError("predicate باید callable باشد")
        self._predicate = predicate
        self.name = name or getattr(predicate, "__name__", "custom")

    def matches(
        self,
        *,
        method: str,
        data: Any,
        url: str,
        api_method: str | None = None,
        http_method: str | None = None,
        client: Any = None,
        **_: Any,
    ) -> bool:
        """Return whether the request context matches this filter."""
        context = {
            "method": method,
            "http_method": http_method or method,
            "api_method": api_method,
            "data": data,
            "url": url,
            "client": client,
        }
        result = self._predicate(context)
        if not isinstance(result, bool):
            raise TypeError(
                f"RequestFilter predicate must return bool, got {type(result).__name__}"
            )
        return result

    @staticmethod
    def _require_values(name: str, values: tuple[str, ...]) -> tuple[str, ...]:
        if not values:
            raise ValueError(f"{name} requires at least one value")
        if any(not isinstance(value, str) for value in values):
            raise TypeError(f"All {name} values must be strings")
        return values

    @classmethod
    def api_method(cls, *methods: str) -> RequestFilter:
        """Match one of the exact Rubika API method names (e.g. ``getUpdates``)."""
        accepted = frozenset(cls._require_values("api_method", methods))
        return cls(
            lambda context: context.get("api_method") in accepted,
            name=f"api_method({', '.join(methods)})",
        )

    @classmethod
    def http_method(cls, *methods: str) -> RequestFilter:
        """Match one or more HTTP methods, case-insensitively."""
        accepted = frozenset(
            value.upper() for value in cls._require_values("http_method", methods)
        )
        return cls(
            lambda context: str(
                context.get("http_method") or context.get("method") or ""
            ).upper() in accepted,
            name=f"http_method({', '.join(methods)})",
        )

    @classmethod
    def url_contains(cls, *parts: str) -> RequestFilter:
        """Match when the URL contains any supplied substring."""
        parts = cls._require_values("url_contains", parts)
        return cls(
            lambda context: any(part in str(context.get("url") or "") for part in parts),
            name=f"url_contains({', '.join(parts)})",
        )

    @classmethod
    def url_startswith(cls, *prefixes: str) -> RequestFilter:
        """Match when the URL starts with any supplied prefix."""
        prefixes = cls._require_values("url_startswith", prefixes)
        return cls(
            lambda context: str(context.get("url") or "").startswith(prefixes),
            name=f"url_startswith({', '.join(prefixes)})",
        )

    @classmethod
    def data_has(cls, *keys: str) -> RequestFilter:
        """Match when the payload mapping contains every supplied key."""
        keys = cls._require_values("data_has", keys)
        return cls(
            lambda context: isinstance(context.get("data"), Mapping)
            and all(key in context["data"] for key in keys),
            name=f"data_has({', '.join(keys)})",
        )

    @classmethod
    def data_equals(cls, key: str, value: Any) -> RequestFilter:
        """Match when the payload contains ``key`` and its value equals ``value``."""
        if not isinstance(key, str):
            raise TypeError("key must be a string")
        return cls(
            lambda context: isinstance(context.get("data"), Mapping)
            and key in context["data"]
            and context["data"][key] == value,
            name=f"data_equals({key!r}, {value!r})",
        )

    def __and__(self, other: RequestFilter) -> RequestFilter:
        if not isinstance(other, RequestFilter):
            return NotImplemented
        return RequestFilter(
            lambda context: self._predicate_matches_context(context)
            and other._predicate_matches_context(context),
            name=f"({self!r} & {other!r})",
        )

    def __or__(self, other: RequestFilter) -> RequestFilter:
        if not isinstance(other, RequestFilter):
            return NotImplemented
        return RequestFilter(
            lambda context: self._predicate_matches_context(context)
            or other._predicate_matches_context(context),
            name=f"({self!r} | {other!r})",
        )

    def __invert__(self) -> RequestFilter:
        return RequestFilter(
            lambda context: not self._predicate_matches_context(context),
            name=f"~{self!r}",
        )

    def _predicate_matches_context(self, context: Mapping[str, Any]) -> bool:
        result = self._predicate(context)
        if not isinstance(result, bool):
            raise TypeError(
                f"RequestFilter predicate must return bool, got {type(result).__name__}"
            )
        return result

    def __repr__(self) -> str:
        return f"RequestFilter({self.name})"
