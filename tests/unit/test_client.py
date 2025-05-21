"""Unit tests for functions defined in src/client.py."""

import os
from unittest.mock import patch

from client import get_llama_stack_client
from models.config import LLamaStackConfiguration


@patch.dict(os.environ, {"INFERENCE_MODEL": "llama3.2:3b-instruct-fp16"})
def test_get_llama_stack_library_client():
    cfg = LLamaStackConfiguration(
        url=None,
        api_key=None,
        use_as_library_client=True,
        library_client_config_path="ollama",
    )
    client = get_llama_stack_client(cfg)
    assert client is not None


@patch.dict(os.environ, {"INFERENCE_MODEL": "llama3.2:3b-instruct-fp16"})
def test_get_llama_stack_remote_client():
    cfg = LLamaStackConfiguration(
        url="http://localhost:8321",
        api_key=None,
        use_as_library_client=False,
        library_client_config_path="ollama",
    )
    client = get_llama_stack_client(cfg)
    assert client is not None
