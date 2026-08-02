import importlib

# List of modules that pyrubi needs
_PYRUBI_DEPS = ["Crypto", "websockets", "mutagen", "filetype"]

_missing = []
for _dep in _PYRUBI_DEPS:
    try:
        importlib.import_module(_dep)
    except ImportError:
        _missing.append(_dep)

if _missing:
    import warnings
    warnings.warn(
        f"pyrubi dependencies are not installed: {', '.join(_missing)}. "
        f"Install them with: pip install fastrub[pyrubi]. "
        f"Userbot features will not work until these are installed.",
        ImportWarning,
        stacklevel=2,
    )


from .client import Client

__version__ = "3.6.0-fork"
__author__ = "seyyed mohamad hosein moosavi raja"
__original_author__ = "Ali Ganji"
