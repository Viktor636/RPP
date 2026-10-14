from datetime import datetime


class SystemClock:
    """Часы реального времени — живут в слое адаптеров."""

    def now(self) -> datetime:
        return datetime.now()