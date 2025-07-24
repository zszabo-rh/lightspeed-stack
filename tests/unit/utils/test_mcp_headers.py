"""Unit tests for MCP headers utility functions."""

from fastapi import Request
from unittest.mock import Mock
import pytest

from utils import mcp_headers


def test_extract_mcp_headers_empty_headers():
    """Test the extract_mcp_headers function for request without any headers."""
    request = Mock(spec=Request)
    # no headers
    request.headers = {}

    result = mcp_headers.extract_mcp_headers(request)
    assert result == {}


def test_extract_mcp_headers_mcp_headers_empty():
    """Test the extract_mcp_headers function for request with empty MCP-HEADERS header."""
    request = Mock(spec=Request)
    # empty MCP-HEADERS
    request.headers = {"MCP-HEADERS": ""}

    # empty dict should be returned
    result = mcp_headers.extract_mcp_headers(request)
    assert result == {}


def test_extract_mcp_headers_valid_mcp_header():
    """Test the extract_mcp_headers function for request with valid MCP-HEADERS header."""
    request = Mock(spec=Request)
    # valid MCP-HEADERS
    request.headers = {"MCP-HEADERS": '{"http://www.redhat.com": {"auth": "token123"}}'}

    result = mcp_headers.extract_mcp_headers(request)

    expected = {"http://www.redhat.com": {"auth": "token123"}}
    assert result == expected


def test_extract_mcp_headers_valid_mcp_headers():
    """Test the extract_mcp_headers function for request with valid MCP-HEADERS headers."""
    request = Mock(spec=Request)
    # valid MCP-HEADERS
    header1 = '"http://www.redhat.com": {"auth": "token123"}'
    header2 = '"http://www.example.com": {"auth": "tokenXYZ"}'

    request.headers = {"MCP-HEADERS": f"{{{header1}, {header2}}}"}

    result = mcp_headers.extract_mcp_headers(request)

    expected = {
        "http://www.redhat.com": {"auth": "token123"},
        "http://www.example.com": {"auth": "tokenXYZ"},
    }
    assert result == expected


def test_extract_mcp_headers_invalid_json_mcp_header():
    """Test the extract_mcp_headers function for request with invalid MCP-HEADERS header."""
    request = Mock(spec=Request)
    # invalid MCP-HEADERS - not a JSON
    request.headers = {"MCP-HEADERS": "this-is-invalid"}

    # empty dict should be returned
    result = mcp_headers.extract_mcp_headers(request)
    assert result == {}


def test_extract_mcp_headers_invalid_mcp_header_type():
    """Test the extract_mcp_headers function for request with invalid MCP-HEADERS header type."""
    request = Mock(spec=Request)
    # invalid MCP-HEADERS - not a dict
    request.headers = {"MCP-HEADERS": "[]"}

    # empty dict should be returned
    result = mcp_headers.extract_mcp_headers(request)
    assert result == {}


def test_extract_mcp_headers_invalid_mcp_header_null_value():
    """Test the extract_mcp_headers function for request with invalid MCP-HEADERS header type."""
    request = Mock(spec=Request)
    # invalid MCP-HEADERS - not a dict
    request.headers = {"MCP-HEADERS": "null"}

    # empty dict should be returned
    result = mcp_headers.extract_mcp_headers(request)
    assert result == {}
