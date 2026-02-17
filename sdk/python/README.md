# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

Protocol/schema generated types live under `src/codex_app_server/generated/`.

## Minimal public API

```python
from codex_app_server import Codex

codex = Codex()  # starts + initializes immediately (raises on failure)
print(codex.init().server_name)

thread = codex.thread_start(model="gpt-5")

turn = thread.turn("Explain Newton's method in 3 bullets")
result = turn.run()  # TurnResult (flat attributes)
print(result.text)
print(result.thread_id)
print(result.turn_id)
print(result.status)   # completed / interrupted / failed
print(result.items)
print(result.error)
print(result.usage)    # ThreadTokenUsageUpdatedNotificationPayload | None

models = codex.models()
print(models[0].id if models else None)

turn2 = thread.turn("Now stream this")
for event in turn2.stream():
    print(event.method)

codex.close()
```

## Surface

- `Codex()` (constructor auto-starts + initializes)
- `Codex.init() -> InitializeResult`
- `Codex.close()`
- `Codex.thread_start(model=None, **opts) -> Thread`
- `Codex.thread(thread_id) -> Thread`
- `Codex.models(include_hidden=False)`
- `Thread.id`
- `Thread.turn(input, **opts) -> Turn`
- `Turn.stream() -> Iterator[Notification]` (all turn notifications/events)
- `Turn.run() -> TurnResult` (`completed`, optional `usage`)

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
