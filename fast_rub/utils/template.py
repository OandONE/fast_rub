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
        client: "Client"
    ):
        self.client = client
    
    def render(
        self,
        template: str,
        parse_mode: str = "Markdown",
        auto_escape: bool = True,
        **kwargs: Any
    ) -> tuple[str, list[dict[str, Any]]]:
        # FileOpen
        for key, value in kwargs.items():
            if isinstance(value, FileOpen):
                kwargs[key] = value.read()
        
        # placeholder
        placeholders = self.PLACEHOLDER_PATTERN.findall(template)
        
        if not placeholders:
            metadata, clean_text = self._parse(template, parse_mode)
            return clean_text, metadata
        
        # auto_escape=False
        if not auto_escape:
            self.client.logger.warning(
                "⚠️ auto_escape=False — ورودی کاربر بدون escape رندر میشه."
            )
            result = template
            for key in placeholders:
                value = str(kwargs.get(key, f"{{{{ {key} }}}}"))
                result = result.replace(f"{{{{ {key} }}}}", value)
            metadata, clean_text = self._parse(result, parse_mode)
            return clean_text, metadata
        
        # auto_escape=True
        random_map: dict[str, str] = {}
        value_map: dict[str, str] = {}
        safe_template = template
        
        for key in placeholders:
            placeholder = f"{{{{ {key} }}}}"
            random_str = self._random_string(len(placeholder))
            random_map[random_str] = placeholder
            value_map[random_str] = str(kwargs.get(key, ""))
            safe_template = safe_template.replace(placeholder, random_str)
        
        # Pars
        metadata, clean_text = self._parse(safe_template, parse_mode)
        
        # Replace
        final_text: str = clean_text
        for random_str, placeholder in random_map.items():
            value = value_map[random_str]
            old_len = len(random_str)
            new_len = len(value)
            diff = new_len - old_len
            
            pos = final_text.find(random_str)
            if pos != -1:
                final_text = final_text.replace(random_str, value)
                
                if diff != 0:
                    for meta in metadata:
                        if meta["from_index"] >= pos + old_len:
                            meta["from_index"] += diff
                        elif meta["from_index"] >= pos and meta["from_index"] + meta["length"] <= pos + old_len:
                            meta["length"] += diff
        
        return final_text, metadata
    
    def _parse(self, text: str, parse_mode: str) -> tuple[list[dict[str, Any]], str]:
        from .text_parser import TextParser
        if parse_mode == "HTML":
            return TextParser.html(text)
        return TextParser.markdown(text)
    
    def _random_string(self, length: int) -> str:
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=length))
