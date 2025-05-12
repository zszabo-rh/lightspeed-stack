from pydantic import BaseModel

from typing import Optional


class LLamaStackConfiguration(BaseModel):
    """Llama stack configuration."""

    url: str
    api_key: Optional[str] = None


class Configuration(BaseModel):
    """Global service configuration."""

    name: str
    llama_stack: LLamaStackConfiguration
