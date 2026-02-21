# SDK UX Examples

This directory shows practical user-facing usage patterns for the Python SDK.

## Files

- `01_quickstart_constructor.py` - constructor-first flow (`Codex()` auto-starts/initializes).
- `02_turn_run.py` - run a turn and read `TurnResult` fields.
- `03_turn_stream_events.py` - stream full turn notifications/events.
- `04_models_and_metadata.py` - inspect startup metadata and model list.
- `05_existing_thread.py` - attach to an existing thread id and continue.
- `06_thread_lifecycle_and_controls.py` - resume/list/read/fork/archive/unarchive/set_name/compact plus steer/interrupt.
- `07_image_and_text.py` - send text plus remote image in one turn.
- `08_local_image_and_text.py` - send text plus local image in one turn.
- `09_async_parity.py` - async parity for initialize, thread start, turn start, and event streaming.
- `10_error_handling_and_retry.py` - typed JSON-RPC error handling plus overload retry backoff.
- `11_cli_mini_app.py` - mini end-to-end interactive CLI over one persistent thread.

## Run

From `sdk/python`:

```bash
python examples/01_quickstart_constructor.py
```

For async example:

```bash
python examples/09_async_parity.py
```

(Requires local `codex` app-server availability and auth.)
