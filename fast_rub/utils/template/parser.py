from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, NoReturn

from .exceptions import TemplateSyntaxError
from .lexer import Token, tokenize


@dataclass
class TextNode:
    text: str


@dataclass
class ExpressionNode:
    expression: str
    token: Token


@dataclass
class IfNode:
    branches: list[tuple[str, list[Any]]] = field(default_factory=list)
    else_body: list[Any] = field(default_factory=list)
    token: Token | None = None


@dataclass
class ForNode:
    target: str
    expression: str
    body: list[Any] = field(default_factory=list)
    else_body: list[Any] = field(default_factory=list)
    token: Token | None = None


@dataclass
class SetNode:
    name: str
    expression: str
    token: Token | None = None


@dataclass
class IncludeNode:
    expression: str
    ignore_missing: bool = False
    token: Token | None = None


class TemplateParser:
    """Parser for Fast Rub's small, Jinja-inspired template language"""

    _set_pattern = re.compile(r"^set\s+([A-Za-z_]\w*)\s*=\s*(.+)$", re.DOTALL)
    _for_pattern = re.compile(r"^for\s+([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)?)\s+in\s+(.+)$", re.DOTALL)

    def __init__(self, source: str, template_name: str | None = None) -> None:
        self.source = source
        self.template_name = template_name
        self.tokens = tokenize(source, template_name)
        self.index = 0

    def parse(self) -> list[Any]:
        nodes, stop = self._parse_until(set())
        if stop is not None:
            self._error(f"Unexpected '{stop.value}' block", stop)
        return nodes

    def _parse_until(self, stop_names: set[str]) -> tuple[list[Any], Token | None]:
        nodes: list[Any] = []
        while self.index < len(self.tokens):
            token = self.tokens[self.index]
            self.index += 1

            if token.kind == "TEXT":
                nodes.append(TextNode(token.value))
                continue
            if token.kind == "EXPR":
                if not token.value:
                    self._error("Empty expression", token)
                nodes.append(ExpressionNode(token.value, token))
                continue
            if token.kind != "BLOCK":
                continue

            command = token.value.split(None, 1)[0] if token.value else ""
            if command in stop_names:
                self.index -= 1
                return nodes, token
            if command == "if":
                nodes.append(self._parse_if(token))
            elif command == "for":
                nodes.append(self._parse_for(token))
            elif command == "set":
                match = self._set_pattern.fullmatch(token.value)
                if not match:
                    self._error("Expected '{% set name = expression %}'", token)
                nodes.append(SetNode(match.group(1), match.group(2).strip(), token))
            elif command == "include":
                expression = token.value[len("include"):].strip()
                ignore_missing = expression.endswith(" ignore missing")
                if ignore_missing:
                    expression = expression[:-len(" ignore missing")].strip()
                if not expression:
                    self._error("Expected a template name after 'include'", token)
                nodes.append(IncludeNode(expression, ignore_missing, token))
            else:
                self._error(f"Unknown block command: {command!r}", token)
        return nodes, None

    def _parse_if(self, start_token: Token) -> IfNode:
        expression = start_token.value[len("if"):].strip()
        if not expression:
            self._error("Expected an expression after 'if'", start_token)
        node = IfNode(token=start_token)
        body, stop = self._parse_until({"elif", "else", "endif"})
        node.branches.append((expression, body))

        while stop is not None:
            command = stop.value.split(None, 1)[0]
            self.index += 1
            if command == "elif":
                expression = stop.value[len("elif"):].strip()
                if not expression:
                    self._error("Expected an expression after 'elif'", stop)
                body, stop = self._parse_until({"elif", "else", "endif"})
                node.branches.append((expression, body))
                continue
            if command == "else":
                node.else_body, stop = self._parse_until({"endif"})
                if stop is None:
                    self._error("Unclosed 'if' block", start_token)
                self.index += 1
                return node
            # endif
            return node

        self._error("Unclosed 'if' block", start_token)
        return node

    def _parse_for(self, start_token: Token) -> ForNode:
        match = self._for_pattern.fullmatch(start_token.value)
        if not match:
            self._error("Expected '{% for item in items %}'", start_token)
        target, expression = match.groups()
        target_names = [name.strip() for name in target.split(",")]
        if len(target_names) > 2:
            self._error("A loop can assign to at most two variables", start_token)
        node = ForNode(",".join(target_names), expression.strip(), token=start_token)
        node.body, stop = self._parse_until({"else", "endfor"})
        if stop is None:
            self._error("Unclosed 'for' block", start_token)
        command = stop.value.split(None, 1)[0]
        self.index += 1
        if command == "else":
            node.else_body, stop = self._parse_until({"endfor"})
            if stop is None:
                self._error("Unclosed 'for' block", start_token)
            self.index += 1
        return node

    def _error(self, message: str, token: Token) -> NoReturn:
        raise TemplateSyntaxError(
            message,
            template_name=self.template_name,
            line=token.line,
            column=token.column,
        )
