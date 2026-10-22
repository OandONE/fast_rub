from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any


class Context(Mapping[str, Any]):
    """Layered template context; child scopes do not overwrite parent values"""

    __slots__ = ("_values", "_parent")

    def __init__(
        self,
        values: Mapping[str, Any] | None = None,
        parent: "Context | None" = None,
    ) -> None:
        self._values = dict(values or {})
        self._parent = parent

    def resolve(self, key: str, default: Any = None) -> Any:
        if key in self._values:
            return self._values[key]
        if self._parent is not None:
            return self._parent.resolve(key, default)
        return default

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value

    def child(self, values: Mapping[str, Any] | None = None) -> "Context":
        return Context(values, parent=self)

    def flatten(self) -> dict[str, Any]:
        values = self._parent.flatten() if self._parent is not None else {}
        values.update(self._values)
        return values

    def __getitem__(self, key: str) -> Any:
        marker = object()
        value = self.resolve(key, marker)
        if value is marker:
            raise KeyError(key)
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self.flatten())

    def __len__(self) -> int:
        return len(self.flatten())
