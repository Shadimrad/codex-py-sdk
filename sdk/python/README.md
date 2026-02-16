# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

## Minimal public API

```python
from codex_app_server import Codex

codex = Codex()
codex.start()
codex.initialize()

thread = codex.thread_start(model="gpt-5")

# non-streaming
answer = thread.run("Explain Newton's method in 3 bullets")
print(answer)

# streaming
for chunk in thread.stream("Now stream 3 short words"):
    print(chunk, end="", flush=True)
print()

codex.close()
```

### Surface

- `Codex.start()`
- `Codex.initialize()`
- `Codex.close()`
- `Codex.thread_start(model=None, **opts) -> Thread`
- `Codex.thread(thread_id) -> Thread`
- `Codex.models(include_hidden=False)`
- `Thread.id`
- `Thread.turn(input, **opts)`
- `Thread.run(input, **opts) -> str`
- `Thread.stream(input, **opts) -> Iterator[str]`

`input` is unified: string, dict item, or list of items.

## Install

```bash
cd sdk/python
python -m pip install -e .
```

## Tests

```bash
cd sdk/python
pytest
```
