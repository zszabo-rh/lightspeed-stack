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


