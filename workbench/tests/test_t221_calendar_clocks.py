"""Fixed calendar oracles keep the shared T-136/T-137 clock sensitive to DST all year."""
from datetime import datetime, timedelta
import os
import unittest
from unittest.mock import patch

import local_calendar


class CalendarClocks(unittest.TestCase):
    def test_named_local_clock_keeps_wall_time_across_calendar_days(self):
        # UTC inputs are instants; expected offsets/dates are hand-derived New York calendar facts.
        cases = [
            ('spring-two-days', '2026-03-07T03:34:00+00:00', 2, 10, '2026-03-08T10:00:00-04:00'),
            ('fall-two-days', '2026-11-01T02:34:00+00:00', 2, 10, '2026-11-02T10:00:00-05:00'),
            ('spring-week', '2026-03-02T14:00:00+00:00', 7, 9, '2026-03-09T09:00:00-04:00'),
            ('fall-week', '2026-10-26T13:00:00+00:00', 7, 9, '2026-11-02T09:00:00-05:00'),
            ('month-end', '2026-05-01T03:34:00+00:00', 2, 10, '2026-05-02T10:00:00-04:00'),
            ('year-end', '2026-12-31T03:34:00+00:00', 2, 10, '2027-01-01T10:00:00-05:00'),
        ]
        environment = dict(os.environ, TZ='America/New_York')
        for name, instant, days, hour, expected in cases:
            with self.subTest(name=name):
                anchor = datetime.fromisoformat(instant)

                class Clock(datetime):
                    @classmethod
                    def now(cls, tz=None):
                        return cls.fromtimestamp(anchor.timestamp(), tz)

                # Only time is injected. Zone discovery and the shared E2E clock remain real.
                with patch.object(local_calendar, 'datetime', Clock):
                    local = local_calendar.local_now(environment)
                actual = (local + timedelta(days=days)).replace(hour=hour, minute=0, second=0, microsecond=0)
                self.assertEqual(actual.isoformat(), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
