"""
# Calendar.py
# Calendar schedule manager for tracking administrator busy times and automated availability.
# Author: Gabriella Hernandez
"""

try:
    import utime as time
except ImportError:
    import time

from Log import *


class Calendar:
    """
    **Calendar** tracks an administrator's scheduled meetings and busy intervals.

    It stores schedule intervals in a dictionary keyed by day name and evaluates
    whether the administrator is currently busy based on the system RTC clock.

    Parameters:
    -----------
    busyTime : dict, optional
        Dictionary mapping day names (e.g., 'Monday', 'Mon') to lists of time interval
        tuples in 24-hour format (e.g., `[("09:00", "11:00"), ("14:00", "15:30")]`).
        Defaults to an empty dictionary.

    Examples:
    ---------
    1. Creating a calendar with busy intervals:
       ```python
       cal = Calendar({
           "Monday": [("09:00", "11:00"), ("13:00", "15:00")],
           "Wednesday": [("10:00", "12:00")]
       })
       if cal.isBusy():
           Log.i("Administrator is in a scheduled meeting")
       ```
    """

    WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    WEEKDAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def __init__(self, busyTime=None):
        """
        Initialize the Calendar instance with busy intervals.

        Parameters:
        -----------
        busyTime : dict, optional
            Dictionary containing scheduled busy intervals.
        """
        self._busyTime = busyTime if busyTime is not None else {}
        Log.i(f"Calendar initialized with {len(self._busyTime)} scheduled days")

    def _parseMinutes(self, time_str):
        """Convert 'HH:MM' string to minutes from midnight."""
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])

    def isBusy(self, check_time=None) -> bool:
        """
        Check whether the current time falls within any scheduled busy interval.

        Parameters:
        -----------
        check_time : tuple, optional
            A time tuple `(year, month, day, hour, min, sec, weekday, ...)` matching
            `time.localtime()`. If omitted or None, the current system clock is used.

        Returns:
        --------
        bool : True if the administrator is busy, False otherwise.
        """
        if not self._busyTime:
            return False

        if check_time is None:
            t = time.localtime()
        else:
            t = check_time

        # t[6] is weekday index (0=Monday, ..., 6=Sunday)
        weekday_idx = t[6]
        hour = t[3]
        minute = t[4]
        current_minutes = hour * 60 + minute

        day_full = self.WEEKDAY_NAMES[weekday_idx]
        day_short = self.WEEKDAY_SHORT[weekday_idx]

        # Look up busy slots for the day
        slots = self._busyTime.get(day_full, []) or self._busyTime.get(day_short, [])

        for start_str, end_str in slots:
            start_min = self._parseMinutes(start_str)
            end_min = self._parseMinutes(end_str)
            if start_min <= current_minutes < end_min:
                Log.d(f"Calendar: Current time ({hour:02d}:{minute:02d}) is BUSY within {start_str}-{end_str}")
                return True

        Log.d(f"Calendar: Current time ({hour:02d}:{minute:02d}) is NOT busy")
        return False


if __name__ == "__main__":
    Log.i("Testing Calendar.py...")

    test_schedule = {
        "Monday": [("09:00", "11:00"), ("14:00", "15:30")],
        "Wed": [("10:00", "12:00")]
    }
    cal = Calendar(test_schedule)

    # Monday 09:30 -> Busy
    mon_busy = (2026, 11, 2, 9, 30, 0, 0, 306)
    assert cal.isBusy(mon_busy) is True, "Monday 09:30 should be busy"

    # Monday 11:30 -> Not busy
    mon_free = (2026, 11, 2, 11, 30, 0, 0, 306)
    assert cal.isBusy(mon_free) is False, "Monday 11:30 should be free"

    # Monday 14:15 -> Busy
    mon_busy_afternoon = (2026, 11, 2, 14, 15, 0, 0, 306)
    assert cal.isBusy(mon_busy_afternoon) is True, "Monday 14:15 should be busy"

    # Wednesday 10:30 (using short day name) -> Busy
    wed_busy = (2026, 11, 4, 10, 30, 0, 2, 308)
    assert cal.isBusy(wed_busy) is True, "Wednesday 10:30 should be busy"

    # Friday 10:00 -> Not scheduled -> Not busy
    fri_free = (2026, 11, 6, 10, 0, 0, 4, 310)
    assert cal.isBusy(fri_free) is False, "Friday should be free"

    # Empty calendar -> Always False
    empty_cal = Calendar()
    assert empty_cal.isBusy(mon_busy) is False, "Empty calendar should never be busy"

    Log.i("Testing complete - all checks passed")
