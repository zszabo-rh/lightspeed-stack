# Getting started guide

<!-- vim-markdown-toc GFM -->

* [Foobar](#foobar)

<!-- vim-markdown-toc -->

## Deployment methods

![Llama Stack as library](./llama_stack_as_library.svg)
![Llama Stack as service](./llama_stack_as_service.svg)

## Local deployment

### Llama Stack used as a library

### Llama Stack used as a separate process

## Running from container

### Llama Stack used as a library

### Llama Stack used as a separate process in container



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
