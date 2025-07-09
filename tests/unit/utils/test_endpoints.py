"""Unit tests for endpoints utility functions."""

import os
import pytest

import constants
from configuration import AppConfig

from models.requests import QueryRequest
from utils import endpoints


@pytest.fixture
def input_file(tmp_path):
    """Create file manually using the tmp_path fixture."""
    filename = os.path.join(tmp_path, "prompt.txt")
    with open(filename, "wt") as fout:
        fout.write("this is prompt!")
    return filename


def test_get_default_system_prompt():
    """Test that default system prompt is returned when other prompts are not provided."""
    config_dict = {
        "name": "foo",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "feedback_disabled": True,
        },
        "mcp_servers": [],
        "customization": None,
    }

    # no customization provided
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # no system prompt in query request
    query_request = QueryRequest(query="query", system_prompt=None)

    # default system prompt needs to be returned
    system_prompt = endpoints.get_system_prompt(query_request, cfg)
    assert system_prompt == constants.DEFAULT_SYSTEM_PROMPT


def test_get_customized_system_prompt():
    """Test that customized system prompt is used when system prompt is not provided in query."""
    config_dict = {
        "name": "foo",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "feedback_disabled": True,
        },
        "mcp_servers": [],
        "customization": {
            "system_prompt": "This is system prompt",
        },
    }

    # no customization provided
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # no system prompt in query request
    query_request = QueryRequest(query="query", system_prompt=None)

    # default system prompt needs to be returned
    system_prompt = endpoints.get_system_prompt(query_request, cfg)
    assert system_prompt == "This is system prompt"


def test_get_query_system_prompt():
    """Test that system prompt from query is returned."""
    config_dict = {
        "name": "foo",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "feedback_disabled": True,
        },
        "mcp_servers": [],
        "customization": None,
    }

    # no customization provided
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # system prompt defined in query request
    system_prompt = "System prompt defined in query"
    query_request = QueryRequest(query="query", system_prompt=system_prompt)

    # default system prompt needs to be returned
    system_prompt = endpoints.get_system_prompt(query_request, cfg)
    assert system_prompt == system_prompt


def test_get_query_system_prompt_not_customized_one():
    """Test that system prompt from query is returned even when customized one is specified."""
    config_dict = {
        "name": "foo",
        "service": {
            "host": "localhost",
            "port": 8080,
            "auth_enabled": False,
            "workers": 1,
            "color_log": True,
            "access_log": True,
        },
        "llama_stack": {
            "api_key": "xyzzy",
            "url": "http://x.y.com:1234",
            "use_as_library_client": False,
        },
        "user_data_collection": {
            "feedback_disabled": True,
        },
        "mcp_servers": [],
        "customization": {
            "system_prompt": "This is system prompt",
        },
    }

    # no customization provided
    cfg = AppConfig()
    cfg.init_from_dict(config_dict)

    # system prompt defined in query request
    system_prompt = "System prompt defined in query"
    query_request = QueryRequest(query="query", system_prompt=system_prompt)

    # default system prompt needs to be returned
    system_prompt = endpoints.get_system_prompt(query_request, cfg)
    assert system_prompt == system_prompt
