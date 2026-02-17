from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from .client import AppServerClient, AppServerConfig
from .models import Notification
from .generated.schema_types import TurnCompletedNotificationPayload, ThreadTokenUsageUpdatedNotificationPayload


@dataclass(slots=True)
class TurnResult:
    thread_id: str
    turn_id: str
    status: str
    error: Any | None
    text: str
    items: list[Any]
    usage: ThreadTokenUsageUpdatedNotificationPayload | None = None

Input = list[dict[str, Any]] | dict[str, Any] | str


@dataclass(slots=True)
class InitializeResult:
    server_name: str | None = None
    server_version: str | None = None


@dataclass(slots=True)
class Model:
    id: str
    name: str | None = None


class Codex:
    """Minimal public SDK surface for app-server v2.

    Constructor is eager: it starts and initializes the app-server immediately.
    Errors are raised directly from constructor for Pythonic fail-fast behavior.
    """

    def __init__(self, config: AppServerConfig | None = None) -> None:
        self._client = AppServerClient(config=config)
        self._client.start()
        self._init = self._parse_initialize(self._client.initialize())

    def __enter__(self) -> "Codex":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    @staticmethod
    def _parse_initialize(payload: dict[str, Any]) -> InitializeResult:
        server = payload.get("serverInfo") if isinstance(payload, dict) else None
        if not isinstance(server, dict):
            return InitializeResult()
        return InitializeResult(
            server_name=server.get("name"),
            server_version=server.get("version"),
        )

    @property
    def metadata(self) -> InitializeResult:
        """Startup metadata captured during construction."""
        return self._init

    def close(self) -> None:
        self._client.close()

    def thread_start(self, *, model: str | None = None, **opts: Any) -> Thread:
        payload = dict(opts)
        if model is not None:
            payload["model"] = model
        started = self._client.thread_start(**payload)
        return Thread(self._client, started["thread"]["id"])

    def thread(self, thread_id: str) -> Thread:
        return Thread(self._client, thread_id)

    def models(self, *, include_hidden: bool = False) -> list[Model]:
        result = self._client.model_list(include_hidden=include_hidden)
        raw_models = result.get("models") or result.get("data") or []
        out: list[Model] = []
        for m in raw_models:
            if isinstance(m, dict):
                out.append(Model(id=str(m.get("id", "")), name=m.get("name")))
        return out


@dataclass(slots=True)
class Thread:
    _client: AppServerClient
    id: str

    def turn(self, input: Input, **opts: Any) -> Turn:
        turn = self._client.turn_start(self.id, input, **opts)
        return Turn(self._client, self.id, turn["turn"]["id"])


@dataclass(slots=True)
class Turn:
    _client: AppServerClient
    thread_id: str
    id: str

    def stream(self) -> Iterator[Notification]:
        """Yield all notifications for this turn until turn/completed."""
        while True:
            event = self._client.next_notification()
            yield event
            if event.method == "turn/completed" and (event.params or {}).get("turn", {}).get("id") == self.id:
                break

    def run(self) -> TurnResult:
        """Consume turn events and return typed `TurnResult` (completed + usage + text)."""
        completed_payload: dict[str, Any] | None = None
        usage: ThreadTokenUsageUpdatedNotificationPayload | None = None
        chunks: list[str] = []

        for event in self.stream():
            if event.method == "item/agentMessage/delta":
                chunks.append((event.params or {}).get("delta", ""))
            elif event.method == "thread/tokenUsageUpdated":
                params = event.params or {}
                if params.get("turnId") == self.id:
                    usage = ThreadTokenUsageUpdatedNotificationPayload.from_dict(params)
            elif event.method == "turn/completed" and (event.params or {}).get("turn", {}).get("id") == self.id:
                completed_payload = event.params or {}

        if completed_payload is None:
            raise RuntimeError("turn completed event not received")

        completed = TurnCompletedNotificationPayload.from_dict(completed_payload)
        return TurnResult(
            thread_id=completed.threadId,
            turn_id=completed.turn.id,
            status=completed.turn.status,
            error=completed.turn.error,
            text="".join(chunks),
            items=list(completed.turn.items or []),
            usage=usage,
        )
