"""Unit tests for the app/main.py startup event."""

import pytest
from unittest.mock import AsyncMock


class TestStartupEvent:
    """Test cases for the startup event in app/main.py."""

    def setup_default_mocks(self, mocker):
        """Set up default mocks for startup event tests."""
        # Mock app_state
        mock_app_state = mocker.MagicMock()
        mocker.patch('app.endpoints.health.app_state', mock_app_state)
        
        # Mock configuration
        mock_configuration = mocker.MagicMock()
        mock_configuration.configuration = {"test": "config"}
        mocker.patch('app.main.configuration', mock_configuration)
        
        # Mock MCP registration (default: success)
        mock_register_mcp = mocker.AsyncMock()
        mocker.patch('app.main.register_mcp_servers_async', mock_register_mcp)
        
        # Mock logger
        mock_get_logger = mocker.MagicMock()
        mocker.patch('app.main.get_logger', mock_get_logger)
        
        # Mock database operations (default: success)
        mock_initialize_database = mocker.MagicMock()
        mocker.patch('app.main.initialize_database', mock_initialize_database)
        
        mock_create_tables = mocker.MagicMock()
        mocker.patch('app.main.create_tables', mock_create_tables)
        
        return {
            'app_state': mock_app_state,
            'configuration': mock_configuration,
            'register_mcp': mock_register_mcp,
            'get_logger': mock_get_logger,
            'initialize_database': mock_initialize_database,
            'create_tables': mock_create_tables,
        }

    @pytest.mark.asyncio
    async def test_startup_event_success(self, mocker):
        """Test the startup event completes successfully and tracks initialization state."""
        # Setup default mocks (all successful)
        mocks = self.setup_default_mocks(mocker)
        
        # Import and run the startup event
        from app.main import startup_event
        await startup_event()
        
        # Verify MCP servers were registered and tracked
        mocks['register_mcp'].assert_called_once()
        mocks['app_state'].mark_check_complete.assert_any_call('mcp_servers_registered', True)
        
        # Verify database initialization
        mocks['initialize_database'].assert_called_once()
        mocks['create_tables'].assert_called_once()
        
        # Verify initialization completion was marked
        mocks['app_state'].mark_initialization_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_event_mcp_registration_failure(self, mocker):
        """Test the startup event handles MCP registration failure properly."""
        # Setup default mocks
        mocks = self.setup_default_mocks(mocker)
        
        # Override: Mock MCP registration to fail
        mocks['register_mcp'].side_effect = Exception("MCP registration failed")
        
        # Import and run the startup event
        from app.main import startup_event
        await startup_event()
        
        # Verify MCP registration failure was tracked
        mocks['register_mcp'].assert_called_once()
        mocks['app_state'].mark_check_complete.assert_any_call(
            'mcp_servers_registered',
            False,
            'Configuration not available: MCP registration failed'
        )

        # Verify database initialization WAS called (graceful failure continues startup)
        mocks['initialize_database'].assert_called_once()
        # Verify initialization completion was called
        mocks['app_state'].mark_initialization_complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_event_database_failure(self, mocker):
        """Test the startup event handles database initialization failure properly."""
        # Setup default mocks
        mocks = self.setup_default_mocks(mocker)
        
        # Override: Mock database initialization to fail
        mocks['initialize_database'].side_effect = Exception("Database init failed")
        
        # Import and run the startup event
        from app.main import startup_event
        await startup_event()
        
        # Verify MCP registration was successful
        mocks['register_mcp'].assert_called_once()
        mocks['app_state'].mark_check_complete.assert_any_call('mcp_servers_registered', True)
        
        # Verify database failure was tracked
        mocks['initialize_database'].assert_called_once()
        mocks['app_state'].mark_check_complete.assert_any_call(
            'mcp_servers_registered', 
            False, 
            'Startup event failed: Database init failed'
        )
        
        # Verify create_tables was NOT called (due to earlier exception)
        mocks['create_tables'].assert_not_called()
        
        # Verify initialization completion was NOT marked (due to exception)
        mocks['app_state'].mark_initialization_complete.assert_not_called() 