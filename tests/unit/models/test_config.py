"""Unit tests for functions defined in src/models/config.py."""

import pytest

from models.config import Configuration, LLamaStackConfiguration


def test_llama_stack_configuration_constructor() -> None:
    """Test the LLamaStackConfiguration constructor."""
    l = LLamaStackConfiguration(
        use_as_library_client=True, library_client_config_path="foo"
    )
    assert l is not None

    l = LLamaStackConfiguration(use_as_library_client=False, url="http://localhost")
    assert l is not None

    l = LLamaStackConfiguration(url="http://localhost")
    assert l is not None

    l = LLamaStackConfiguration(
        use_as_library_client=False, url="http://localhost", api_key="foo"
    )
    assert l is not None


def test_llama_stack_wrong_configuration_constructor_no_url() -> None:
    """Test the LLamaStackConfiguration constructor."""
    with pytest.raises(
        ValueError,
        match="LLama stack URL is not specified and library client mode is not specified",
    ):
        LLamaStackConfiguration()


def test_llama_stack_wrong_configuration_constructor_library_mode_off() -> None:
    """Test the LLamaStackConfiguration constructor."""
    with pytest.raises(
        ValueError,
        match="LLama stack URL is not specified and library client mode is not enabled",
    ):
        LLamaStackConfiguration(use_as_library_client=False)


def test_llama_stack_wrong_configuration_no_config_file() -> None:
    """Test the LLamaStackConfiguration constructor."""
    with pytest.raises(
        ValueError,
        match="LLama stack library client mode is enabled but a configuration file path is not specified",
    ):
        LLamaStackConfiguration(use_as_library_client=True)
