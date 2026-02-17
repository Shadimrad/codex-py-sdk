# SDK UX Examples

This directory shows practical user-facing usage patterns for the Python SDK.

## Files

- `01_quickstart_constructor.py` — constructor-first flow (`Codex()` auto-starts/initializes).
- `02_turn_run.py` — run a turn and read `TurnResult` flat attributes.
- `03_turn_stream_events.py` — stream full turn notifications/events.
- `04_models_and_metadata.py` — inspect startup metadata and model list.
- `05_existing_thread.py` — attach to an existing thread id and continue.
- `06_thread_lifecycle_and_controls.py` — resume/list/read/fork/archive/unarchive/set_name/compact + steer/interrupt.
- `legacy_appserver_client_basic.py` — low-level `AppServerClient` usage for advanced/internal needs.

## Run

From `sdk/python`:

```bash
python examples/01_quickstart_constructor.py
```

(Requires local `codex` app-server availability and auth.)
