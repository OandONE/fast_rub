"""Fast Rub's integrated template engine

Syntax supported: ``{{ expression }}``, filters, ``if/elif/else``, ``for/else``,
``set``, comments, and file ``include`` directives. The return shape is kept
compatible with the previous utility: ``TemplateEngine.render`` returns
``(clean_text, metadata)``
"""

from .engine import TemplateEngine
from .exceptions import (
    TemplateError,
    TemplateExpressionError,
    TemplateNotFound,
    TemplateSyntaxError,
)
from .loader import FileOpen, TemplateLoader

__all__ = [
    "TemplateEngine",
    "FileOpen",
    "TemplateLoader",
    "TemplateError",
    "TemplateSyntaxError",
    "TemplateExpressionError",
    "TemplateNotFound",
]
