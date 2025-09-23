"""Unit tests for the /health REST API endpoint."""

from unittest.mock import Mock, patch

import pytest
from llama_stack.providers.datatypes import HealthStatus
from app.endpoints.health import (
    readiness_probe_get_method,
    liveness_probe_get_method,
    get_providers_health_statuses,
    ApplicationState,
    validate_configuration,
    find_unresolved_template_placeholders,
    app_state,
)
from models.responses import ProviderHealthStatus, ReadinessResponse
from tests.unit.utils.auth_helpers import mock_authorization_resolvers


@pytest.fixture
def reset_app_state():
    """Reset the global app_state between tests."""
    # Reset the global app_state
    global app_state
    app_state._initialization_complete = False
    app_state._initialization_errors = []
    app_state._startup_checks = {
        'configuration_loaded': False,
        'configuration_valid': False,
        'llama_client_initialized': False,
        'mcp_servers_registered': False
    }
    yield
    # Reset after test too
    app_state._initialization_complete = False
    app_state._initialization_errors = []
    app_state._startup_checks = {
        'configuration_loaded': False,
        'configuration_valid': False,
        'llama_client_initialized': False,
        'mcp_servers_registered': False
    }


@pytest.mark.asyncio
async def test_readiness_probe_fails_due_to_unhealthy_providers(mocker, reset_app_state):
    """Test the readiness endpoint handler fails when providers are unhealthy."""
    mock_authorization_resolvers(mocker)

    # Mock configuration validation to pass
    mocker.patch("app.endpoints.health.validate_configuration", return_value=(True, "Configuration valid"))
    
    # Mock app_state to be fully initialized
    app_state._initialization_complete = True
    app_state._startup_checks = {k: True for k in app_state._startup_checks}

    # Mock get_providers_health_statuses to return an unhealthy provider
    mock_get_providers_health_statuses = mocker.patch(
        "app.endpoints.health.get_providers_health_statuses"
    )
    mock_get_providers_health_statuses.return_value = [
        ProviderHealthStatus(
            provider_id="test_provider",
            status=HealthStatus.ERROR.value,
            message="Test error",
        )
    ]

    # Mock the Response object
    mock_response = Mock()

    response = await readiness_probe_get_method(response=mock_response)

    assert response.ready is False
    assert "test_provider" in response.reason
    assert "Unhealthy providers" in response.reason
    assert mock_response.status_code == 503


@pytest.mark.asyncio
async def test_readiness_probe_success_when_all_providers_healthy(mocker, reset_app_state):
    """Test the readiness endpoint handler succeeds when all providers are healthy."""
    mock_authorization_resolvers(mocker)

    # Mock configuration validation to pass
    mocker.patch("app.endpoints.health.validate_configuration", return_value=(True, "Configuration valid"))
    
    # Mock app_state to be fully initialized
    app_state._initialization_complete = True
    app_state._startup_checks = {k: True for k in app_state._startup_checks}

    # Mock get_providers_health_statuses to return healthy providers
    mock_get_providers_health_statuses = mocker.patch(
        "app.endpoints.health.get_providers_health_statuses"
    )
    mock_get_providers_health_statuses.return_value = [
        ProviderHealthStatus(
            provider_id="provider1",
            status=HealthStatus.OK.value,
            message="Provider is healthy",
        ),
        ProviderHealthStatus(
            provider_id="provider2",
            status=HealthStatus.NOT_IMPLEMENTED.value,
            message="Provider does not implement health check",
        ),
    ]

    # Mock the Response object
    mock_response = Mock()

    response = await readiness_probe_get_method(response=mock_response)
    assert response is not None
    assert isinstance(response, ReadinessResponse)
    assert response.ready is True
    assert response.reason == "Application fully initialized and ready"
    # Should return empty list since no providers are unhealthy
    assert len(response.providers) == 0


@pytest.mark.asyncio
async def test_readiness_probe_fails_due_to_configuration_issues(mocker, reset_app_state):
    """Test the readiness endpoint fails when configuration has unresolved templates."""
    mock_authorization_resolvers(mocker)

    # Mock configuration validation to fail
    mocker.patch(
        "app.endpoints.health.validate_configuration", 
        return_value=(False, "Unresolved template placeholders found: authentication.jwk_config.jwt_configuration.role_rules=${\\{AUTHN_ROLE_RULES}} (malformed template)")
    )
    
    # Mock app_state to be incomplete
    app_state._initialization_complete = False
    app_state._startup_checks['configuration_loaded'] = False
    app_state._startup_checks['configuration_valid'] = False

    # Mock providers to be healthy (but won't matter due to config failure)
    mocker.patch("app.endpoints.health.get_providers_health_statuses", return_value=[])

    # Mock the Response object
    mock_response = Mock()

    response = await readiness_probe_get_method(response=mock_response)

    assert response.ready is False
    assert "Configuration error:" in response.reason
    assert "AUTHN_ROLE_RULES" in response.reason
    assert mock_response.status_code == 503


