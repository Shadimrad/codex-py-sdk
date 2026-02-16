from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from .client import AppServerClient, AppServerConfig
from .models import Notification
from .schema_types import TurnCompletedNotificationPayload, ThreadTokenUsageUpdatedNotificationPayload

Input = list[dict[str, Any]] | dict[str, Any] | str


@dataclass(slots=True)
class RunResult:
    text: str
    completed: TurnCompletedNotificationPayload
    usage: ThreadTokenUsageUpdatedNotificationPayload | None

    @property
    def items(self) -> list[Any]:
        return self.completed.turn.items


class Codex:
    """Minimal public SDK surface for app-server v2."""

    def __init__(self, config: AppServerConfig | None = None) -> None:
        self._client = AppServerClient(config=config)

    def start(self) -> None:
        self._client.start()

    def initialize(self) -> dict[str, Any]:
        return self._client.initialize()

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

    def models(self, *, include_hidden: bool = False) -> list[dict[str, Any]]:
        result = self._client.model_list(include_hidden=include_hidden)
        return result.get("models", [])


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

    def run(self) -> RunResult:
        """Consume the event stream and return typed completion + usage + assembled text."""
        chunks: list[str] = []
        completed_payload: dict[str, Any] | None = None
        usage: ThreadTokenUsageUpdatedNotificationPayload | None = None

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
        return RunResult(text="".join(chunks), completed=completed, usage=usage)
