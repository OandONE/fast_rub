from __future__ import annotations

import logging
import secrets
import string
from bisect import bisect_left
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, TYPE_CHECKING

from .context import Context
from .exceptions import TemplateError, TemplateExpressionError, TemplateNotFound
from .expressions import evaluate
from .filters import DEFAULT_FILTERS
from .loader import FileOpen, TemplateLoader
from .parser import (
    ExpressionNode,
    ForNode,
    IfNode,
    IncludeNode,
    SetNode,
    TemplateParser,
    TextNode,
)

if TYPE_CHECKING:
    from ...core import Client


class _AutoParseMode:
    """Sentinel type for automatic parse-mode inference"""
    __slots__ = ()


_AUTO_PARSE_MODE = _AutoParseMode()


class TemplateEngine:
    """Jinja-inspired template support integrated with Fast Rub's message metadata"""

    def __init__(
        self,
        client: "Client | None" = None,
        template_dir: str | Path | None = None,
        *,
        max_loop_iterations: int = 10_000,
        max_include_depth: int = 20,
    ) -> None:
        self.client = client
        config_dir = getattr(getattr(client, "config", None), "template_dir", None)
        self.loader = TemplateLoader(template_dir or config_dir)
        self.filters: dict[str, Any] = dict(DEFAULT_FILTERS)
        if max_loop_iterations < 1:
            raise ValueError("max_loop_iterations must be positive")
        if max_include_depth < 1:
            raise ValueError("max_include_depth must be positive")
        self.max_loop_iterations = max_loop_iterations
        self.max_include_depth = max_include_depth

    def register_filter(self, name: str, function: Any, *, replace: bool = True) -> None:
        """Register a callable filter for templates; existing filters may be protected"""
        if not name or not name.isidentifier():
            raise ValueError("Filter names must be valid Python identifiers")
        if not callable(function):
            raise TypeError("Filter must be callable")
        if not replace and name in self.filters:
            raise ValueError(f"Filter {name!r} is already registered")
        self.filters[name] = function

    def render(
        self,
        template: str | Path | FileOpen,
        parse_mode: str | None | _AutoParseMode = _AUTO_PARSE_MODE,
        auto_escape: bool = True,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Render template syntax and convert Markdown/HTML into Rubika metadata.

        The public return contract intentionally remains ``(clean_text, metadata)``.
        """
        source, template_name = self.loader.load(template)
        if isinstance(parse_mode, _AutoParseMode):
            parse_mode = self._infer_parse_mode(template)
        context_values = {
            key: value.read() if isinstance(value, FileOpen) else value
            for key, value in kwargs.items()
        }
        context = Context(context_values)

        effective_parse_mode: str | None = parse_mode
        main_parse_mode = self.client.main_parse_mode if self.client is not None else "Null"
        if main_parse_mode != "Null":
            effective_parse_mode = main_parse_mode

        chunks: list[str] = []
        replacements: list[tuple[str, str]] = []
        self._render_nodes(
            TemplateParser(source, template_name).parse(),
            context,
            chunks,
            replacements,
            source,
            template_name,
            include_stack=(),
        )
        rendered_source = "".join(chunks)

        config = getattr(self.client, "config", None) if self.client is not None else None
        config_auto_escape = bool(getattr(config, "auto_escape", True)) if config is not None else True
        protect_values = bool(auto_escape and config_auto_escape)

        if replacements and not protect_values:
            logger = getattr(self.client, "logger", None) if self.client is not None else None
            (logger or logging.getLogger("fast_rub")).warning(
                "⚠️ auto_escape=False - ورودی‌های قالب بدون محافظت در برابر Markdown/HTML رندر می‌شوند"
            )
            for marker, value in replacements:
                rendered_source = rendered_source.replace(marker, value, 1)
            replacements = []

        metadata, clean_text = self._parse(rendered_source, effective_parse_mode)
        if protect_values:
            clean_text, metadata = self._replace_markers(clean_text, metadata, replacements)

        clean_text, metadata = self._normalize_output(clean_text, metadata, config)
        return clean_text, metadata

    def render_file(
        self,
        path: str | Path,
        parse_mode: str | None | _AutoParseMode = _AUTO_PARSE_MODE,
        auto_escape: bool = True,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Render a file; by default infer HTML, Markdown, or plain text from suffix"""
        return self.render(Path(path), parse_mode=parse_mode, auto_escape=auto_escape, **kwargs)

    @staticmethod
    def _infer_parse_mode(template: str | Path | FileOpen) -> str | None:
        """Infer the markup parser only for file templates; strings keep Markdown default"""
        if isinstance(template, FileOpen):
            suffix = Path(template.path).suffix.lower()
        elif isinstance(template, Path):
            suffix = template.suffix.lower()
        else:
            return "Markdown"
        if suffix in (".html", ".htm"):
            return "HTML"
        if suffix in (".txt", ".text"):
            return None
        return "Markdown"

    def _render_nodes(
        self,
        nodes: list[Any],
        context: Context,
        chunks: list[str],
        replacements: list[tuple[str, str]],
        source: str,
        template_name: str | None,
        include_stack: tuple[str, ...],
    ) -> None:
        for node in nodes:
            if isinstance(node, TextNode):
                chunks.append(node.text)
            elif isinstance(node, ExpressionNode):
                value = evaluate(node.expression, context, self.filters)
                rendered_value = "" if value is None else str(value)
                marker = self._new_marker(source, chunks, replacements)
                chunks.append(marker)
                replacements.append((marker, rendered_value))
            elif isinstance(node, SetNode):
                context.set(node.name, evaluate(node.expression, context, self.filters))
            elif isinstance(node, IfNode):
                selected = False
                for expression, branch in node.branches:
                    if evaluate(expression, context, self.filters):
                        self._render_nodes(branch, context, chunks, replacements, source, template_name, include_stack)
                        selected = True
                        break
                if not selected:
                    self._render_nodes(node.else_body, context, chunks, replacements, source, template_name, include_stack)
            elif isinstance(node, ForNode):
                iterable = evaluate(node.expression, context, self.filters)
                if iterable is None or getattr(iterable, "is_undefined", False):
                    values: list[Any] = []
                else:
                    try:
                        known_length = len(iterable)
                    except (TypeError, AttributeError):
                        known_length = None
                    if known_length is not None and known_length > self.max_loop_iterations:
                        raise TemplateExpressionError(
                            f"Loop exceeds max_loop_iterations={self.max_loop_iterations}"
                        )
                    try:
                        iterator = iter(iterable)
                        values = []
                        for _ in range(self.max_loop_iterations + 1):
                            try:
                                values.append(next(iterator))
                            except StopIteration:
                                break
                        if len(values) > self.max_loop_iterations:
                            raise TemplateExpressionError(
                                f"Loop exceeds max_loop_iterations={self.max_loop_iterations}"
                            )
                    except TypeError as error:
                        raise TemplateExpressionError(f"Expression in for-loop is not iterable: {node.expression!r}") from error

                if not values:
                    self._render_nodes(node.else_body, context, chunks, replacements, source, template_name, include_stack)
                    continue

                target_names = [part.strip() for part in node.target.split(",")]
                total = len(values)
                for index, item in enumerate(values):
                    loop_values: dict[str, Any] = {
                        "loop": {
                            "index": index + 1,
                            "index0": index,
                            "first": index == 0,
                            "last": index == total - 1,
                            "length": total,
                        }
                    }
                    if len(target_names) == 1:
                        loop_values[target_names[0]] = item
                    else:
                        try:
                            first, second = item
                        except (TypeError, ValueError) as error:
                            raise TemplateExpressionError(
                                f"Loop target {node.target!r} needs two values"
                            ) from error
                        loop_values[target_names[0]] = first
                        loop_values[target_names[1]] = second
                    self._render_nodes(
                        node.body,
                        context.child(loop_values),
                        chunks,
                        replacements,
                        source,
                        template_name,
                        include_stack,
                    )
            elif isinstance(node, IncludeNode):
                target = evaluate(node.expression, context, self.filters)
                if target is None or getattr(target, "is_undefined", False):
                    if node.ignore_missing:
                        continue
                    raise TemplateNotFound(f"Included template name is undefined: {node.expression}")
                try:
                    included_source, included_name = self.loader.load_file(
                        str(target),
                        relative_to=template_name if template_name else None,
                    )
                except TemplateNotFound:
                    if node.ignore_missing:
                        continue
                    raise
                if included_name in include_stack or included_name == template_name:
                    raise TemplateError(f"Recursive template include detected: {included_name}")
                if len(include_stack) >= self.max_include_depth:
                    raise TemplateError(f"Template include depth exceeds {self.max_include_depth}")
                self._render_nodes(
                    TemplateParser(included_source, included_name).parse(),
                    context,
                    chunks,
                    replacements,
                    included_source,
                    included_name,
                    include_stack + ((template_name,) if template_name else ()),
                )

    @staticmethod
    def _new_marker(source: str, chunks: list[str], replacements: list[tuple[str, str]]) -> str:
        existing = source + "".join(chunks)
        existing += "".join(marker for marker, _ in replacements)
        while True:
            marker = "FRX" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24)) + "XRF"
            if marker not in existing:
                return marker

    def _replace_markers(
        self,
        text: str,
        metadata: list[dict[str, Any]],
        replacements: list[tuple[str, str]],
    ) -> tuple[str, list[dict[str, Any]]]:
        result = text
        for marker, value in replacements:
            position = result.find(marker)
            if position < 0:
                # A marker can only disappear if the template parser strips the whole region.
                continue
            start = self._utf16_length(result[:position])
            old_length = self._utf16_length(marker)
            new_length = self._utf16_length(value)
            end = start + old_length
            diff = new_length - old_length
            result = result[:position] + value + result[position + len(marker):]
            if not diff:
                continue
            for item in metadata:
                item_start = int(item.get("from_index", 0))
                item_end = item_start + int(item.get("length", 0))
                if item_start >= end:
                    item["from_index"] = item_start + diff
                elif item_start <= start and item_end >= end:
                    item["length"] = int(item.get("length", 0)) + diff
        metadata = [item for item in metadata if int(item.get("length", 0)) > 0]
        return result, metadata

    def _parse(self, text: str, parse_mode: str | None) -> tuple[list[dict[str, Any]], str]:
        if parse_mode is None or parse_mode == "Null":
            return [], text
        # Reuse Fast Rub's existing parser and its UTF-16 metadata logic.
        from ..text_parser import TextParser

        if parse_mode == "HTML":
            return TextParser.html(text)
        return TextParser.markdown(text)

    def _normalize_output(
        self,
        text: str,
        metadata: list[dict[str, Any]],
        config: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Apply Client text settings while keeping metadata offsets aligned"""
        if config is None or not text:
            return text, metadata

        original = text
        chars = list(text)
        # Each rendered character points back to the span it originated from.
        origins: list[tuple[int, int]] = [(index, index + 1) for index in range(len(chars))]

        if getattr(config, "strip_text", False):
            # Use the framework's existing text utility rather than duplicating its policy.
            from ..utils import Utils

            current = "".join(chars)
            trimmed = Utils.trim_text(current)
            if trimmed != current:
                origins = self._remap_origins(current, origins, trimmed)
                chars = list(trimmed)

        if getattr(config, "optimize_text", False):
            new_chars: list[str] = []
            new_origins: list[tuple[int, int]] = []
            index = 0
            while index < len(chars):
                if not chars[index].isspace():
                    new_chars.append(chars[index])
                    new_origins.append(origins[index])
                    index += 1
                    continue
                run_start = index
                while index < len(chars) and chars[index].isspace():
                    index += 1
                if not new_chars or index == len(chars):
                    continue
                start_origin = min(item[0] for item in origins[run_start:index])
                end_origin = max(item[1] for item in origins[run_start:index])
                new_chars.append(" ")
                new_origins.append((start_origin, end_origin))
            chars, origins = new_chars, new_origins

        limit = getattr(config, "max_text_length", None)
        if limit and len(chars) > limit:
            if getattr(config, "compress_long_text", False):
                cut = max(0, int(limit) - 3)
                kept_origin = origins[cut - 1][1] if cut > 0 and cut <= len(origins) else 0
                chars = chars[:cut] + list("...")
                origins = origins[:cut] + [(kept_origin, kept_origin)] * 3
            else:
                chars = chars[:int(limit)]
                origins = origins[:int(limit)]

        normalized = "".join(chars)
        if normalized == original:
            return normalized, metadata

        old_prefix = self._utf16_prefix(original)
        new_prefix = self._utf16_prefix(normalized)
        adjusted: list[dict[str, Any]] = []
        for item in metadata:
            old_start = int(item.get("from_index", 0))
            old_end = old_start + int(item.get("length", 0))
            old_start_char = bisect_left(old_prefix, old_start)
            old_end_char = bisect_left(old_prefix, old_end)
            touched = [
                index for index, (origin_start, origin_end) in enumerate(origins)
                if origin_start < old_end_char and origin_end > old_start_char
            ]
            if not touched:
                continue
            start_char = touched[0]
            end_char = touched[-1] + 1
            updated = dict(item)
            updated["from_index"] = new_prefix[start_char]
            updated["length"] = new_prefix[end_char] - new_prefix[start_char]
            if updated["length"] > 0:
                adjusted.append(updated)
        return normalized, adjusted

    @staticmethod
    def _remap_origins(
        old_text: str,
        old_origins: list[tuple[int, int]],
        new_text: str,
    ) -> list[tuple[int, int]]:
        """Map transformed characters back to source spans for metadata remapping"""
        if old_text == new_text:
            return old_origins[:]
        matcher = SequenceMatcher(a=old_text, b=new_text, autojunk=False)
        mapped: list[tuple[int, int] | None] = [None] * len(new_text)
        for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            if tag == "equal":
                for old_index, new_index in zip(range(old_start, old_end), range(new_start, new_end)):
                    mapped[new_index] = old_origins[old_index]
            elif tag == "replace":
                if old_start < old_end:
                    source_start = min(origin[0] for origin in old_origins[old_start:old_end])
                    source_end = max(origin[1] for origin in old_origins[old_start:old_end])
                else:
                    source_start = source_end = (old_origins[old_start - 1][1] if old_start else 0)
                for new_index in range(new_start, new_end):
                    mapped[new_index] = (source_start, source_end)
            elif tag == "insert":
                point = old_origins[old_start - 1][1] if old_start > 0 else 0
                for new_index in range(new_start, new_end):
                    mapped[new_index] = (point, point)
            # Delete operations intentionally produce no destination characters.
        return [origin if origin is not None else (0, 0) for origin in mapped]

    @staticmethod
    def _utf16_length(text: str) -> int:
        return len(text.encode("utf-16-le")) // 2

    @staticmethod
    def _utf16_prefix(text: str) -> list[int]:
        prefix = [0]
        total = 0
        for char in text:
            total += 2 if ord(char) > 0xFFFF else 1
            prefix.append(total)
        return prefix
