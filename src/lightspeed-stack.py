"""Lightspeed stack."""

from runners.uvicorn import start_uvicorn
import version

if __name__ == "__main__":
    print("Lightspeed stack")
    start_uvicorn()
