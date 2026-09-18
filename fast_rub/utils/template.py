import logging
import re
import random
import string
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Client


class FileOpen:
    def __init__(
        self,
        path: str,
        mode: str = "r"
    ):
        self.path = path
        self.mode = mode
    
    def read(self) -> str:
        with open(self.path, self.mode, encoding="utf-8") as f:
            return f.read()


class TemplateEngine:
    PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")

    def __init__(
        self,
        client: "Client | None" = None
    ):
        # client اختیاری است — یوزربات (پایروبی) بدون Client فست‌روب هم از آن استفاده می‌کند
        self.client = client

    def render(
        self,
        template: str,
        parse_mode: str | None = "Markdown",
        auto_escape: bool = True,
        **kwargs: Any
    ) -> tuple[str, list[dict[str, Any]]]:
        # FileOpen
        for key, value in kwargs.items():
            if isinstance(value, FileOpen):
                kwargs[key] = value.read()

        # placeholder
        placeholder_matches = list(self.PLACEHOLDER_PATTERN.finditer(template))

        if not placeholder_matches:
            metadata, clean_text = self._parse(template, parse_mode)
            return clean_text, metadata

        config = getattr(self.client, "config", None) if self.client is not None else None
        config_auto_escape = bool(getattr(config, "auto_escape", True)) if config is not None else True
        logger = getattr(self.client, "logger", None) if self.client is not None else None

        # auto_escape=False
        if not auto_escape or not config_auto_escape:
            (logger or logging.getLogger("fast_rub")).warning(
                "⚠️ auto_escape=False — ورودی کاربر بدون escape رندر میشه."
            )
            result = template
            for match in placeholder_matches:
                placeholder = match.group(0)
                key = match.group(1)
                value = str(kwargs.get(key, placeholder))
                result = result.replace(placeholder, value, 1)

            metadata, clean_text = self._parse(result, parse_mode)
            return clean_text, metadata

        # auto_escape=True
        replacements: list[tuple[str, str]] = []
        used_markers: set[str] = set()
        safe_template_parts: list[str] = []
        last = 0

        for match in placeholder_matches:
            safe_template_parts.append(template[last:match.start()])

            placeholder = match.group(0)
            key = match.group(1)
            value = str(kwargs.get(key, ""))

            marker_len = len(placeholder)
            marker = self._random_string(marker_len)
            while marker in used_markers or marker in template:
                marker = self._random_string(marker_len)

            used_markers.add(marker)
            replacements.append((marker, value))
            safe_template_parts.append(marker)
            last = match.end()

        safe_template_parts.append(template[last:])
        safe_template = "".join(safe_template_parts)

        # Parse before inserting user values so Markdown/HTML syntax inside values
        # cannot accidentally become formatting.
        metadata, clean_text = self._parse(safe_template, parse_mode)

        # Replace markers one-by-one and update metadata in UTF-16 code units,
        # which is the coordinate system used by TextParser.
        final_text = clean_text
        for marker, value in replacements:
            pos = final_text.find(marker)
            if pos == -1:
                continue

            start_utf16 = self._utf16_length(final_text[:pos])
            old_len_utf16 = self._utf16_length(marker)
            new_len_utf16 = self._utf16_length(value)
            diff_utf16 = new_len_utf16 - old_len_utf16
            end_utf16 = start_utf16 + old_len_utf16

            final_text = final_text[:pos] + value + final_text[pos + len(marker):]

            if diff_utf16 == 0:
                continue

            for meta in metadata:
                meta_start = meta["from_index"]
                meta_end = meta_start + meta["length"]

                # Metadata fully after the replaced marker shifts by diff.
                if meta_start >= end_utf16:
                    meta["from_index"] += diff_utf16

                # Metadata contains the marker. The formatting range keeps covering
                # the inserted value, so only its length changes.
                elif meta_start <= start_utf16 and meta_end >= end_utf16:
                    meta["length"] += diff_utf16

        return final_text, metadata

    def _parse(self, text: str, parse_mode: str | None) -> tuple[list[dict[str, Any]], str]:
        from .text_parser import TextParser
        if parse_mode == "HTML":
            return TextParser.html(text)
        return TextParser.markdown(text)
    
    @staticmethod
    def _utf16_length(text: str) -> int:
        """Return text length in UTF-16 code units (Rubika metadata indexing)."""
        return len(text.encode("utf-16-le")) // 2

    def _random_string(self, length: int) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
