"""Abstract base class for authentication methods."""

from abc import ABC, abstractmethod

from fastapi import Request

UserID = str
UserName = str
Token = str

AuthTuple = tuple[UserID, UserName, Token]


class AuthInterface(ABC):  # pylint: disable=too-few-public-methods
    """Base class for all authentication method implementations."""

    @abstractmethod
    async def __call__(self, request: Request) -> AuthTuple:
        """Validate FastAPI Requests for authentication and authorization."""
