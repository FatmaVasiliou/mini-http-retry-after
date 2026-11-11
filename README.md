# mini-http-retry-after

Parse an HTTP `Retry-After` header into a delay in seconds, supporting both the
seconds form and the HTTP-date form.

## Usage

```python
from mini_http_retry_after import parse_retry_after

# Seconds form
assert parse_retry_after("120") == 120.0

# HTTP-date form; pass a reference timestamp so the result is deterministic.
# This header is 60 seconds after the reference.
now = 784111717.0
assert parse_retry_after("Sun, 06 Nov 1994 08:49:37 GMT", now=now) == 60.0

# Invalid values return None rather than raising.
assert parse_retry_after("soon") is None
```

## Why this exists

Applications that talk to rate-limited APIs need to turn a `Retry-After` header
into a number of seconds before sleeping. The header has two forms — a
non-negative integer number of seconds, or an HTTP-date — and the date form is
often emitted in the past, which would otherwise produce a negative sleep.
This library normalises both forms into a non-negative float and returns `None`
for anything it cannot parse, so callers can decide on a fallback delay instead
of catching exceptions.

The trade-off: only the IMF-fixdate form of HTTP-date is accepted. RFC 7231
permits obsolete date formats for parsing, but servers that use the date form
of `Retry-After` practically always use IMF-fixdate. Supporting the obsolete
formats would add a large, rarely exercised parser for no real benefit. If you
receive an obsolete date, `parse_retry_after` returns `None` and you should
apply your own fallback.

## The awkward edge

The date form is relative to "now", so the result depends on the clock. Rather
than hide that, `parse_retry_after` and `parse_retry_after_date` accept a
keyword-only `now` argument (a Unix timestamp). Tests pass a fixed value;
production code can omit it and use the wall clock. A date in the past is
clamped to `0.0`, never negative.
