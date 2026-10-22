from __future__ import annotations

from pathlib import Path
from typing import Any

from .exceptions import TemplateNotFound


class FileOpen:
    """Compatibility wrapper for reading UTF-8 files in existing Fast Rub code"""

    def __init__(self, path: str | Path, mode: str = "r") -> None:
        self.path = str(path)
        self.mode = mode

    def read(self) -> str:
        if "b" in self.mode:
            raise ValueError("FileOpen is a text-template helper; binary mode is not supported")
        with open(self.path, self.mode, encoding="utf-8") as file:
            return file.read()


class TemplateLoader:
    """Loads template files and prevents include paths escaping template_dir"""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        self.template_dir = Path(template_dir).expanduser().resolve() if template_dir else None

    def load_file(self, path: str | Path, relative_to: str | Path | None = None) -> tuple[str, str]:
        candidate = Path(path).expanduser()
        if not candidate.is_absolute():
            if relative_to is not None:
                candidate = Path(relative_to).parent / candidate
            elif self.template_dir is not None:
                candidate = self.template_dir / candidate
            else:
                candidate = Path.cwd() / candidate
        candidate = candidate.resolve()

        if self.template_dir is not None:
            try:
                candidate.relative_to(self.template_dir)
            except ValueError as error:
                raise TemplateNotFound(f"Template path is outside template_dir: {path}") from error

        try:
            return candidate.read_text(encoding="utf-8"), str(candidate)
        except FileNotFoundError as error:
            raise TemplateNotFound(f"Template not found: {candidate}") from error
        except IsADirectoryError as error:
            raise TemplateNotFound(f"Template path is a directory: {candidate}") from error

    def load(self, source: Any, relative_to: str | Path | None = None) -> tuple[str, str | None]:
        if isinstance(source, FileOpen):
            return source.read(), str(Path(source.path).expanduser().resolve())
        if isinstance(source, Path):
            return self.load_file(source, relative_to=relative_to)
        if isinstance(source, str):
            # A string passed to render() is template source, never guessed to be a path.
            return source, None
        raise TypeError("template must be str, pathlib.Path, or FileOpen")
