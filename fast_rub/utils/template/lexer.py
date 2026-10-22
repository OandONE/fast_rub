from __future__ import annotations

from dataclasses import dataclass

from .exceptions import TemplateSyntaxError


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    start: int
    end: int
    line: int
    column: int


_OPENERS = (("{{", "}}", "EXPR"), ("{%", "%}", "BLOCK"), ("{#", "#}", "COMMENT"))


def tokenize(source: str, template_name: str | None = None) -> list[Token]:
    """Split a template into text, expression, block and comment tokens"""
    tokens: list[Token] = []
    cursor = 0
    length = len(source)

    while cursor < length:
        found_at = -1
        opener = None
        for candidate in _OPENERS:
            index = source.find(candidate[0], cursor)
            if index != -1 and (found_at == -1 or index < found_at):
                found_at = index
                opener = candidate

        if found_at == -1:
            tokens.append(_token("TEXT", source[cursor:], cursor, length, source))
            cursor = length
            break

        if found_at > cursor:
            tokens.append(_token("TEXT", source[cursor:found_at], cursor, found_at, source))

        assert opener is not None
        open_text, close_text, kind = opener
        close_at = source.find(close_text, found_at + len(open_text))
        if close_at == -1:
            line, column = _line_column(source, found_at)
            raise TemplateSyntaxError(
                f"Unclosed {open_text!r} tag",
                template_name=template_name,
                line=line,
                column=column,
            )

        content_start = found_at + len(open_text)
        token_end = close_at + len(close_text)
        value = source[content_start:close_at]
        if kind != "COMMENT":
            value = value.strip()
            tokens.append(_token(kind, value, found_at, token_end, source))
        cursor = token_end

    if length == 0:
        return []
    return tokens


def _token(kind: str, value: str, start: int, end: int, source: str) -> Token:
    line, column = _line_column(source, start)
    return Token(kind, value, start, end, line, column)


def _line_column(source: str, offset: int) -> tuple[int, int]:
    line = source.count("\n", 0, offset) + 1
    previous_newline = source.rfind("\n", 0, offset)
    return line, offset - previous_newline
