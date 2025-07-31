# Getting started guide

<!-- vim-markdown-toc GFM -->

* [Preface](#preface)
* [Deployment methods](#deployment-methods)
* [Integration with Llama Stack framework](#integration-with-llama-stack-framework)
    * [Llama Stack as a library](#llama-stack-as-a-library)
    * [Llama Stack as a server](#llama-stack-as-a-server)
* [Local deployment](#local-deployment)
    * [Llama Stack used as a separate process](#llama-stack-used-as-a-separate-process)
        * [Prerequisities](#prerequisities)
        * [Installation of all required tools](#installation-of-all-required-tools)
        * [Installing dependencies for Llama Stack](#installing-dependencies-for-llama-stack)
        * [Check if Llama Stack can be started](#check-if-llama-stack-can-be-started)
        * [Llama Stack configuration](#llama-stack-configuration)
        * [Run Llama Stack in a separate process](#run-llama-stack-in-a-separate-process)
        * [LCS configuration to connect to Llama Stack running in separate process](#lcs-configuration-to-connect-to-llama-stack-running-in-separate-process)
        * [Start LCS](#start-lcs)
        * [Check if service runs](#check-if-service-runs)
    * [Llama Stack used as a library](#llama-stack-used-as-a-library)
        * [Prerequisities](#prerequisities-1)
        * [Installation of all required tools](#installation-of-all-required-tools-1)
        * [Installing dependencies for Llama Stack](#installing-dependencies-for-llama-stack-1)
        * [Llama Stack configuration](#llama-stack-configuration-1)
        * [LCS configuration to use Llama Stack in library mode](#lcs-configuration-to-use-llama-stack-in-library-mode)
        * [Start LCS](#start-lcs-1)
        * [Check if service runs](#check-if-service-runs-1)
* [Running from container](#running-from-container)
    * [Llama Stack used as a separate process in container](#llama-stack-used-as-a-separate-process-in-container)
    * [Llama Stack used as a library](#llama-stack-used-as-a-library-1)

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



#### Prerequisities

1. Python 3.12 or 3.13
1. `pip` tool installed
1. `jq` and `curl` tools installed

#### Installation of all required tools

1. `pip install --user uv`
1. `sudo dnf install curl jq`

#### Installing dependencies for Llama Stack


1. Create a new directory
    ```bash
    mkdir llama-stack-server
    cd llama-stack-server
    ```
1. Create project file named `pyproject.toml` in this directory. This file should have the following content:
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
1. Run the following command to install all dependencies:

    ```bash
    uv sync
    ```

    You should get the following output:

    ```ascii
    Using CPython 3.12.10 interpreter at: /usr/bin/python3
    Creating virtual environment at: .venv
    Resolved 136 packages in 1.90s
          Built sqlalchemy==2.0.42
    Prepared 14 packages in 10.04s
    Installed 133 packages in 4.36s
     + accelerate==1.9.0
     + aiohappyeyeballs==2.6.1
     ...
     ...
     ...
     + transformers==4.54.0
     + triton==3.3.1
     + trl==0.20.0
     + typing-extensions==4.14.1
     + typing-inspection==0.4.1
     + tzdata==2025.2
     + urllib3==2.5.0
     + uvicorn==0.35.0
     + wcwidth==0.2.13
     + wrapt==1.17.2
     + xxhash==3.5.0
     + yarl==1.20.1
     + zipp==3.23.0
    ```



#### Check if Llama Stack can be started

1. In the next step, we need to verify that it is possible to run a tool called `llama`. It was installed into a Python virtual environment and therefore we have to run it via `uv run` command:
    ```bash
     uv run llama
    ```
1. If the installation was successful, the following messages should be displayed on the terminal:
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
1. If we try to run the Llama Stack without configuring it, only the exception information is displayed (which is not very user-friendly):
    ```bash
    uv run llama stack run
    ```
    Output:
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



#### Llama Stack configuration

Llama Stack needs to be configured properly. For using the default runnable Llama Stack a file named `run.yaml` with following content needs to be created:

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



#### Run Llama Stack in a separate process

1. Export OpenAI key by using the following command:
    ```bash
    export OPENAI_API_KEY="sk-foo-bar-baz"
    ```
1. Run the following command:
    ```bash
    uv run llama stack run run.yaml
    ```
1. Check the output on terminal, it should look like:
    ```
    INFO     2025-07-29 15:26:20,864 llama_stack.cli.stack.run:126 server: Using run configuration: run.yaml
    INFO     2025-07-29 15:26:20,877 llama_stack.cli.stack.run:147 server: No image type or image name provided. Assuming environment packages.
    INFO     2025-07-29 15:26:21,277 llama_stack.distribution.server.server:441 server: Using config file: run.yaml
    INFO     2025-07-29 15:26:21,279 llama_stack.distribution.server.server:443 server: Run configuration:
    INFO     2025-07-29 15:26:21,285 llama_stack.distribution.server.server:445 server: apis:
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
             image_name: minimal-viable-llama-stack-configuration
             inference_store:
               db_path: .llama/distributions/ollama/inference_store.db
               type: sqlite
             logging: null
             metadata_store:
               db_path: .llama/distributions/ollama/registry.db
               namespace: null
               type: sqlite
             models:
             - metadata: {}
               model_id: gpt-4-turbo
               model_type: !!python/object/apply:llama_stack.apis.models.models.ModelType
               - llm
               provider_id: openai
               provider_model_id: gpt-4-turbo
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
               - config:
                   api_key: '********'
                 provider_id: openai
                 provider_type: remote::openai
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
                   service_name: lightspeed-stack
                   sinks: sqlite
                   sqlite_db_path: .llama/distributions/ollama/trace_store.db
                 provider_id: meta-reference
                 provider_type: inline::meta-reference
               tool_runtime:
               - config: {}
                 provider_id: model-context-protocol
                 provider_type: remote::model-context-protocol
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
             tool_groups: []
             vector_dbs: []
             version: 2
    ```
1. The server with Llama Stack listens on port 8321. A description of the REST API is available in the form of OpenAPI (endpoint /openapi.json), but other endpoints can also be used. It is possible to check if Llama Stack runs as REST API server by retrieving its version. We use `curl` and `jq` tools for this purposes:
    ```bash
    curl localhost:8321/v1/version | jq .
    ```
    The output should be in this form:
    ```json
    {
      "version": "0.2.14"
    }
    ```


#### LCS configuration to connect to Llama Stack running in separate process

```yaml
name: Lightspeed Core Service (LCS)
service:
  host: localhost
  port: 8080
  auth_enabled: false
  workers: 1
  color_log: true
  access_log: true
llama_stack:
  use_as_library_client: false
  url: http://localhost:8321
  api_key: xyzzy
user_data_collection:
  feedback_enabled: true
  feedback_storage: "/tmp/data/feedback"
  transcripts_enabled: true
  transcripts_storage: "/tmp/data/transcripts"
  data_collector:
    enabled: false
    ingress_server_url: null
    ingress_server_auth_token: null
    ingress_content_service_name: null
    collection_interval: 7200  # 2 hours in seconds
    cleanup_after_send: true
    connection_timeout_seconds: 30
authentication:
  module: "noop"
```

#### Start LCS

```bash
make run
```

```
uv run src/lightspeed_stack.py
[07/29/25 15:43:35] INFO     Initializing app                                                                                 main.py:19
                    INFO     Including routers                                                                                main.py:68
INFO:     Started server process [1922983]
INFO:     Waiting for application startup.
                    INFO     Registering MCP servers                                                                          main.py:81
                    DEBUG    No MCP servers configured, skipping registration                                               common.py:36
                    INFO     Setting up model metrics                                                                         main.py:84
[07/29/25 15:43:35] DEBUG    Set provider/model configuration for openai/gpt-4-turbo to 0                                    utils.py:45
                    INFO     App startup complete                                                                             main.py:86
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8080 (Press CTRL+C to quit)
```

#### Check if service runs

```bash
curl localhost:8080/v1/models | jq .
```

```
{
  "models": [
    {
      "identifier": "gpt-4-turbo",
      "metadata": {},
      "api_model_type": "llm",
      "provider_id": "openai",
      "type": "model",
      "provider_resource_id": "gpt-4-turbo",
      "model_type": "llm"
    }
  ]
}
```



### Llama Stack used as a library

It is possible to run Lightspeed Core Stack service with Llama Stack "embedded" as a Python library. This means that just one process will be running and only one port (for example 8080) will be accessible.




#### Prerequisities

1. Python 3.12 or 3.13
1. `pip` tool installed
1. `jq` and `curl` tools installed

#### Installation of all required tools

1. `pip install --user uv`
1. `sudo dnf install curl jq`

#### Installing dependencies for Llama Stack

1. Clone LCS repository
1. Add and install all required dependencies
    ```bash
    uv add \
    "llama-stack==0.2.16" \
    "fastapi>=0.115.12" \
    "opentelemetry-sdk>=1.34.0" \
    "opentelemetry-exporter-otlp>=1.34.0" \
    "opentelemetry-instrumentation>=0.55b0" \
    "aiosqlite>=0.21.0" \
    "litellm>=1.72.1" \
    "uvicorn>=0.34.3" \
    "blobfile>=3.0.0" \
    "datasets>=3.6.0" \
    "sqlalchemy>=2.0.41" \
    "faiss-cpu>=1.11.0" \
    "mcp>=1.9.4" \
    "autoevals>=0.0.129" \
    "psutil>=7.0.0" \
    "torch>=2.7.1" \
    "peft>=0.15.2" \
    "trl>=0.18.2"
    ```
1. Check if all dependencies are really installed
    ```
    Resolved 195 packages in 1.19s
          Built lightspeed-stack @ file:///tmp/ramdisk/lightspeed-stack
    Prepared 12 packages in 1.72s
    Installed 60 packages in 4.47s
     + accelerate==1.9.0
     + autoevals==0.0.129
     + blobfile==3.0.0
     + braintrust-core==0.0.59
     + chevron==0.14.0
     + datasets==4.0.0
     + dill==0.3.8
     + faiss-cpu==1.11.0.post1
     + fsspec==2025.3.0
     + greenlet==3.2.3
     + grpcio==1.74.0
     + httpx-sse==0.4.1
     ~ lightspeed-stack==0.1.1 (from file:///tmp/ramdisk/lightspeed-stack)
     + litellm==1.74.9.post1
     + lxml==6.0.0
     + mcp==1.12.2
     + mpmath==1.3.0
     + multiprocess==0.70.16
     + networkx==3.5
     + nvidia-cublas-cu12==12.6.4.1
     + nvidia-cuda-cupti-cu12==12.6.80
     + nvidia-cuda-nvrtc-cu12==12.6.77
     + nvidia-cuda-runtime-cu12==12.6.77
     + nvidia-cudnn-cu12==9.5.1.17
     + nvidia-cufft-cu12==11.3.0.4
     + nvidia-cufile-cu12==1.11.1.6
     + nvidia-curand-cu12==10.3.7.77
     + nvidia-cusolver-cu12==11.7.1.2
     + nvidia-cusparse-cu12==12.5.4.2
     + nvidia-cusparselt-cu12==0.6.3
     + nvidia-nccl-cu12==2.26.2
     + nvidia-nvjitlink-cu12==12.6.85
     + nvidia-nvtx-cu12==12.6.77
     + opentelemetry-api==1.36.0
     + opentelemetry-exporter-otlp==1.36.0
     + opentelemetry-exporter-otlp-proto-common==1.36.0
     + opentelemetry-exporter-otlp-proto-grpc==1.36.0
     + opentelemetry-exporter-otlp-proto-http==1.36.0
     + opentelemetry-instrumentation==0.57b0
     + opentelemetry-proto==1.36.0
     + opentelemetry-sdk==1.36.0
     + opentelemetry-semantic-conventions==0.57b0
     + peft==0.16.0
     + polyleven==0.9.0
     + psutil==7.0.0
     + pyarrow==21.0.0
     + pycryptodomex==3.23.0
     + pydantic-settings==2.10.1
     + safetensors==0.5.3
     + setuptools==80.9.0
     + sqlalchemy==2.0.42
     + sse-starlette==3.0.2
     + sympy==1.14.0
     + tokenizers==0.21.4
     + torch==2.7.1
     + transformers==4.54.1
     + triton==3.3.1
     + trl==0.20.0
     + wrapt==1.17.2
     + xxhash==3.5.0
    ```

#### Llama Stack configuration

Llama Stack needs to be configured properly. For using the default runnable Llama Stack a file named `run.yaml` with following content needs to be created:

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

#### LCS configuration to use Llama Stack in library mode

```yaml
name: Lightspeed Core Service (LCS)
service:
  host: localhost
  port: 8080
  auth_enabled: false
  workers: 1
  color_log: true
  access_log: true
llama_stack:
  use_as_library_client: true
  library_client_config_path: run.yaml
user_data_collection:
  feedback_enabled: true
  feedback_storage: "/tmp/data/feedback"
  transcripts_enabled: true
  transcripts_storage: "/tmp/data/transcripts"
  data_collector:
    enabled: false
    ingress_server_url: null
    ingress_server_auth_token: null
    ingress_content_service_name: null
    collection_interval: 7200  # 2 hours in seconds
    cleanup_after_send: true
    connection_timeout_seconds: 30
authentication:
  module: "noop"
```

#### Start LCS

1. Export OpenAI key by using the following command:
    ```bash
    export OPENAI_API_KEY="sk-foo-bar-baz"
    ```
1. Run the following command
    ```bash
    make run
    ```
1. Check the output
    ```
    uv run src/lightspeed_stack.py
    Using config run.yaml:
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
    [07/30/25 20:01:53] INFO     Initializing app                                                                                 main.py:19
    [07/30/25 20:01:54] INFO     Including routers                                                                                main.py:68
                        INFO     Registering MCP servers                                                                          main.py:81
                        DEBUG    No MCP servers configured, skipping registration                                               common.py:36
                        INFO     Setting up model metrics                                                                         main.py:84
    [07/30/25 20:01:54] DEBUG    Set provider/model configuration for openai/openai/chatgpt-4o-latest to 0                       utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-3.5-turbo to 0                           utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-3.5-turbo-0125 to 0                      utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-3.5-turbo-instruct to 0                  utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4 to 0                                   utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4-turbo to 0                             utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4o to 0                                  utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4o-2024-08-06 to 0                       utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4o-audio-preview to 0                    utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/gpt-4o-mini to 0                             utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/o1 to 0                                      utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/o1-mini to 0                                 utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/o3-mini to 0                                 utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/o4-mini to 0                                 utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/text-embedding-3-large to 0                  utils.py:45
                        DEBUG    Set provider/model configuration for openai/openai/text-embedding-3-small to 0                  utils.py:45
                        INFO     App startup complete                                                                             main.py:86
    ```

#### Check if service runs

```bash
curl localhost:8080/v1/models | jq .
```

```
{
  "models": [
    {
      "identifier": "gpt-4-turbo",
      "metadata": {},
      "api_model_type": "llm",
      "provider_id": "openai",
      "type": "model",
      "provider_resource_id": "gpt-4-turbo",
      "model_type": "llm"
    }
  ]
}
```



## Running from container

### Llama Stack used as a separate process in container

### Llama Stack used as a library



