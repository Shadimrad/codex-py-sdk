# Codex App Server Python SDK (v2)

Python SDK for `codex app-server` JSON-RPC v2 over stdio.

Protocol/schema generated types live under `src/codex_app_server/generated/`.
Full v2 models are generated into `src/codex_app_server/generated/v2_all/` via `datamodel-code-generator` (`scripts/generate_all_v2_types.py`).

## Minimal public API

```python
from codex_app_server import Codex, TextInput, ImageInput, LocalImageInput

codex = Codex()  # starts + initializes immediately (raises on failure)
print(codex.metadata.server_name)

thread = codex.thread_start(model="gpt-5")

turn = thread.turn(TextInput("Explain Newton's method in 3 bullets"))
result = turn.run()  # TurnResult (flat attributes, typed turn items)
print(result.text)
print(result.thread_id)
print(result.turn_id)
print(result.status)   # completed / interrupted / failed
print(result.items)
print(result.error)
print(result.usage)    # ThreadTokenUsageUpdatedNotificationPayload | None

models = codex.models()  # ModelListResponse
print(models.data[0].id if models.data else None)

turn2 = thread.turn(TextInput("Now stream this"))
for event in turn2.stream():
    print(event.method)

codex.close()
```

## Surface

- `Codex()` (constructor auto-starts + initializes)
- `Codex.metadata: InitializeResult`
- `Codex.close()`
- `Codex.thread_start(model=None, **opts) -> Thread`
- `Codex.thread(thread_id) -> Thread`
- `Codex.thread_resume(thread_id, **opts) -> Thread`
- `Codex.thread_list(**opts) -> ThreadListResponse`
- `Codex.thread_read(thread_id, include_turns=False) -> ThreadReadResponse`
- `Codex.thread_fork(thread_id, **opts) -> Thread`
- `Codex.thread_archive(thread_id) -> None`
- `Codex.thread_unarchive(thread_id) -> Thread`
- `Codex.thread_set_name(thread_id, name) -> None`
- `Codex.thread_compact(thread_id) -> ThreadCompactStartResponse`
- `Codex.turn_steer(thread_id, expected_turn_id, input) -> TurnSteerResponse`
- `Codex.turn_interrupt(thread_id, turn_id) -> None`
- `Codex.models(include_hidden=False) -> ModelListResponse`
- `Thread.id`
- `Thread.turn(input, **opts) -> Turn`
- `Turn.stream() -> Iterator[Notification]` (all turn notifications/events)
- `Turn.run() -> TurnResult` (`thread_id`, `turn_id`, `status`, `error`, `text`, `items: list[ThreadItem]`, optional `usage`)

`input` is unified: string, typed input item, or list of typed input items.

### Input examples (text + image)

```python
# plain text
thread.turn(TextInput("Describe this image")).run()

# remote image
thread.turn([
    TextInput("What is in this image?"),
    ImageInput("https://example.com/cat.jpg"),
]).run()

# local image
thread.turn([
    TextInput("Read this screenshot"),
    LocalImageInput("./screenshot.png"),
]).run()
```

## Install

```bash
cd sdk/python
python -m pip install -e .
```

## Examples

See `examples/README.md` for UX-focused examples covering constructor flow, run, streaming events, metadata/models, existing-thread continuation, and image+text turns.

## Tests

```bash
cd sdk/python
pytest
```
