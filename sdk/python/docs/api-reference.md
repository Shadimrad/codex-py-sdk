# API Reference

This page documents the minimal public SDK from `codex_app_server` and key error types from `codex_app_server.errors`.

## Minimal surface (`codex_app_server`)

```python
from codex_app_server import (
    Codex,
    Thread,
    Turn,
    TurnResult,
    InitializeResult,
    TextInput,
    ImageInput,
    LocalImageInput,
    SkillInput,
    MentionInput,
    Input,
    InputItem,
)
```

### `Codex`

```python
class Codex:
    def __init__(self, config: AppServerConfig | None = None) -> None
    @property
    def metadata(self) -> InitializeResult
    def close(self) -> None

    def thread_start(
        *,
        approval_policy: str | None = None,
        base_instructions: str | None = None,
        config: dict[str, Any] | None = None,
        cwd: str | None = None,
        developer_instructions: str | None = None,
        ephemeral: bool | None = None,
        model: str | None = None,
        model_provider: str | None = None,
        personality: Any | None = None,
        sandbox: Any | None = None,
    ) -> Thread

    def thread(self, thread_id: str) -> Thread

    def thread_resume(
        thread_id: str,
        *,
        approval_policy: str | None = None,
        base_instructions: str | None = None,
        config: dict[str, Any] | None = None,
        cwd: str | None = None,
        developer_instructions: str | None = None,
        model: str | None = None,
        model_provider: str | None = None,
        personality: Any | None = None,
        sandbox: Any | None = None,
    ) -> Thread

    def thread_list(
        *,
        archived: bool | None = None,
        cursor: str | None = None,
        cwd: str | None = None,
        limit: int | None = None,
        model_providers: list[str] | None = None,
        sort_key: str | None = None,
        source_kinds: list[str] | None = None,
    ) -> ThreadListResponse

    def thread_read(self, thread_id: str, *, include_turns: bool = False) -> ThreadReadResponse

    def thread_fork(
        thread_id: str,
        *,
        approval_policy: str | None = None,
        base_instructions: str | None = None,
        config: dict[str, Any] | None = None,
        cwd: str | None = None,
        developer_instructions: str | None = None,
        model: str | None = None,
        model_provider: str | None = None,
        sandbox: Any | None = None,
    ) -> Thread

    def thread_archive(self, thread_id: str) -> None
    def thread_unarchive(self, thread_id: str) -> Thread
    def thread_set_name(self, thread_id: str, name: str) -> None
    def thread_compact(self, thread_id: str) -> ThreadCompactStartResponse

    def turn_steer(self, thread_id: str, expected_turn_id: str, input: Input) -> TurnSteerResponse
    def turn_interrupt(self, thread_id: str, turn_id: str) -> None

    def models(self, *, include_hidden: bool = False) -> ModelListResponse
```

Behavior notes:

- Constructor is eager: starts transport and sends `initialize` immediately.
- `metadata` contains parsed `serverInfo` from `initialize`.
- Methods returning `Thread` expect the server response to contain `thread.id` and raise `ValueError` if missing.
- `thread_*`/`turn_*` methods validate payloads using generated v2 params models before RPC.

### `Thread`

```python
@dataclass(slots=True)
class Thread:
    id: str
    def turn(self, input: Input) -> Turn
```

Behavior notes:

- `turn(...)` calls `turn/start` and returns a `Turn` bound to `thread_id` and the created `turn.id`.

### `Turn`

```python
@dataclass(slots=True)
class Turn:
    thread_id: str
    id: str
    def stream(self) -> Iterator[Notification]
    def run(self) -> TurnResult
```

Behavior notes:

- `stream()` yields raw notifications until matching `turn/completed`.
- `run()` collects:
- text deltas from `item/agentMessage/delta`
- usage from `thread/tokenUsageUpdated` for this turn
- completion payload from `turn/completed`
- `run()` raises `RuntimeError` if completion is never received.

### `TurnResult`

```python
@dataclass(slots=True)
class TurnResult:
    thread_id: str
    turn_id: str
    status: str
    error: Any | None
    text: str
    items: list[ThreadItem]
    usage: ThreadTokenUsageUpdatedNotification | None = None
```

### Inputs

```python
@dataclass(slots=True)
class TextInput:
    text: str

@dataclass(slots=True)
class ImageInput:
    url: str

@dataclass(slots=True)
class LocalImageInput:
    path: str

@dataclass(slots=True)
class SkillInput:
    name: str
    path: str

@dataclass(slots=True)
class MentionInput:
    name: str
    path: str

InputItem = TextInput | ImageInput | LocalImageInput | SkillInput | MentionInput
Input = list[InputItem] | InputItem
```

Wire mapping:

- `TextInput` -> `{"type": "text", "text": ...}`
- `ImageInput` -> `{"type": "image", "url": ...}`
- `LocalImageInput` -> `{"type": "localImage", "path": ...}`
- `SkillInput` -> `{"type": "skill", "name": ..., "path": ...}`
- `MentionInput` -> `{"type": "mention", "name": ..., "path": ...}`

### `InitializeResult`

```python
@dataclass(slots=True)
class InitializeResult:
    server_name: str | None = None
    server_version: str | None = None
```

## Key exceptions (`codex_app_server.errors`)

```python
from codex_app_server.errors import (
    AppServerError,
    TransportClosedError,
    JsonRpcError,
    AppServerRpcError,
    ParseError,
    InvalidRequestError,
    MethodNotFoundError,
    InvalidParamsError,
    InternalRpcError,
    ServerBusyError,
    RetryLimitExceededError,
)
```

- `JsonRpcError`: has `.code`, `.message`, `.data`
- `ServerBusyError`: retryable overload condition
- `RetryLimitExceededError`: retryable category where server indicates retry budget exhaustion
- `TransportClosedError`: app-server stdio transport closed unexpectedly

Also available:

- `retry_on_overload(...)` in `codex_app_server.retry`
- `AppServerClient.request_with_retry_on_overload(...)`
