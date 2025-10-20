"""Quota limiter factory class."""

import logging

from models.config import QuotaHandlersConfiguration

from constants import USER_QUOTA_LIMITER, CLUSTER_QUOTA_LIMITER
from quota.quota_limiter import QuotaLimiter

logger = logging.getLogger(__name__)


class QuotaLimiterFactory:
    """Quota limiter factory class."""

    @staticmethod
    def quota_limiters(config: QuotaHandlersConfiguration) -> list[QuotaLimiter]:
        """Create instances of quota limiters based on loaded configuration.

        Returns:
            List of instances of 'QuotaLimiter',
        """
        limiters: list[QuotaLimiter] = []
        return limiters
