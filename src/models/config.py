from pydantic import BaseModel


class Configuration(BaseModel):
    """Global service configuration."""

    name: str