@pytest.mark.asyncio
async def test_readiness_probe_fails_due_to_incomplete_initialization(mocker, reset_app_state):
    """Test the readiness endpoint fails when application initialization is incomplete."""
    mock_authorization_resolvers(mocker)

    # Mock configuration validation to pass
    mocker.patch("app.endpoints.health.validate_configuration", return_value=(True, "Configuration valid"))
    
    # Mock app_state to be incomplete
    app_state._initialization_complete = False
    app_state._startup_checks['configuration_loaded'] = True
    app_state._startup_checks['configuration_valid'] = True
    app_state._startup_checks['llama_client_initialized'] = False  # This will cause failure
    app_state._startup_checks['mcp_servers_registered'] = False
    app_state._initialization_errors = ["llama_client_initialized: Failed to connect to llama stack"]

    # Mock providers to be healthy
    mocker.patch("app.endpoints.health.get_providers_health_statuses", return_value=[])

    # Mock the Response object
    mock_response = Mock()

    response = await readiness_probe_get_method(response=mock_response)
    
    assert response.ready is False
    assert "Llama Client Initialized: Failed to connect to llama stack" in response.reason
    assert mock_response.status_code == 503


@pytest.mark.asyncio
async def test_liveness_probe(mocker):
    """Test the liveness endpoint handler."""
    mock_authorization_resolvers(mocker)

    response = await liveness_probe_get_method()
    assert response is not None
    assert response.alive is True


class TestApplicationState:
    """Test cases for the ApplicationState class."""

    def test_application_state_initialization(self):
        """Test ApplicationState initializes with correct defaults."""
        state = ApplicationState()
        assert state._initialization_complete is False
        assert state._initialization_errors == []
        assert len(state._startup_checks) == 4
        assert all(not v for v in state._startup_checks.values())

    def test_mark_check_complete_success(self):
        """Test marking a check as complete successfully."""
        state = ApplicationState()
        state.mark_check_complete('configuration_loaded', True)
        
        assert state._startup_checks['configuration_loaded'] is True
        assert len(state._initialization_errors) == 0

    def test_mark_check_complete_failure(self):
        """Test marking a check as failed with error message."""
        state = ApplicationState()
        state.mark_check_complete('configuration_loaded', False, "Failed to load config")
        
        assert state._startup_checks['configuration_loaded'] is False
        assert "configuration_loaded: Failed to load config" in state._initialization_errors

    def test_mark_initialization_complete(self):
        """Test marking initialization as complete."""
        state = ApplicationState()
        state.mark_initialization_complete()
        
        assert state._initialization_complete is True

    def test_is_fully_initialized_false_when_incomplete(self):
        """Test is_fully_initialized returns False when initialization is incomplete."""
        state = ApplicationState()
        assert state.is_fully_initialized is False
        
        # Even if all checks pass, initialization must be marked complete
        for check in state._startup_checks:
            state._startup_checks[check] = True
        assert state.is_fully_initialized is False

    def test_is_fully_initialized_false_when_checks_fail(self):
        """Test is_fully_initialized returns False when some checks fail."""
        state = ApplicationState()
        state.mark_initialization_complete()
        
        # Some checks still false
        state._startup_checks['configuration_loaded'] = False
        assert state.is_fully_initialized is False

    def test_is_fully_initialized_true_when_complete(self):
        """Test is_fully_initialized returns True when everything is ready."""
        state = ApplicationState()
        state.mark_initialization_complete()
        
        # All checks pass
        for check in state._startup_checks:
            state._startup_checks[check] = True
        assert state.is_fully_initialized is True

    def test_initialization_status(self):
        """Test initialization_status returns correct status dict."""
        state = ApplicationState()
        state.mark_check_complete('configuration_loaded', True)
        state.mark_check_complete('llama_client_initialized', False, "Connection failed")
        
        status = state.initialization_status
        assert status['complete'] is False
        assert status['checks']['configuration_loaded'] is True
        assert status['checks']['llama_client_initialized'] is False
        assert "llama_client_initialized: Connection failed" in status['errors']


