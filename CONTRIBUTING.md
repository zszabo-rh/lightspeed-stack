# CONTRIBUTING

<!-- the following line is used by tool to autogenerate Table of Content when the document is changed -->
<!-- vim-markdown-toc GFM -->

* [TLDR;](#tldr)
* [Setting up your development environment](#setting-up-your-development-environment)
* [Definition of Done](#definition-of-done)
    * [A deliverable is to be considered “done” when](#a-deliverable-is-to-be-considered-done-when)
* [Automation](#automation)
    * [Pre-commit hook settings](#pre-commit-hook-settings)
    * [Code coverage measurement](#code-coverage-measurement)
    * [Type hints checks](#type-hints-checks)
    * [Linters](#linters)
    * [Security checks](#security-checks)
* [Testing](#testing)
    * [Tips and hints for developing unit tests](#tips-and-hints-for-developing-unit-tests)
        * [Patching](#patching)
        * [Verifying that some exception is thrown](#verifying-that-some-exception-is-thrown)
        * [Checking what was printed and logged to stdout or stderr by the tested code](#checking-what-was-printed-and-logged-to-stdout-or-stderr-by-the-tested-code)
    * [Tips and hints for developing e2e tests](#tips-and-hints-for-developing-e2e-tests)
        * [Detecting which statements are called in real service](#detecting-which-statements-are-called-in-real-service)
* [Benchmarks](#benchmarks)
    * [Running benchmarks](#running-benchmarks)
    * [`pytest-benchmark` package](#pytest-benchmark-package)
    * [Basic usage of `benchmark` fixture](#basic-usage-of-benchmark-fixture)
    * [Combination of `benchmark` fixture with other fixtures](#combination-of-benchmark-fixture-with-other-fixtures)
    * [Example output from benchmarks](#example-output-from-benchmarks)
* [Updating Dependencies](#updating-dependencies)
* [Code style](#code-style)
    * [Docstrings style](#docstrings-style)
* [Adding a new provider/model](#adding-a-new-providermodel)

<!-- vim-markdown-toc -->

## TLDR;

1. Create your own fork of the repo
2. Make changes to the code in your fork
3. Run unit tests and integration tests
4. Check the code with linters
5. Submit PR from your fork to main branch of the project repo


## Prerequisities

- git
- Python 3.11, 3.12, or 3.13
- pip

The development requires at least [Python 3.11](https://docs.python.org/3/whatsnew/3.11.html) due to significant improvement on performance, optimizations which benefit modern ML, AI, LLM, NL stacks, and improved asynchronous processing capabilities. It is also possible to use Python 3.12 or Python 3.13.



### Tooling installation

1. `pip install --user pdm`
1. `pdm --version` -- should return no error



## Setting up your development environment

```bash
# clone your fork
git clone https://github.com/YOUR-GIT-PROFILE/lightspeed-stack.git

# move into the directory
cd lightspeed-stack

# setup your devel environment with pdm
pdm install -G dev

# Now you can run test commands trough make targets, or prefix the rest of commands with `pdm run`, eg. `pdm run make test`

# run unit tests
make unit-tests

# run integration tests
make integration-tests

# code formatting
# (this is also run automatically as part of pre-commit hook if configured)
make format

# code style and docstring style
# (this is also run automatically as part of pre-commit hook if configured)
make verify

# check type hints
# (this is also run automatically as part of pre-commit hook)
make check-types
```

Happy hacking!


