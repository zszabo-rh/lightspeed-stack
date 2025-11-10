# Lightspeed Core

![LCORE](images/lcore.jpg)

---

Vladimír Kadlec, 
vkadlec@redhat.com

Pavel Tišnovský,
ptisnovs@redhat.com

---

## Agenda

* Llama Stack
* Lightspeed Core
* Evaluation

---

## What is Llama Stack?

* Framework to create applications with AI
    - chat bots
    - generative AI
    - training and evaluation tools
* Real framework independent on programming language
    - providers
    - RAG, quota control, guardrails, metrics

---

![LS1](images/llama_stack.png)

---

### Easiest usage of Llama Stack

* LLM call
* Processing answer from LLM
* "chatbot v.0.0.1"

---

### In reality, the requirements are larger

* RAG
* Conversation history
* Conversation forking
* Conversation summary
* Facts about user
* MCP calls
* Quota handling
* Answers validation
* Responses validation
* Multiple LLM calls
* Responses evaluation

---

### API and providers

* Fully configurable
* It is possible to retrieve list of APIs
* It is possible to retrieve list of providers
* Warning: more dependencies for providers

---

### Providers (1/2)

<table>
<tr><th>Name</th><th>Meaning</th></tr>
<tr><td>Agents</td><td>interacting with agents</td></tr>
<tr><td>Inference</td><td>interface to LLMs and embedding models</td></tr>
<tr><td>VectorIO</td><td>originally vector DB I/O but now support fulltext search</td></tr>
</table>

---

### Providers (2/2)

<table>
<tr><th>Name</th><th>Meaning</th></tr>
<tr><td>Safety</td><td>questions with improper content detection</td></tr>
<tr><td>Telemetry</td><td>telemetry (OpenTelemetry etc.)</td></tr>
<tr><td>Eval</td><td>evaluation of model answers etc.</td></tr>
<tr><td>DatasetIO</td><td>file I/O (datasets etc.)</td></tr>
</table>

---

![LS-providers](images/llama_stack_providers.svg)

---

### Communication with Llama Stack

* CLI
* REST API
* As a common library (Python etc.)
* Llama Stack client
    - supports REST API
    - support running as a library (async)

---

### Llama Stack client

* Python
* Swift
* Kotlin
* Node.js

---

### Llama Stack as a library

![LS1](images/llama_stack_as_library.svg)

---

### Llama Stack as a service

![LS1](images/llama_stack_as_service.svg)

---

### Run inside container

![LS1](images/llama_stack_in_container.svg)

---

### Llama Stack installation

---

Python ecosystem

```
pdm init
pdm add llama-stack fastapi opentelemetry-sdk \
opentelemetry-exporter-otlp opentelemetry-instrumentation \
aiosqlite litellm uvicorn blobfile
```

---

### Generated project file

```toml
[project]
name = "llama-stack-demo"
version = "0.1.0"
description = "Default template for PDM package"
authors = []
dependencies = [
    "llama-stack==0.2.20",
    "llama-stack-client==0.2.20",
    "opentelemetry-sdk>=1.34.0",
    "opentelemetry-exporter-otlp>=1.34.0",
    "opentelemetry-instrumentation>=0.55b0",
    ...
    ...
    ...
]
requires-python = "==3.12.*"
readme = "README.md"
license = {text = "MIT"}


[tool.pdm]
distribution = false
```

---

### Starting Llama Stack

```bash
uv run llama stack
```

---

### List of Llama Stack API

```bash
uv run llama stack list-apis
```

---

```text
┏━━━━━━━━━━━━━━━━━━━┓
┃ API               ┃
┡━━━━━━━━━━━━━━━━━━━┩
│ providers         │
├───────────────────┤
│ inference         │
├───────────────────┤
│ safety            │
├───────────────────┤
│ agents            │
├───────────────────┤
│ batches           │
├───────────────────┤
│ vector_io         │
├───────────────────┤
│ datasetio         │
├───────────────────┤
│ scoring           │
├───────────────────┤
│ eval              │
├───────────────────┤
│ post_training     │
├───────────────────┤
│ tool_runtime      │
├───────────────────┤
│ telemetry         │
├───────────────────┤
│ models            │
├───────────────────┤
│ shields           │
├───────────────────┤
│ vector_dbs        │
├───────────────────┤
│ datasets          │
├───────────────────┤
│ scoring_functions │
├───────────────────┤
│ benchmarks        │
├───────────────────┤
│ tool_groups       │
├───────────────────┤
│ files             │
├───────────────────┤
│ inspect           │
└───────────────────┘
```

---

### List of providers

```bash
uv run llama stack list-providers
```

---

```text
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ API Type      ┃ Provider Type                  ┃ PIP Package Dependencies                                                                                   ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ agents        │ inline::meta-reference         │ matplotlib,pillow,pandas,scikit-learn,mcp>=1.8.1,aiosqlite,psycopg2-binary,redis,pymongo                   │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ batches       │ inline::reference              │ openai                                                                                                     │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ datasetio     │ inline::localfs                │ pandas                                                                                                     │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ datasetio     │ remote::huggingface            │ datasets                                                                                                   │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ datasetio     │ remote::nvidia                 │ datasets                                                                                                   │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ eval          │ inline::meta-reference         │ tree_sitter,pythainlp,langdetect,emoji,nltk                                                                │
├───────────────┼────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
```

---

Lightspeed Core

![LCORE](images/lcore.jpg)

---

### Based on Llama Stack

* REST API
* Supports Llama Stack in service mode
* Supports Llama Stack in library mode
* Implemented as async Python code

---

![Python](images/python.png)

---

![LS1](images/llama_stack_arch.svg)

---

## Evaluation

* Motivation
* Evaluation tool
    - Ragas
    - Deep Eval
* Statistical significance


---

## Summary

---

## Thank you

