# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

## Minimal public API

```python
from codex_app_server import Codex

codex = Codex()
codex.start()
codex.initialize()

thread = codex.thread_start(model="gpt-5")

turn = thread.turn("Explain Newton's method in 3 bullets")
result = turn.run()  # typed completed + optional typed usage + text
print(result.text)
print(result.completed.turn.status)  # completed / interrupted / failed
print(result.items)                 # alias for result.completed.turn.items
print(result.usage)                 # ThreadTokenUsageUpdatedNotificationPayload | None

turn2 = thread.turn("Now stream this")
for event in turn2.stream():
    print(event.method)

codex.close()
```

## Surface

- `Codex.start()`
- `Codex.initialize()`
- `Codex.close()`
- `Codex.thread_start(model=None, **opts) -> Thread`
- `Codex.thread(thread_id) -> Thread`
- `Codex.models(include_hidden=False)`
- `Thread.id`
- `Thread.turn(input, **opts) -> Turn`
- `Turn.stream() -> Iterator[Notification]` (all turn notifications/events)
- `Turn.run() -> RunResult` (`text`, typed `completed`, optional typed `usage`, `items`)

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
