# Getting started guide

<!-- vim-markdown-toc GFM -->

* [Preface](#preface)
* [Deployment methods](#deployment-methods)
* [Integration with Llama Stack framework](#integration-with-llama-stack-framework)
    * [Llama Stack as a library](#llama-stack-as-a-library)
    * [Llama Stack as a server](#llama-stack-as-a-server)
* [Local deployment](#local-deployment)
    * [Llama Stack used as a library](#llama-stack-used-as-a-library)
    * [Llama Stack used as a separate process](#llama-stack-used-as-a-separate-process)
* [Running from container](#running-from-container)
    * [Llama Stack used as a library](#llama-stack-used-as-a-library-1)
    * [Llama Stack used as a separate process in container](#llama-stack-used-as-a-separate-process-in-container)
    * [Llama Stack configuration](#llama-stack-configuration)

<!-- vim-markdown-toc -->

## Preface

In this document, you will learn how to install and run a service called *Lightspeed Core Stack (LCS)*. It is a service that allows users to communicate with large language models (LLMs), access to RAG databases, call so called agents, process conversation history, ensure that the conversation is only about permitted topics, etc.



## Deployment methods

*Lightspeed Core Stack (LCS)* is built on the Llama Stack framework, which can be run in several modes. Additionally, it is possible to run *LCS* locally (as a regular Python application) or from within a container. This means that it is possible to leverage multiple deployment methods:

* Local deployment
    - Llama Stack framework is used as a library
    - Llama Stack framework is used as a separate process (deployed locally)
* Running from a container
    - Llama Stack framework is used as a library
    - Llama Stack framework is used as a separate process in a container

All those deployments methods will be covered later.



## Integration with Llama Stack framework

The Llama Stack framework can be run as a standalone server and accessed via its the REST API. However, instead of direct communication via the REST API (and JSON format), there is an even better alternative. It is based on the so-called Llama Stack Client. It is a library available for Python, Swift, Node.js or Kotlin, which "wraps" the REST API stack in a suitable way, which is easier for many applications.



### Llama Stack as a library

When this mode is selected, Llama Stack is used as a regular Python library. This means that the library must be installed in the system Python environment, a user-level environment, or a virtual environment. All calls to Llama Stack are performed via standard function or method calls:

![Llama Stack as library](./llama_stack_as_library.svg)

[!NOTE]
Even when Llama Stack is used as a library, it still requires the configuration file `run.yaml` to be presented. This configuration file is loaded during initialization phase.



### Llama Stack as a server

When this mode is selected, Llama Stack is started as a separate REST API service. All communication with Llama Stack is performed via REST API calls, which means that Llama Stack can run on a separate machine if needed.

![Llama Stack as service](./llama_stack_as_service.svg)

[!NOTE]
The REST API schema and semantics can change at any time, especially before version 1.0.0 is released. By using *Lightspeed Core Service*, developers, users, and customers stay isolated from these incompatibilities.



## Local deployment

In this chapter it will be shown how to run LCS locally. This mode is especially useful for developers, as it is possible to work with the latest versions of source codes, including locally made changes and improvements. And last but not least, it is possible to trace, monitor and debug the entire system from within integrated development environment etc.



### Llama Stack used as a separate process

The easiest option is to run Llama Stack in a separate process. This means that there will at least be two running processes involved:

1. Llama Stack framework with open port 8321 (can be easily changed if needed)
1. LCS with open port 8080 (can be easily changed if needed)

### Llama Stack used as a library

## Running from container

### Llama Stack used as a separate process in container

### Llama Stack used as a library




```toml
[project]
name = "llama-stack-demo"
version = "0.1.0"
description = "Default template for PDM package"
authors = []
dependencies = [
    "llama-stack==0.2.14",
    "fastapi>=0.115.12",
    "opentelemetry-sdk>=1.34.0",
    "opentelemetry-exporter-otlp>=1.34.0",
    "opentelemetry-instrumentation>=0.55b0",
    "aiosqlite>=0.21.0",
    "litellm>=1.72.1",
    "uvicorn>=0.34.3",
    "blobfile>=3.0.0",
    "datasets>=3.6.0",
    "sqlalchemy>=2.0.41",
    "faiss-cpu>=1.11.0",
    "mcp>=1.9.4",
    "autoevals>=0.0.129",
    "psutil>=7.0.0",
    "torch>=2.7.1",
    "peft>=0.15.2",
    "trl>=0.18.2"]
requires-python = "==3.12.*"
readme = "README.md"
license = {text = "MIT"}


[tool.pdm]
distribution = false
```

```yaml
version: '2'
image_name: minimal-viable-llama-stack-configuration

apis:
  - agents
  - datasetio
  - eval
  - inference
  - post_training
  - safety
  - scoring
  - telemetry
  - tool_runtime
  - vector_io
benchmarks: []
container_image: null
datasets: []
external_providers_dir: null
inference_store:
  db_path: .llama/distributions/ollama/inference_store.db
  type: sqlite
logging: null
metadata_store:
  db_path: .llama/distributions/ollama/registry.db
  namespace: null
  type: sqlite
providers:
  agents:
  - config:
      persistence_store:
        db_path: .llama/distributions/ollama/agents_store.db
        namespace: null
        type: sqlite
      responses_store:
        db_path: .llama/distributions/ollama/responses_store.db
        type: sqlite
    provider_id: meta-reference
    provider_type: inline::meta-reference
  datasetio:
  - config:
      kvstore:
        db_path: .llama/distributions/ollama/huggingface_datasetio.db
        namespace: null
        type: sqlite
    provider_id: huggingface
    provider_type: remote::huggingface
  - config:
      kvstore:
        db_path: .llama/distributions/ollama/localfs_datasetio.db
        namespace: null
        type: sqlite
    provider_id: localfs
    provider_type: inline::localfs
  eval:
  - config:
      kvstore:
        db_path: .llama/distributions/ollama/meta_reference_eval.db
        namespace: null
        type: sqlite
    provider_id: meta-reference
    provider_type: inline::meta-reference
  inference:
    - provider_id: openai
      provider_type: remote::openai
      config:
        api_key: ${env.OPENAI_API_KEY}
  post_training:
  - config:
      checkpoint_format: huggingface
      device: cpu
      distributed_backend: null
    provider_id: huggingface
    provider_type: inline::huggingface
  safety:
  - config:
      excluded_categories: []
    provider_id: llama-guard
    provider_type: inline::llama-guard
  scoring:
  - config: {}
    provider_id: basic
    provider_type: inline::basic
  - config: {}
    provider_id: llm-as-judge
    provider_type: inline::llm-as-judge
  - config:
      openai_api_key: '********'
    provider_id: braintrust
    provider_type: inline::braintrust
  telemetry:
  - config:
      service_name: 'lightspeed-stack'
      sinks: sqlite
      sqlite_db_path: .llama/distributions/ollama/trace_store.db
    provider_id: meta-reference
    provider_type: inline::meta-reference
  tool_runtime:
    - provider_id: model-context-protocol
      provider_type: remote::model-context-protocol
      config: {}
  vector_io:
  - config:
      kvstore:
        db_path: .llama/distributions/ollama/faiss_store.db
        namespace: null
        type: sqlite
    provider_id: faiss
    provider_type: inline::faiss
scoring_fns: []
server:
  auth: null
  host: null
  port: 8321
  quota: null
  tls_cafile: null
  tls_certfile: null
  tls_keyfile: null
shields: []
vector_dbs: []

models:
  - model_id: gpt-4-turbo
    provider_id: openai
    model_type: llm
    provider_model_id: gpt-4-turbo
```

In the next step, we need to verify that it is possible to run a tool called `llama`. It was installed in a Python virtual environment and therefore we have to run it via `uv run` command:

```bash
 uv run llama
```

If the installation was successful, the following messages should be displayed on the terminal:

```
usage: llama [-h] {model,stack,download,verify-download} ...

Welcome to the Llama CLI

options:
  -h, --help            show this help message and exit

subcommands:
  {model,stack,download,verify-download}

  model                 Work with llama models
  stack                 Operations for the Llama Stack / Distributions
  download              Download a model from llama.meta.com or Hugging Face Hub
  verify-download       Verify integrity of downloaded model files
```

### Llama Stack configuration

If we try to run the Llama Stack without configuring it, only the exception information is displayed (which is not very user-friendly):

```bash
llama-stack-runner]$ uv run llama stack run
```

```
INFO     2025-07-27 16:56:12,464 llama_stack.cli.stack.run:147 server: No image type or image name provided. Assuming environment packages.
Traceback (most recent call last):
  File "/tmp/ramdisk/llama-stack-runner/.venv/bin/llama", line 10, in <module>
    sys.exit(main())
             ^^^^^^
  File "/tmp/ramdisk/llama-stack-runner/.venv/lib64/python3.12/site-packages/llama_stack/cli/llama.py", line 53, in main
    parser.run(args)
  File "/tmp/ramdisk/llama-stack-runner/.venv/lib64/python3.12/site-packages/llama_stack/cli/llama.py", line 47, in run
    args.func(args)
  File "/tmp/ramdisk/llama-stack-runner/.venv/lib64/python3.12/site-packages/llama_stack/cli/stack/run.py", line 164, in _run_stack_run_cmd
    server_main(server_args)
  File "/tmp/ramdisk/llama-stack-runner/.venv/lib64/python3.12/site-packages/llama_stack/distribution/server/server.py", line 414, in main
    elif args.template:
         ^^^^^^^^^^^^^
AttributeError: 'Namespace' object has no attribute 'template'
```
