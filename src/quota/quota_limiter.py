"""Abstract class that is parent for all quota limiter implementations."""

import logging
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class QuotaLimiter(ABC):
    """Abstract class that is parent for all quota limiter implementations."""

    @abstractmethod
    def available_quota(self, subject_id: str) -> int:
        """Retrieve available quota for given user."""

    @abstractmethod
    def revoke_quota(self) -> None:
        """Revoke quota for given user."""

    @abstractmethod
    def increase_quota(self) -> None:
        """Increase quota for given user."""

    @abstractmethod
    def ensure_available_quota(self, subject_id: str = "") -> None:
        """Ensure that there's available quota left."""

    @abstractmethod
    def consume_tokens(
        self, input_tokens: int, output_tokens: int, subject_id: str = ""
    ) -> None:
        """Consume tokens by given user."""

    @abstractmethod
    def __init__(self) -> None:
        """Initialize connection config."""

    @abstractmethod
    def _initialize_tables(self) -> None:
        """Initialize tables and indexes."""

    # pylint: disable=W0201
    def connect(self) -> None:
        """Initialize connection to database."""

    def connected(self) -> bool:
        """Check if connection to cache is alive."""
        return True
