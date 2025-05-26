"""Unit tests for functions defined in src/models/config.py."""

import pytest

from models.config import Configuration, LLamaStackConfiguration, ServiceConfiguration


def test_service_configuration_constructor() -> None:
    """Test the ServiceConfiguration constructor."""
    s = ServiceConfiguration()
    assert s is not None

    assert s.host == "localhost"
    assert s.port == 8080
    assert s.auth_enabled is False
    assert s.workers == 1
    assert s.color_log is True
    assert s.access_log is True


def test_service_configuration_port_value() -> None:
    """Test the ServiceConfiguration port value validation."""
    with pytest.raises(ValueError, match="Port value should not be negative"):
        ServiceConfiguration(port=-1)

    with pytest.raises(ValueError, match="Port value should be less than 65536"):
        ServiceConfiguration(port=100000)


def test_service_configuration_workers_value() -> None:
    """Test the ServiceConfiguration workers value validation."""
    with pytest.raises(ValueError, match="Workers must be set to at least 1"):
        ServiceConfiguration(workers=-1)


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
