"""Lightspeed stack."""

from runners.uvicorn import start_uvicorn
from models.config import Configuration
from configuration import configuration


if __name__ == "__main__":
    print("Lightspeed stack")
    configuration.load_configuration("lightspeed-stack.yaml")
    print(configuration)
    print(configuration.llama_stack_configuration)
    start_uvicorn()
