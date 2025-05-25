"""Integration tests for configuration loading and handling."""

import pytest
from src.configuration import configuration


@pytest.fixture
def configuration_filename() -> str:
    return "tests/configuration/lightspeed-stack.yaml"


def test_default_configuration() -> None:
    cfg = configuration
    assert cfg is not None
    with pytest.raises(Exception, match="logic error: configuration is not loaded"):
        configuration.configuration


def test_loading_proper_configuration(configuration_filename: str) -> None:
    cfg = configuration
    cfg.load_configuration(configuration_filename)
    assert cfg is not None
    assert cfg.configuration is not None
    assert cfg.llama_stack_configuration is not None
    name = cfg.configuration.name
    assert name == "foo bar baz"
    ls_config = cfg.llama_stack_configuration
    assert ls_config.url == "http://localhost:8321"
