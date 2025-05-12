import yaml

from typing import Any, Optional
from models.config import Configuration, LLamaStackConfiguration


class AppConfig:
    _instance = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "AppConfig":
        """Create a new instance of the class."""
        if not isinstance(cls._instance, cls):
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the class instance."""
        self._configuration: Optional[Configuration] = None

    def load_configuration(self, filename: str) -> None:
        """Load configuration from YAML file."""
        with open(filename, encoding="utf-8") as fin:
            config_dict = yaml.safe_load(fin)
            print(config_dict)
            self._configuration = Configuration(**config_dict)

    @property
    def configuration(self) -> Configuration:
        assert (
            self._configuration is not None
        ), "logic error: configuration is not loaded"
        return self._configuration

    @property
    def llama_stack_configuration(self) -> LLamaStackConfiguration:
        assert (
            self._configuration is not None
        ), "logic error: configuration is not loaded"
        return self._configuration.llama_stack


configuration: AppConfig = AppConfig()
xyz: str = "XYZ"
