"""Unit tests for functions defined in src/configuration.py."""

import pytest
from configuration import AppConfig


def test_default_configuration() -> None:
    cfg = AppConfig()
    assert cfg is not None

    # configuration is not loaded
    with pytest.raises(Exception, match="logic error: configuration is not loaded"):
        # try to read property
        cfg.configuration

    with pytest.raises(Exception, match="logic error: configuration is not loaded"):
        # try to read property
        cfg.llama_stack_configuration


def test_configuration_is_singleton() -> None:
    cfg1 = AppConfig()
    cfg2 = AppConfig()
    assert cfg1 == cfg2


def test_init_from_dict() -> None:
    config_dict = {
        "name": "foo",
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
    }
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)
    assert cfg.configuration is not None
    assert cfg.llama_stack_configuration is not None


def test_load_proper_configuration(tmpdir) -> None:
    cfg_filename = tmpdir / "config.yaml"
    with open(cfg_filename, "w") as fout:
        fout.write(
            """
name: foo bar baz
llama_stack:
  use_as_library_client: false
  url: http://localhost:8321
  api_key: xyzzy
        """
        )

    cfg = AppConfig()
    cfg.load_configuration(cfg_filename)
    assert cfg.configuration is not None
    assert cfg.llama_stack_configuration is not None
