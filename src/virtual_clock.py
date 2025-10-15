import datetime


class VirtualClock:
    def __init__(self, start_time=None):
        self.current_time = start_time or datetime.datetime.now()

    def now(self):
        """Return the current virtual time as datetime object."""
        return self.current_time

    def advance_ms(self, delay_ms):
        """Advance virtual time by given milliseconds and return new time."""
        delta = datetime.timedelta(milliseconds=delay_ms)
        self.current_time += delta
        return self.current_time

    def advance_days(self, days):
        """Advance virtual time by N days (negative to subtract)."""
        delta = datetime.timedelta(days=days)
        self.current_time += delta
        return self.current_time

    def start_test_at(self, hour, minute=0, second=0):
        """
        Set the time-of-day to a specific hour (e.g., 8:00).
        Keeps the same date.
        """
        self.current_time = self.current_time.replace(
            hour=hour, minute=minute, second=second, microsecond=0
        )
        return self.current_time

    def formatted_time(self):
        """Return virtual time as string with milliseconds."""
        ts = self.current_time
        return (
            f"{ts.strftime('%Y-%m-%d %H:%M:%S')}.{str(ts.microsecond // 1000).zfill(3)}"
        )
