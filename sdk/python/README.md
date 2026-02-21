# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

## Install

```bash
cd sdk/python
python -m pip install -e .
```

## 5-minute Quickstart

```python
from codex_app_server import Codex, TextInput

with Codex() as codex:
    print("Server:", codex.metadata.server_name, codex.metadata.server_version)

    thread = codex.thread_start(model="gpt-5")
    result = thread.turn(TextInput("Say hello in one sentence.")).run()

    print("Thread:", result.thread_id)
    print("Turn:", result.turn_id)
    print("Status:", result.status)
    print("Text:", result.text)
```

Expected output (example):

```text
Server: codex-app-server 0.x.y
Thread: thr_abc123
Turn: turn_def456
Status: completed
Text: Hello! Nice to meet you.
```

## Task-Oriented Usage

### Text turn

```python
from codex_app_server import Codex, TextInput

with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")
    result = thread.turn(TextInput("Explain Newton's method in 3 bullets.")).run()
    print(result.text)
```

### Image + text in one turn

```python
from codex_app_server import Codex, TextInput, ImageInput

with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")
    result = thread.turn([
        TextInput("What is in this image? Give 3 bullets."),
        ImageInput("https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"),
    ]).run()
    print(result.text)
```

### Resume an existing thread

```python
from codex_app_server import Codex, TextInput

THREAD_ID = "thr_123"  # replace with a real thread id

with Codex() as codex:
    thread = codex.thread(THREAD_ID)
    result = thread.turn(TextInput("Continue where we left off.")).run()
    print(result.text)
```

### Interrupt and steer

```python
from codex_app_server import Codex, TextInput

with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")

    started = thread.turn(TextInput("Start a long answer"))
    codex.turn_interrupt(thread.id, started.id)

    steer = codex.turn_steer(
        thread.id,
        started.id,
        TextInput("Use 5 short bullets and focus on tradeoffs."),
    )
    print("Steered turn:", steer.turnId)
```

## Sync vs Async

- Use `Codex` for most scripts and CLIs. It is the smallest, most stable SDK surface.
- Use `AsyncAppServerClient` (`codex_app_server.async_client`) for async applications, notebooks, and when you need to integrate with other async I/O.
- The APIs are intentionally parallel: start/resume threads, start turns, stream notifications, and model listing exist in both sync and async forms.

## Error Handling / Troubleshooting

| Common issue | Fix |
| --- | --- |
| `FileNotFoundError` / cannot launch `codex` | Install Codex CLI and ensure `codex` is on `PATH`, or set `AppServerConfig(codex_bin="/path/to/codex")`. |
| Constructor fails during `Codex()` startup | Verify local auth/session for Codex CLI, then retry. The constructor starts and initializes eagerly. |
| `MethodNotFoundError` | Check that the method exists in app-server v2 and that client/server versions are compatible. |
| `InvalidParamsError` | Validate parameter names and types (camelCase is used on the wire). |
| `ServerBusyError` or overload-related failures | Retry with backoff via `retry_on_overload(...)` or `request_with_retry_on_overload(...)`. |
| Turn appears to hang | Consume notifications until `turn/completed`; `Turn.run()` does this automatically for the minimal API. |
| No real integration tests running locally | Set `RUN_REAL_CODEX_TESTS=1` and ensure `codex` is installed/authenticated. |

## Compatibility

- Python versions: `>=3.10` (tested classifiers: 3.10, 3.11, 3.12, 3.13).
- Server compatibility: this SDK targets Codex `app-server` JSON-RPC v2.
- App-server version: use a recent `codex` CLI/app-server build that supports the v2 methods used by this SDK.

## Testing Confidence

- Unit/fixture tests: default `pytest` run uses a fake app-server and covers request/response shape, event flow, errors, retries, typed wrappers, and minimal API behavior.
- Real integration tests: `tests/test_real_app_server_integration.py` is env-gated and runs only when `RUN_REAL_CODEX_TESTS=1` and `codex` is available.

## Surface (minimal API)

- `Codex()` (constructor auto-starts + initializes)
- `Codex.metadata: InitializeResult`
- `Codex.close()`
- `Codex.thread_start(...) -> Thread`
- `Codex.thread(thread_id) -> Thread`
- `Codex.thread_resume(thread_id, ...) -> Thread`
- `Codex.thread_list(...) -> ThreadListResponse`
- `Codex.thread_read(thread_id, include_turns=False) -> ThreadReadResponse`
- `Codex.thread_fork(thread_id, ...) -> Thread`
- `Codex.thread_archive(thread_id) -> None`
- `Codex.thread_unarchive(thread_id) -> Thread`
- `Codex.thread_set_name(thread_id, name) -> None`
- `Codex.thread_compact(thread_id) -> ThreadCompactStartResponse`
- `Codex.turn_steer(thread_id, expected_turn_id, input) -> TurnSteerResponse`
- `Codex.turn_interrupt(thread_id, turn_id) -> None`
- `Codex.models(include_hidden=False) -> ModelListResponse`
- `Thread.id`
- `Thread.turn(input) -> Turn`
- `Turn.stream() -> Iterator[Notification]` (all turn notifications/events)
- `Turn.run() -> TurnResult` (`thread_id`, `turn_id`, `status`, `error`, `text`, `items`, optional `usage`)

`input` is unified: typed input item or list of typed input items.

Protocol/schema generated types live under `src/codex_app_server/generated/`.
Full v2 models are generated into `src/codex_app_server/generated/v2_all/`.

## Examples

See `examples/README.md` for practical examples, including async parity, robust error handling/retry, and a mini CLI app.
