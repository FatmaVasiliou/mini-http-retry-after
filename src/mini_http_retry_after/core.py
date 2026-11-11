"""Core parsing logic for HTTP Retry-After headers.

The Retry-After header (RFC 7231 section 7.1.3) can be either:

* a non-negative integer number of seconds, or
* an HTTP-date (IMF-fixdate, e.g. ``Sun, 06 Nov 1994 08:49:37 GMT``).

We deliberately support only the IMF-fixdate form of HTTP-date. RFC 7231
allows obsolete date formats for parsing, but servers that emit Retry-After
with a date practically always use IMF-fixdate, and supporting the obsolete
formats would require a much larger parser for little benefit. This is the
single interpretation we commit to.
"""

from __future__ import annotations

import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone

__all__ = [
    "parse_retry_after",
    "parse_retry_after_date",
    "parse_retry_after_seconds",
]


def parse_retry_after_seconds(value: str) -> float | None:
    """Parse a Retry-After value as a number of seconds.

    Returns the delay in seconds as a float, or ``None`` if *value* is not a
    valid non-negative integer (the only numeric form allowed by the spec).
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    # RFC 7231 requires a non-negative integer. We reject floats, signs and
    # whitespace-separated forms so callers get a clear failure instead of a
    # silently coerced value.
    if not text.isdigit():
        return None
    try:
        return float(int(text, 10))
    except ValueError:  # pragma: no cover - isdigit already guards this
        return None


def parse_retry_after_date(value: str, *, now: float | None = None) -> float | None:
    """Parse a Retry-After value as an HTTP-date and return seconds from *now*.

    The result is clamped at zero: a date in the past yields ``0.0`` rather
    than a negative delay, because a negative delay has no useful meaning to
    a caller that is about to sleep.

    *now* is a Unix timestamp (seconds since the epoch). When omitted, the
    current wall clock is used. Tests pass an explicit value so they never
    depend on the machine clock.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    # parsedate_to_datetime returns naive datetimes for IMF-fixdate without
    # a timezone. Treat those as UTC, matching HTTP semantics.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    target = parsed.timestamp()
    reference = time.time() if now is None else float(now)
    delay = target - reference
    if delay < 0.0:
        return 0.0
    return delay


def parse_retry_after(value: str, *, now: float | None = None) -> float | None:
    """Parse a Retry-After header value into a delay in seconds.

    Accepts either the seconds form or the HTTP-date form. Returns ``None``
    when the value is empty, malformed, or otherwise not a Retry-After value.

    The seconds form is tried first because it is the common case and it is
    unambiguous: a string of digits can never be a valid HTTP-date.

    *now* is forwarded to :func:`parse_retry_after_date` and is only used for
    the date form. It defaults to the current wall clock.
    """
    seconds = parse_retry_after_seconds(value)
    if seconds is not None:
        return seconds
    return parse_retry_after_date(value, now=now)
