from __future__ import annotations

from typing import Any

import fmf
from fmf.utils import FilterError

DEFAULT_FILTER = "result: fail, error, failed"


class FilterExpressionError(Exception):
    """Raised when an fmf filter expression is invalid or cannot be evaluated."""


def matches_filter(filter: str, data: dict[str, Any]) -> bool:  # noqa: A002
    """
    Return True if ``data`` matches the fmf filter expression.

    Matching is case-insensitive and values are treated
    as regular expressions (full match).
    """
    try:
        return bool(fmf.filter(filter, data, sensitive=False, regexp=True, name=None))
    except FilterError as exc:
        raise FilterExpressionError(f"Invalid filter expression {filter!r}.") from exc
