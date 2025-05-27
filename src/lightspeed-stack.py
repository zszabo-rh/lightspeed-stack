"""Lightspeed stack."""

from argparse import ArgumentParser
import logging

from runners.uvicorn import start_uvicorn
from models.config import Configuration
from configuration import configuration

from rich.logging import RichHandler

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)


def create_argument_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        help="make it verbose",
        action="store_true",
        default=None,
    )
    parser.add_argument(
        "-d",
        "--dump-configuration",
        dest="dump_configuration",
        help="dump actual configuration into JSON file and quit",
        action="store_true",
        default=None,
    )
    return parser


def dump_configuration(configuration: Configuration) -> None:
    """Dump actual configuration into JSON file."""
    with open("configuration.json", "w", encoding="utf-8") as fout:
        fout.write(configuration.model_dump_json(indent=4))


def main() -> None:
    logger.info("Lightspeed stack startup")
    parser = create_argument_parser()
    args = parser.parse_args()

    configuration.load_configuration("lightspeed-stack.yaml")
    logger.info("Configuration: %s", configuration.configuration)
    logger.info(
        "Llama stack configuration: %s", configuration.llama_stack_configuration
    )

    if args.dump_configuration:
        dump_configuration(configuration.configuration)
    else:
        start_uvicorn()
    logger.info("Lightspeed stack finished")


if __name__ == "__main__":
    main()
