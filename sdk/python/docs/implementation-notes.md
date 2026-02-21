# Python SDK Implementation Notes

This document explains **why** the Python SDK is designed this way, what the core functions do, and how to use them.

## Design goals

1. **Small default surface**
   - Most users should only need `Codex`, `Thread`, `Turn`, `TurnResult`, and typed inputs.
2. **Fail-fast startup**
   - `Codex()` starts + initializes app-server immediately, so setup/auth issues show up early.
3. **Typed where it matters**
   - Public methods validate request payloads with generated v2 models.
4. **Event-first internals, simple public API**
   - App-server is event-driven; public API offers both `run()` (easy) and `stream()` (advanced).
5. **Protocol fidelity**
   - Keep naming and payload semantics aligned with app-server JSON-RPC v2.

## Core public objects

## `Codex`

High-level session object. Owns the transport process.

Common methods:

- `thread_start(...) -> Thread`
- `thread(thread_id) -> Thread`
- `thread_resume(thread_id, ...) -> Thread`
- `thread_list(...)`
- `thread_read(thread_id, include_turns=False)`
- `thread_fork(thread_id, ...) -> Thread`
- `thread_archive(thread_id)`
- `thread_unarchive(thread_id) -> Thread`
- `thread_set_name(thread_id, name)`
- `thread_compact(thread_id)`
- `turn_steer(thread_id, expected_turn_id, input)`
- `turn_interrupt(thread_id, turn_id)`
- `models(include_hidden=False)`
- `close()`

`Codex.metadata` contains parsed initialize info (`server_name`, `server_version`) when available.

## `Thread`

Conversation container. Use one thread for multi-turn continuity.

- `thread.turn(input) -> Turn`

## `Turn`

One model execution in a thread.

- `turn.run() -> TurnResult`
  - waits for completion and returns final aggregated result
- `turn.stream() -> Iterator[Notification]`
  - yields raw events for custom handling/progress UIs

## `TurnResult`

Normalized completed turn data:

- `thread_id`
- `turn_id`
- `status`
- `error`
- `text`
- `items`
- `usage`

## Typed input classes

- `TextInput(text)`
- `ImageInput(url)`
- `LocalImageInput(path)`
- `SkillInput(name, path)`
- `MentionInput(name, path)`

You can pass one item or a list.

## Why these choices?

- **Constructor eagerness** avoids hidden lazy failures later.
- **`run()` + `stream()` split** supports both simple scripts and advanced streaming UX.
- **Thread-first API** mirrors how users think: “continue conversation in this thread.”
- **Typed inputs** reduce malformed payloads and keep signatures readable.

## Recommended usage patterns

### Quick happy path

```python
from codex_app_server import Codex, TextInput

with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")
    result = thread.turn(TextInput("Explain CAP theorem in 3 bullets.")).run()
    print(result.text)
```

### Continue a thread later

```python
thread = codex.thread(existing_thread_id)
result = thread.turn(TextInput("Continue where we left off.")).run()
```

### Reliability for transient overload

```python
from codex_app_server.retry import retry_on_overload

result = retry_on_overload(lambda: thread.turn(TextInput("Summarize this")).run())
```

### Handle errors explicitly

```python
from codex_app_server.errors import ServerBusyError, InvalidParamsError, JsonRpcError

try:
    result = thread.turn(TextInput("...")).run()
except ServerBusyError:
    ...  # retry/backoff
except InvalidParamsError:
    ...  # fix caller input
except JsonRpcError as exc:
    ...  # fallback
```

## Notebook

See `sdk/python/notebooks/sdk_walkthrough.ipynb` for a guided runnable walkthrough.
