"""Unit tests for QuotaSchedulerConfig model."""

from models.config import QuotaSchedulerConfiguration


def test_quota_scheduler_default_configuration() -> None:
    """Test the default configuration."""
    cfg = QuotaSchedulerConfiguration()
    assert cfg is not None
    # default value
    assert cfg.period == 1


def test_quota_scheduler_custom_configuration() -> None:
    """Test the custom configuration."""
    cfg = QuotaSchedulerConfiguration(period=10)
    assert cfg is not None
    assert cfg.period == 10
