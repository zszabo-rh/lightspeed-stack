# Lightspeed Core Stack installation on MacOS

## Prerequisities

- brew
- git
- Python 3.12 or 3.13
- pip

## Installation steps

1. `brew install uv`
1. `uv --version` -- should return no error
1. Clone the repo to the current dir:
`git clone https://github.com/lightspeed-core/lightspeed-stack`
1. `cd service`
1. `uv info` -- should return no error
1. `uv install` -- if it fails (for example because you ran `uv install` before changing `pyproject.toml`) run:
```sh
uv update
uv install
```

