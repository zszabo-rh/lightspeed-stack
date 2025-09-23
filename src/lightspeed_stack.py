"""Entry point to the Lightspeed Core Stack REST API service.

This source file contains entry point to the service. It is implemented in the
main() function.
"""

from argparse import ArgumentParser
import asyncio
import logging
from rich.logging import RichHandler

from runners.uvicorn import start_uvicorn
from configuration import configuration
from client import AsyncLlamaStackClientHolder
from utils.llama_stack_version import check_llama_stack_version
from models.config import ServiceConfiguration

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)


def create_argument_parser() -> ArgumentParser:
    """Create and configure argument parser object."""
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="make it verbose",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-d",
        "--dump-configuration",
        dest="dump_configuration",
        help="dump actual configuration into JSON file and quit",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="path to configuration file (default: lightspeed-stack.yaml)",
        default="lightspeed-stack.yaml",
    )

    return parser


def main() -> None:
    """Entry point to the web service."""
    logger.info("Lightspeed Core Stack startup")
    parser = create_argument_parser()
    args = parser.parse_args()

    # Import app_state here to avoid circular imports
    from app.endpoints.health import app_state

    try:
        logger.info("Loading configuration from %s", args.config_file)
        configuration.load_configuration(args.config_file)
        app_state.mark_check_complete('configuration_loaded', True)
        app_state.mark_check_complete('configuration_valid', True)
        
    except Exception as e:
        error_msg = f"Configuration loading failed: {str(e)}"
        logger.error(error_msg)
        app_state.mark_check_complete('configuration_loaded', False, error_msg)
        app_state.mark_check_complete('configuration_valid', False, error_msg)
        # Start the web server with minimal config so health endpoints can report the error
        logger.warning("Starting server with minimal configuration for health reporting")
        start_uvicorn(ServiceConfiguration(host="0.0.0.0", port=8090))  # Bind to all interfaces for container access
        return  # Exit the function, don't continue with normal startup

    # -d or --dump-configuration CLI flags are used to dump the actual configuration
    # to a JSON file w/o doing any other operation
    if args.dump_configuration:
        try:
            configuration.configuration.dump()
            logger.info("Configuration dumped to configuration.json")
        except Exception as e:
            logger.error("Failed to dump configuration: %s", e)
            raise SystemExit(1) from e
        return

    try:
        logger.info("Creating AsyncLlamaStackClient")
        asyncio.run(
            AsyncLlamaStackClientHolder().load(configuration.configuration.llama_stack)
        )
        client = AsyncLlamaStackClientHolder().get_client()
        app_state.mark_check_complete('llama_client_initialized', True)

        # check if the Llama Stack version is supported by the service
        asyncio.run(check_llama_stack_version(client))
        
    except Exception as e:
        error_msg = f"Llama client initialization failed: {str(e)}"
        logger.error(error_msg)
        app_state.mark_check_complete('llama_client_initialized', False, error_msg)
        # Continue startup to allow health reporting
    
    # Provider health will be checked directly by the readiness endpoint

    # if every previous steps don't fail, start the service on specified port
    start_uvicorn(configuration.service_configuration)
    logger.info("Lightspeed Core Stack finished")


if __name__ == "__main__":
    main()
