from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .filters import Filter
    from .inline_filters import InlineFilter
    from ..types import Update, UpdateButton

async def _run_filter(
    filters: "Filter | InlineFilter | None",
    update: "Update | UpdateButton"
):
    if filters is not None:
        try:
            filter_class = type(filters)
            if "__acall__" in filter_class.__dict__.keys():
                return await filters.__acall__(update)  # type: ignore
            else:
                return filters(update)  # type: ignore
        except Exception as e:
            return False
    return True
