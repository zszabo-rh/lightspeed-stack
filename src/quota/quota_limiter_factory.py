"""Quota limiter factory class."""

import logging

from models.config import QuotaHandlersConfiguration

from quota.quota_limiter import QuotaLimiter

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods


class QuotaLimiterFactory:
    """Quota limiter factory class."""

    @staticmethod
    def quota_limiters(config: QuotaHandlersConfiguration) -> list[QuotaLimiter]:
        """Create instances of quota limiters based on loaded configuration.

        Returns:
            List of instances of 'QuotaLimiter',
        """
        limiters: list[QuotaLimiter] = []

        limiters_config = config.limiters
        if limiters_config is None:
            logger.warning("Quota limiters are not specified in configuration")
            return limiters

        return limiters
