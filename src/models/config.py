from pydantic import BaseModel, model_validator

from typing import Optional
from typing_extensions import Self


class LLamaStackConfiguration(BaseModel):
    """Llama stack configuration."""

    url: Optional[str] = None
    api_key: Optional[str] = None
    use_as_library_client: Optional[bool] = None
    chat_completion_mode: bool = False

    @model_validator(mode="after")
    def check_llama_stack_model(self) -> Self:
        if self.url is None:
            if self.use_as_library_client is None:
                raise ValueError(
                    "LLama stack URL is not specified and library client mode is not specified"
                )
            if self.use_as_library_client is False:
                raise ValueError(
                    "LLama stack URL is not specified and library client mode is not enabled"
                )
        if self.use_as_library_client is None:
            self.use_as_library_client = False
        return self


class Configuration(BaseModel):
    """Global service configuration."""

    name: str
    llama_stack: LLamaStackConfiguration
