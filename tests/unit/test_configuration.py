"""Unit tests for functions defined in src/configuration.py."""

from src.configuration import configuration


def test_default_configuration():
    cfg = configuration
    assert cfg is not None
