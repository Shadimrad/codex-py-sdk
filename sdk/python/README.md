# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

`Codex` / `AsyncCodex` are ergonomic aliases over `AppServerClient` / `AsyncAppServerClient`.

## Install

```bash
cd sdk/python
python -m pip install -e .
```

For local development/tests:

```bash
python -m pip install -e '.[dev]'
```

## Quickstart

```python
from codex_app_server import Codex

codex = Codex()
codex.start()
codex.initialize()

thread = codex.thread_start(model="gpt-5")
thread_id = thread["thread"]["id"]

turn = codex.turn_text(thread_id, "Explain Newton's method in 3 bullets")
codex.wait_for_turn_completed(turn["turn"]["id"])

codex.close()
```

## Thread-first fluent API

```python
from codex_app_server import Codex

codex = Codex()
codex.start()
codex.initialize()

thread = codex.thread_start_session(model="gpt-5")
result = thread.ask_result("Give me one sentence about gravity")
print(result.text)

for chunk in thread.stream_text("Now stream 3 short words"):
    print(chunk, end="", flush=True)

codex.close()
```

## Typed wrappers

```python
started = client.thread_start_typed(model="gpt-5")
resumed = client.thread_resume_typed(started.thread.id)
models = client.model_list_typed()
turn = client.turn_text_typed(started.thread.id, "hello")
```

Schema wrappers (generated from protocol schemas):

```python
started = client.thread_start_schema(model="gpt-5")
turn = client.turn_text_schema(started.thread.id, "hello")
print(turn.turn.status)
```

## Tests

```bash
cd sdk/python
pytest
```

Optional real integration tests:

```bash
RUN_REAL_CODEX_TESTS=1 pytest tests/test_real_app_server_integration.py
```
