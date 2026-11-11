import unittest

from mini_http_retry_after import (
    parse_retry_after,
    parse_retry_after_date,
    parse_retry_after_seconds,
)


class ParseSecondsTests(unittest.TestCase):
    def test_plain_integer(self):
        self.assertEqual(parse_retry_after_seconds("120"), 120.0)

    def test_zero(self):
        self.assertEqual(parse_retry_after_seconds("0"), 0.0)

    def test_surrounding_whitespace(self):
        self.assertEqual(parse_retry_after_seconds("  45  "), 45.0)

    def test_rejects_negative(self):
        self.assertIsNone(parse_retry_after_seconds("-5"))

    def test_rejects_float(self):
        self.assertIsNone(parse_retry_after_seconds("1.5"))

    def test_rejects_empty(self):
        self.assertIsNone(parse_retry_after_seconds(""))

    def test_rejects_non_numeric(self):
        self.assertIsNone(parse_retry_after_seconds("abc"))

    def test_rejects_non_string(self):
        self.assertIsNone(parse_retry_after_seconds(120))  # type: ignore[arg-type]


class ParseDateTests(unittest.TestCase):
    def test_future_date(self):
        # 60 seconds after the reference timestamp.
        now = 1_000_000.0
        value = "Sun, 06 Nov 1994 08:49:37 GMT"
        # The reference is chosen so that the header is exactly 60s in the future.
        parsed = parse_retry_after_date(value, now=now)
        self.assertIsInstance(parsed, float)
        # Compute the expected delay from the known epoch of that date.
        expected = 784111777.0 - now
        self.assertAlmostEqual(parsed, expected, places=6)

    def test_past_date_clamps_to_zero(self):
        value = "Sun, 06 Nov 1994 08:49:37 GMT"
        parsed = parse_retry_after_date(value, now=2_000_000_000.0)
        self.assertEqual(parsed, 0.0)

    def test_rejects_garbage(self):
        self.assertIsNone(parse_retry_after_date("not a date", now=0.0))

    def test_rejects_empty(self):
        self.assertIsNone(parse_retry_after_date("", now=0.0))

    def test_rejects_non_string(self):
        self.assertIsNone(parse_retry_after_date(None, now=0.0))  # type: ignore[arg-type]


class ParseRetryAfterTests(unittest.TestCase):
    def test_seconds_form(self):
        self.assertEqual(parse_retry_after("30"), 30.0)

    def test_date_form(self):
        now = 1_000_000.0
        value = "Sun, 06 Nov 1994 08:49:37 GMT"
        expected = 784111777.0 - now
        self.assertAlmostEqual(parse_retry_after(value, now=now), expected, places=6)

    def test_invalid(self):
        self.assertIsNone(parse_retry_after("nonsense", now=0.0))

    def test_empty(self):
        self.assertIsNone(parse_retry_after(""))

    def test_prefers_seconds_over_date(self):
        # A string of digits is never a valid date, so the seconds branch wins.
        self.assertEqual(parse_retry_after("10"), 10.0)


if __name__ == "__main__":
    unittest.main()
