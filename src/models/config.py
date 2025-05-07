from typing import Optional

from pydantic import BaseModel


class LLamaStackConfiguration(BaseModel):
    """Llama stack configuration."""

    url: str


class Configuration(BaseModel):
    """Global service configuration."""

    name: str
    llama_stack: LLamaStackConfiguration
