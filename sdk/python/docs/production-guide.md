# Production Guide

Use this when moving from local experiments to reliable long-running usage.

## Lifecycle and shutdown

Preferred pattern:

```python
from codex_app_server import Codex

with Codex() as codex:
    # work
    ...
```

Why:

- `Codex()` starts and initializes eagerly.
- Exiting the context always calls `close()` and terminates the app-server process.

If you cannot use a context manager, call `close()` in `finally`.

## Retries for transient overload

Use `retry_on_overload` for operations that can fail with `ServerBusyError`:

```python
from codex_app_server.retry import retry_on_overload

result = retry_on_overload(
    lambda: thread.turn(TextInput("Summarize this")).run(),
    max_attempts=4,
    initial_delay_s=0.25,
    max_delay_s=2.0,
)
```

Retry behavior:

- Exponential backoff with jitter.
- Retries only when `is_retryable_error(exc)` is true.
- Raises the last exception after attempts are exhausted.

## Error handling strategy

Catch specific JSON-RPC errors first:

```python
from codex_app_server.errors import (
    InvalidParamsError,
    MethodNotFoundError,
    ServerBusyError,
    JsonRpcError,
    TransportClosedError,
)

try:
    result = thread.turn(TextInput("...")).run()
except ServerBusyError:
    # retry or return 503 in your app boundary
    ...
except InvalidParamsError:
    # caller bug or schema mismatch
    ...
except MethodNotFoundError:
    # client/server version mismatch
    ...
except TransportClosedError:
    # restart client/process
    ...
except JsonRpcError:
    # fallback for other server errors
    ...
```

Treat `TurnResult.status == "failed"` as a completed turn with model failure details in `TurnResult.error`.

## Timeouts

The SDK transport itself is blocking and does not expose per-request timeout arguments.

Practical approaches:

- Enforce timeout at the process or job boundary.
- Wrap blocking calls in your own executor/thread and apply timeout there.
- For user-facing flows, prefer streaming (`Turn.stream()`) so you can surface progress and enforce your own timeout logic.

## Logging and observability

Recommended fields per turn:

- `thread_id`, `turn_id`
- `status`
- `error` (if any)
- latency (wall clock around `run()`)
- token usage (`TurnResult.usage`, when present)

Keep logs at your app boundary so you can include request IDs and user IDs from your system.

## Sync vs async in production

- Use `Codex` for scripts, workers, and CLIs.
- Use `AsyncAppServerClient` when your app is already asyncio-based.
- Prefer one client per worker/process and reuse threads instead of creating a new process per prompt.

## Resume and recovery patterns

- Persist `thread.id` after `thread_start`.
- Resume later with `codex.thread(thread_id)` or `codex.thread_resume(thread_id, ...)`.
- On `TransportClosedError`, create a new `Codex` and continue the same logical thread by ID.

## Reference implementation

See `examples/12_production_pattern.py` for a robust loop with retries and graceful shutdown.
