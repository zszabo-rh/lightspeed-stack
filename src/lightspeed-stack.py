"""Lightspeed stack."""

import yaml

from runners.uvicorn import start_uvicorn
from models.config import Configuration


def load_configuration(filename: str) -> Configuration:
    """Load configuration from YAML file."""
    with open(filename, encoding="utf-8") as fin:
        config_dict = yaml.safe_load(fin)
        return Configuration(**config_dict)


if __name__ == "__main__":
    print("Lightspeed stack")
    configuration = load_configuration("lightspeed-stack.yaml")
    print(configuration)
    start_uvicorn()