class TestFindUnresolvedTemplatePlaceholders:
    """Test cases for the find_unresolved_template_placeholders function."""

    def test_find_simple_template_placeholders(self):
        """Test finding simple template placeholders."""
        config = {
            'service': {
                'api_key': '${env.OPENAI_API_KEY}',
                'host': 'localhost'  # normal string
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 1
        assert result[0][0] == 'service.api_key'
        assert 'env.OPENAI_API_KEY' in result[0][1]
        assert 'unresolved llama-stack env var' in result[0][1]

    def test_find_malformed_template_placeholders(self):
        """Test finding malformed template placeholders."""
        config = {
            'authentication': {
                'role_rules': '${\\{AUTHN_ROLE_RULES}}'  # malformed
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 1
        assert result[0][0] == 'authentication.role_rules'
        assert 'AUTHN_ROLE_RULES' in result[0][1]
        assert 'malformed template' in result[0][1]

    def test_find_openshift_template_placeholders(self):
        """Test finding OpenShift-style template placeholders."""
        config = {
            'service': {
                'name': '${SERVICE_NAME}',
                'port': '${SERVICE_PORT}'
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 2
        # Results should be sorted by path
        paths = [r[0] for r in result]
        assert 'service.name' in paths
        assert 'service.port' in paths

    def test_find_templates_in_nested_structures(self):
        """Test finding templates in nested objects and arrays."""
        config = {
            'nested': {
                'list': [
                    {'item1': 'normal_value'},
                    {'item2': '${TEMPLATE_IN_LIST}'}
                ],
                'dict': {
                    'deep': '${DEEP_TEMPLATE}'
                }
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 2
        paths = [r[0] for r in result]
        assert 'nested.list[1].item2' in paths
        assert 'nested.dict.deep' in paths

    def test_ignore_normal_strings(self):
        """Test that normal strings without templates are ignored."""
        config = {
            'service': {
                'host': 'localhost',
                'description': 'This is a normal string',
                'url': 'http://localhost:8080'
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 0

    def test_report_same_template_in_different_paths(self):
        """Test that the same template variable is reported when it appears in different configuration paths."""
        config = {
            'service': {
                'api_key': '${env.SAME_VAR}',  # Same template value in different paths
                'backup_key': '${env.SAME_VAR}'
            }
        }
        
        result = find_unresolved_template_placeholders(config)
        assert len(result) == 2  # Should report both occurrences since they're in different paths
        assert result[0][0] != result[1][0]  # Different paths
        
        # Both should reference the same template variable but at different paths
        paths = [r[0] for r in result]
        assert 'service.api_key' in paths
        assert 'service.backup_key' in paths


class TestValidateConfiguration:
    """Test cases for the validate_configuration function."""

    @pytest.mark.asyncio
    async def test_validate_configuration_not_loaded(self, mocker):
        """Test validation when configuration is not loaded."""
        # Mock configuration to be None
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = None
        
        result = await validate_configuration()
        assert result[0] is False
        assert "Configuration not loaded - no detailed error available" in result[1]

    @pytest.mark.asyncio
    async def test_validate_configuration_not_loaded_with_detailed_error(self, mocker):
        """Test validation when configuration is not loaded but app_state has detailed errors."""
        # Mock configuration to be None
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = None
        
        # Set up detailed configuration error in app_state
        app_state._initialization_errors = [
            "configuration_loaded: Pydantic validation failed: Input should be a valid list"
        ]
        
        result = await validate_configuration()
        assert result[0] is False
        assert "Pydantic validation failed: Input should be a valid list" in result[1]
        
        # Clean up
        app_state._initialization_errors = []

    @pytest.mark.asyncio
    async def test_validate_configuration_with_unresolved_templates(self, mocker):
        """Test validation when configuration has unresolved templates."""
        # Mock configuration to be loaded
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = {'test': 'config'}
        
        # Mock find_unresolved_template_placeholders to return issues
        mocker.patch(
            "app.endpoints.health.find_unresolved_template_placeholders",
            return_value=[
                ('auth.role_rules', '${\\{AUTHN_ROLE_RULES}} (malformed template)'),
                ('service.api_key', '${env.OPENAI_API_KEY} (unresolved llama-stack env var)')
            ]
        )
        
        result = await validate_configuration()
        assert result[0] is False
        assert "Unresolved template placeholders found" in result[1]
        assert "auth.role_rules" in result[1]
        assert "service.api_key" in result[1]

    @pytest.mark.asyncio
    async def test_validate_configuration_success(self, mocker):
        """Test validation when configuration is valid."""
        # Mock configuration to be loaded
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = {'test': 'config'}
        
        # Mock find_unresolved_template_placeholders to return no issues
        mocker.patch(
            "app.endpoints.health.find_unresolved_template_placeholders",
            return_value=[]
        )
        
        result = await validate_configuration()
        assert result[0] is True
        assert "Configuration valid" in result[1]

    @pytest.mark.asyncio
    async def test_validate_configuration_exception(self, mocker):
        """Test validation when an exception occurs during validation."""
        # Mock configuration to throw an exception when accessing _configuration
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = {"test": "config"}  # Set it to some value so we get past the first check
        
        # Mock find_unresolved_template_placeholders to throw an exception
        mocker.patch(
            "app.endpoints.health.find_unresolved_template_placeholders",
            side_effect=Exception("Something went wrong")
        )
        
        result = await validate_configuration()
        assert result[0] is False
        assert "Configuration validation error" in result[1]

    @pytest.mark.asyncio
    async def test_validate_configuration_limits_issue_reporting(self, mocker):
        """Test that validation limits the number of issues reported."""
        # Mock configuration to be loaded
        mock_config = mocker.patch("app.endpoints.health.configuration")
        mock_config._configuration = {'test': 'config'}
        
        # Mock find_unresolved_template_placeholders to return many issues
        many_issues = [(f'path{i}', f'${{{i}}}') for i in range(10)]
        mocker.patch(
            "app.endpoints.health.find_unresolved_template_placeholders",
            return_value=many_issues
        )
        
        result = await validate_configuration()
        assert result[0] is False
        assert "Unresolved template placeholders found" in result[1]
        assert "and 5 more" in result[1]  # Should limit to first 5 and mention there are more


class TestProviderHealthStatus:
    """Test cases for the ProviderHealthStatus model."""

    def test_provider_health_status_creation(self):
        """Test creating a ProviderHealthStatus instance."""
        status = ProviderHealthStatus(
            provider_id="test_provider", status="ok", message="All good"
        )
        assert status.provider_id == "test_provider"
        assert status.status == "ok"
        assert status.message == "All good"

    def test_provider_health_status_optional_fields(self):
        """Test creating a ProviderHealthStatus with minimal fields."""
        status = ProviderHealthStatus(provider_id="test_provider", status="ok")
        assert status.provider_id == "test_provider"
        assert status.status == "ok"
        assert status.message is None


class TestGetProvidersHealthStatuses:
    """Test cases for the get_providers_health_statuses function."""

    async def test_get_providers_health_statuses(self, mocker):
        """Test get_providers_health_statuses with healthy providers."""
        # Mock the imports
        mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")

        # Mock the client and its methods
        mock_client = mocker.AsyncMock()
        mock_lsc.return_value = mock_client

        # Mock providers.list() to return providers with health
        mock_provider_1 = mocker.Mock()
        mock_provider_1.provider_id = "provider1"
        mock_provider_1.health = {
            "status": HealthStatus.OK.value,
            "message": "All good",
        }

        mock_provider_2 = mocker.Mock()
        mock_provider_2.provider_id = "provider2"
        mock_provider_2.health = {
            "status": HealthStatus.NOT_IMPLEMENTED.value,
            "message": "Provider does not implement health check",
        }

        mock_provider_3 = mocker.Mock()
        mock_provider_3.provider_id = "unhealthy_provider"
        mock_provider_3.health = {
            "status": HealthStatus.ERROR.value,
            "message": "Connection failed",
        }

        mock_client.providers.list.return_value = [
            mock_provider_1,
            mock_provider_2,
            mock_provider_3,
        ]

        # Mock configuration
        result = await get_providers_health_statuses()

        assert len(result) == 3
        assert result[0].provider_id == "provider1"
        assert result[0].status == HealthStatus.OK.value
        assert result[0].message == "All good"
        assert result[1].provider_id == "provider2"
        assert result[1].status == HealthStatus.NOT_IMPLEMENTED.value
        assert result[1].message == "Provider does not implement health check"
        assert result[2].provider_id == "unhealthy_provider"
        assert result[2].status == HealthStatus.ERROR.value
        assert result[2].message == "Connection failed"

    async def test_get_providers_health_statuses_connection_error(self, mocker):
        """Test get_providers_health_statuses when connection fails."""
        # Mock the imports
        mock_lsc = mocker.patch("client.AsyncLlamaStackClientHolder.get_client")

        # Mock get_llama_stack_client to raise an exception
        mock_lsc.side_effect = Exception("Connection error")

        result = await get_providers_health_statuses()

        assert len(result) == 1
        assert result[0].provider_id == "unknown"
        assert result[0].status == HealthStatus.ERROR.value
        assert (
            result[0].message == "Failed to initialize health check: Connection error"
        )
