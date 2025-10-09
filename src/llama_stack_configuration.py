"""Llama Stack configuration handling."""

import yaml

from log import get_logger

from models.config import Configuration

logger = get_logger(__name__)


# pylint: disable=too-many-ancestors
class YamlDumper(yaml.Dumper):
    """Custom YAML dumper with proper indentation levels."""

    def increase_indent(self, flow: bool = False, indentless: bool = False) -> None:
        """Control the indentation level of formatted YAML output."""
        _ = indentless
        return super().increase_indent(flow, False)


def generate_configuration(
    input_file: str, output_file: str, config: Configuration
) -> None:
    """Generate new Llama Stack configuration."""
    logger.info("Reading Llama Stack configuration from file %s", input_file)

    with open(input_file, "r", encoding="utf-8") as file:
        ls_config = yaml.safe_load(file)

    logger.info("Processing Llama Stack configuration")
    _ = config

    logger.info("Writing Llama Stack configuration into file %s", output_file)

    with open(output_file, "w", encoding="utf-8") as file:
        yaml.dump(ls_config, file, Dumper=YamlDumper, default_flow_style=False)
