from dataclasses import dataclass


@dataclass(frozen=True)
class AutoFailoverConfig:
    """Auto Failover timing options. / تنظیمات زمانی Auto Failover."""

    check_interval: float | None = None
    failure_timeout: float | None = None
    recovery_successes: int | None = None

    def __post_init__(self):
        """Validate timing options. / اعتبارسنجی گزینه‌های زمانی."""
        # Reject invalid values early instead of failing inside the monitor task.
        if self.check_interval is not None and self.check_interval <= 0:
            raise ValueError("check_interval باید بزرگ‌تر از صفر باشد")
        if self.failure_timeout is not None and self.failure_timeout <= 0:
            raise ValueError("failure_timeout باید بزرگ‌تر از صفر باشد")
        if self.recovery_successes is not None and self.recovery_successes < 1:
            raise ValueError("recovery_successes باید حداقل ۱ باشد")
