"""Unit tests for the src/lightspeed_stack.py entry point module."""

from unittest import mock

import pytest


def test_create_argument_parser():
    """Test for create_argument_parser function."""
    from lightspeed_stack import create_argument_parser
    arg_parser = create_argument_parser()
    # nothing more to test w/o actual parsing is done
    assert arg_parser is not None


def test_main_import():
    """Test main can be imported."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("main", f"src/lightspeed_stack.py")
    main = importlib.util.module_from_spec(spec)
    sys.modules["main"] = main
    spec.loader.exec_module(main)

    assert main is not None


@mock.patch('lightspeed_stack.configuration')
@mock.patch('lightspeed_stack.AsyncLlamaStackClientHolder')
@mock.patch('lightspeed_stack.check_llama_stack_version')
@mock.patch('lightspeed_stack.start_uvicorn')
def test_main_success_flow_with_state_tracking(
    mock_start_uvicorn, 
    mock_check_version, 
    mock_llama_holder, 
    mock_configuration,
    mocker
):
    """Test the main function success flow with initialization state tracking."""
    # Mock the app_state (it's imported from app.endpoints.health within the function)
    mock_app_state = mocker.MagicMock()
    mocker.patch('app.endpoints.health.app_state', mock_app_state)
    
    # Mock arguments
    mock_args = mocker.MagicMock()
    mock_args.dump_configuration = False
    mock_args.config_file = "test-config.yaml"
    
    # Mock argument parser
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mocker.patch('lightspeed_stack.create_argument_parser', return_value=mock_parser)
    
    # Mock configuration loading
    mock_configuration.load_configuration = mocker.MagicMock()
    mock_config_obj = mocker.MagicMock()
    mock_config_obj.llama_stack = {"url": "http://test"}
    mock_configuration.configuration = mock_config_obj
    mock_configuration.llama_stack_configuration = {"url": "http://test"}
    mock_configuration.service_configuration = {"host": "localhost", "port": 8080}
    
    # Mock llama stack client
    mock_client = mocker.AsyncMock()
    mock_llama_holder.return_value.load = mocker.AsyncMock()
    mock_llama_holder.return_value.get_client.return_value = mock_client
    mock_check_version.return_value = mocker.AsyncMock()
    
    # Import and call main
    from lightspeed_stack import main
    main()
    
    # Verify configuration loading was tracked
    mock_app_state.mark_check_complete.assert_any_call('configuration_loaded', True)
    mock_app_state.mark_check_complete.assert_any_call('configuration_valid', True)
    mock_app_state.mark_check_complete.assert_any_call('llama_client_initialized', True)
    
    # Verify configuration was loaded
    mock_configuration.load_configuration.assert_called_once_with("test-config.yaml")
    
    # Verify llama stack client was initialized
    mock_llama_holder.return_value.load.assert_called_once()
    mock_llama_holder.return_value.get_client.assert_called_once()
    
    # Verify uvicorn was started
    mock_start_uvicorn.assert_called_once()


@mock.patch('lightspeed_stack.configuration')
@mock.patch('lightspeed_stack.start_uvicorn')
def test_main_configuration_failure_with_state_tracking(
    mock_start_uvicorn,
    mock_configuration,
    mocker
):
    """Test the main function when configuration loading fails."""
    # Mock the app_state (it's imported from app.endpoints.health within the function)
    mock_app_state = mocker.MagicMock()
    mocker.patch('app.endpoints.health.app_state', mock_app_state)

    # Mock ServiceConfiguration for minimal config
    mock_service_config = mocker.MagicMock()
    mock_service_config_class = mocker.patch('lightspeed_stack.ServiceConfiguration', return_value=mock_service_config)

    # Mock arguments
    mock_args = mocker.MagicMock()
    mock_args.dump_configuration = False
    mock_args.config_file = "test-config.yaml"

    # Mock argument parser
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mocker.patch('lightspeed_stack.create_argument_parser', return_value=mock_parser)

    # Mock configuration loading to fail
    mock_configuration.load_configuration.side_effect = Exception("Config failed")

    # Import and call main - it should start server with minimal config and return normally
    from lightspeed_stack import main
    main()  # Should not raise SystemExit, should start minimal server and return

    # Verify the minimal server was started with correct port
    mock_service_config_class.assert_called_once_with(host="0.0.0.0", port=8090)
    mock_start_uvicorn.assert_called_once_with(mock_service_config)
    
    # Verify state tracking
    mock_app_state.mark_check_complete.assert_any_call(
        'configuration_loaded', False, 'Configuration loading failed: Config failed'
    )
    mock_app_state.mark_check_complete.assert_any_call(
        'configuration_valid', False, 'Configuration loading failed: Config failed'
    )


@mock.patch('lightspeed_stack.configuration')
@mock.patch('lightspeed_stack.AsyncLlamaStackClientHolder')
@mock.patch('lightspeed_stack.check_llama_stack_version')
@mock.patch('lightspeed_stack.start_uvicorn')
def test_main_llama_client_failure_continues_startup(
    mock_start_uvicorn, 
    mock_check_version, 
    mock_llama_holder, 
    mock_configuration,
    mocker
):
    """Test the main function when llama client fails but startup continues."""
    # Mock the app_state (it's imported from app.endpoints.health within the function)
    mock_app_state = mocker.MagicMock()
    mocker.patch('app.endpoints.health.app_state', mock_app_state)
    
    # Mock arguments
    mock_args = mocker.MagicMock()
    mock_args.dump_configuration = False
    mock_args.config_file = "test-config.yaml"
    
    # Mock argument parser
    mock_parser = mocker.MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mocker.patch('lightspeed_stack.create_argument_parser', return_value=mock_parser)
    
    # Mock configuration loading success
    mock_configuration.load_configuration = mocker.MagicMock()
    mock_config_obj = mocker.MagicMock()
    mock_config_obj.llama_stack = {"url": "http://test"}
    mock_configuration.configuration = mock_config_obj
    mock_configuration.llama_stack_configuration = {"url": "http://test"}
    mock_configuration.service_configuration = {"host": "localhost", "port": 8080}
    
    # Mock llama stack client to fail
    mock_llama_holder.return_value.load.side_effect = Exception("Llama client failed")
    
    # Import and call main
    from lightspeed_stack import main
    main()
    
    # Verify configuration success was tracked
    mock_app_state.mark_check_complete.assert_any_call('configuration_loaded', True)
    mock_app_state.mark_check_complete.assert_any_call('configuration_valid', True)
    
    # Verify llama client failure was tracked
    mock_app_state.mark_check_complete.assert_any_call('llama_client_initialized', False, 'Llama client initialization failed: Llama client failed')
    
    # Verify uvicorn was still started (allows health endpoints to report the issue)
    mock_start_uvicorn.assert_called_once()
