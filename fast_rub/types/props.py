from collections.abc import MutableMapping
from typing import Any

class props(MutableMapping):
    """
    Wrapper حرفه‌ای برای dict و list با دسترسی هم با attribute و هم با index.
    """
    def __init__(self, data: Any):
        if isinstance(data, dict):
            self._data = {}
            for k, v in data.items():
                self._data[k] = self._wrap_value(v)
        elif isinstance(data, list):
            self._data = [self._wrap_value(v) for v in data]
        else:
            raise TypeError(f"props only accepts dict or list, got {type(data)}")

    def _wrap_value(self, value):
        if isinstance(value, dict) or isinstance(value, list):
            return props(value)
        return value

    # ---------------- Dict-like behavior ----------------
    def __getitem__(self, key):
        if isinstance(self._data, dict):
            return self._data[key]
        raise TypeError("Cannot use key indexing on a list")

    def __setitem__(self, key, value):
        if isinstance(self._data, dict):
            self._data[key] = self._wrap_value(value)
        else:
            raise TypeError("Cannot use key indexing on a list")

    def __delitem__(self, key):
        if isinstance(self._data, dict):
            del self._data[key]
        else:
            raise TypeError("Cannot use key indexing on a list")

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    # ---------------- Attribute-like behavior ----------------
    def __getattr__(self, name):
        if isinstance(self._data, dict):
            if name in self._data:
                return self._data[name]
            raise AttributeError(f"'props' object has no attribute '{name}'")
        raise AttributeError(f"'props' object is a list, cannot access '{name}' as attribute")

    def __setattr__(self, name, value):
        if name == "_data":
            super().__setattr__(name, value)
        elif isinstance(self._data, dict):
            self._data[name] = self._wrap_value(value)
        else:
            raise AttributeError(f"'props' object is a list, cannot set attribute '{name}'")

    # ---------------- List-like behavior ----------------
    def __getitem_list__(self, index):
        if isinstance(self._data, list):
            return self._data[index]
        raise TypeError("Cannot index a dict with integer")

    def __setitem_list__(self, index, value):
        if isinstance(self._data, list):
            self._data[index] = self._wrap_value(value)
        else:
            raise TypeError("Cannot index a dict with integer")

    # ---------------- String / Representation ----------------
    def __repr__(self):
        return f"props({self._data!r})"

    def __str__(self):
        import json
        return json.dumps(self._to_primitive(self._data), indent=4, ensure_ascii=False)

    def _to_primitive(self, value):
        if isinstance(value, props):
            return self._to_primitive(value._data)
        elif isinstance(value, dict):
            return {k: self._to_primitive(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._to_primitive(v) for v in value]
        else:
            return value

    # ---------------- Helpers ----------------
    def to_dict(self):
        """بازگرداندن dict/list خام"""
        return self._to_primitive(self._data)
