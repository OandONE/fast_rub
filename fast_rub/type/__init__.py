# This module is deprecated. Use 'types' instead.
import warnings

warnings.warn(
    "Importing from 'fast_rub.type' is deprecated. Use 'fast_rub.types' instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new 'types' module
from fast_rub.types import *  # noqa: F403, E402