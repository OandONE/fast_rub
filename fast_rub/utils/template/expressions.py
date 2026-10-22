from __future__ import annotations

import ast
import operator
import re
from collections.abc import Mapping
from typing import Any

from .exceptions import TemplateExpressionError
from .filters import DEFAULT_FILTERS, split_arguments, split_filter_chain


class Undefined:
    """Undefined template value. It behaves as an empty and false value"""

    __slots__ = ("name",)
    is_undefined = True

    def __init__(self, name: str = "") -> None:
        self.name = name

    def __str__(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"Undefined({self.name!r})"

    def __bool__(self) -> bool:
        return False

    def __getattr__(self, name: str) -> "Undefined":
        if name.startswith("_"):
            raise AttributeError(name)
        return Undefined(f"{self.name}.{name}".strip("."))

    def __getitem__(self, key: Any) -> "Undefined":
        return Undefined(f"{self.name}[{key!r}]")


class _DefinedSentinel:
    pass


DEFINED = _DefinedSentinel()
SAFE_FUNCTIONS = {
    "range": range,
    "len": len,
    "enumerate": enumerate,
    "zip": zip,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "abs": abs,
    "round": round,
}

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_CMPOPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
}


def evaluate(expression: str, context: Mapping[str, Any], filters: Mapping[str, Any] | None = None) -> Any:
    """Evaluate a restricted expression and a chain of registered filters"""
    pieces = split_filter_chain(expression)
    if not pieces or not pieces[0]:
        raise TemplateExpressionError("Empty template expression")

    value = _evaluate_python_expression(pieces[0], context)
    filter_registry = dict(DEFAULT_FILTERS)
    if filters:
        filter_registry.update(filters)

    for spec in pieces[1:]:
        match = re.fullmatch(r"([A-Za-z_]\w*)\s*(?:\((.*)\))?", spec, flags=re.DOTALL)
        if not match:
            raise TemplateExpressionError(f"Invalid filter syntax: {spec!r}")
        name, raw_args = match.groups()
        function = filter_registry.get(name)
        if function is None:
            raise TemplateExpressionError(f"Unknown template filter: {name!r}")
        args = [
            _evaluate_python_expression(arg, context)
            for arg in split_arguments(raw_args or "")
        ]
        try:
            value = function(value, *args)
        except Exception as error:
            raise TemplateExpressionError(f"Filter {name!r} failed: {error}") from error
    return value


def _evaluate_python_expression(expression: str, context: Mapping[str, Any]) -> Any:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise TemplateExpressionError(f"Invalid expression {expression!r}: {error.msg}") from error
    try:
        return _eval(tree.body, context)
    except TemplateExpressionError:
        raise
    except Exception as error:
        raise TemplateExpressionError(f"Could not evaluate {expression!r}: {error}") from error


def _lookup(context: Mapping[str, Any], name: str) -> Any:
    if name in ("true", "True"):
        return True
    if name in ("false", "False"):
        return False
    if name in ("none", "None", "null", "Null"):
        return None
    if name == "defined":
        return DEFINED
    try:
        return context[name]
    except (KeyError, TypeError):
        resolver = getattr(context, "resolve", None)
        if resolver is not None:
            value = resolver(name, Undefined(name))
            return value
        return Undefined(name)


def _attribute(value: Any, name: str) -> Any:
    if name.startswith("_"):
        return Undefined(name)
    if isinstance(value, Mapping):
        return value.get(name, Undefined(name))
    try:
        return getattr(value, name)
    except (AttributeError, TypeError):
        return Undefined(name)


def _eval(node: ast.AST, context: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return _lookup(context, node.id)
    if isinstance(node, ast.Attribute):
        return _attribute(_eval(node.value, context), node.attr)
    if isinstance(node, ast.Subscript):
        value = _eval(node.value, context)
        key = _eval(node.slice, context)
        try:
            return value[key]
        except (KeyError, IndexError, TypeError):
            return Undefined(f"{value!s}[{key!r}]")
    if isinstance(node, ast.Slice):
        return slice(
            _eval(node.lower, context) if node.lower is not None else None,
            _eval(node.upper, context) if node.upper is not None else None,
            _eval(node.step, context) if node.step is not None else None,
        )
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_eval(item, context) for item in node.elts]
        if isinstance(node, ast.List):
            return values
        if isinstance(node, ast.Tuple):
            return tuple(values)
        return set(values)
    if isinstance(node, ast.Dict):
        dict_result: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                unpacked = _eval(value_node, context)
                if not isinstance(unpacked, Mapping):
                    raise TemplateExpressionError(
                        "Dictionary unpacking requires a mapping"
                    )
                dict_result.update(unpacked)
                continue

            key = _eval(key_node, context)
            dict_result[key] = _eval(value_node, context)
        return dict_result
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval(node.left, context), _eval(node.right, context))
    if isinstance(node, ast.UnaryOp):
        value = _eval(node.operand, context)
        if isinstance(node.op, ast.Not):
            return not value
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.UAdd):
            return +value
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            result: Any = True
            for item in node.values:
                result = _eval(item, context)
                if not result:
                    return result
            return result
        if isinstance(node.op, ast.Or):
            result = False
            for item in node.values:
                result = _eval(item, context)
                if result:
                    return result
            return result
    if isinstance(node, ast.Compare):
        left = _eval(node.left, context)
        for operation, comparator in zip(node.ops, node.comparators):
            if isinstance(operation, (ast.Is, ast.IsNot)) and isinstance(comparator, ast.Name) and comparator.id == "defined":
                is_defined = not getattr(left, "is_undefined", False)
                result = (not is_defined) if isinstance(operation, ast.IsNot) else is_defined
            else:
                right = _eval(comparator, context)
                if type(operation) not in _CMPOPS:
                    raise TemplateExpressionError(f"Unsupported comparison: {type(operation).__name__}")
                result = _CMPOPS[type(operation)](left, right)
            if not result:
                return False
            left = _eval(comparator, context)
        return True
    if isinstance(node, ast.IfExp):
        return _eval(node.body if _eval(node.test, context) else node.orelse, context)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in SAFE_FUNCTIONS:
            raise TemplateExpressionError("Function calls are limited to approved template helpers")
        function = SAFE_FUNCTIONS[node.func.id]
        args = [_eval(item, context) for item in node.args]
        kwargs = {item.arg: _eval(item.value, context) for item in node.keywords if item.arg is not None}
        return function(*args, **kwargs)
    raise TemplateExpressionError(f"Unsupported expression syntax: {type(node).__name__}")
