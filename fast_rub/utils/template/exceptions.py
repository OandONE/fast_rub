from __future__ import annotations


class TemplateError(Exception):
    """Base exception for Fast Rub template errors"""


class TemplateSyntaxError(TemplateError):
    """Raised when a template contains invalid or unbalanced syntax"""

    def __init__(
        self,
        message: str,
        *,
        template_name: str | None = None,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.template_name = template_name
        self.line = line
        self.column = column
        location = ""
        if template_name:
            location += f" in {template_name}"
        if line is not None:
            location += f" at line {line}"
            if column is not None:
                location += f", column {column}"
        super().__init__(f"{message}{location}")


class TemplateNotFound(TemplateError, FileNotFoundError):
    """Raised when a named template cannot be loaded"""


class TemplateExpressionError(TemplateError):
    """Raised when a template expression cannot be evaluated safely"""


class TemplateUndefinedError(TemplateExpressionError):
    """Raised when strict mode encounters an undefined template value"""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Undefined template variable: {name!r}")
