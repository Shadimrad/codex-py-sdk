from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from .client import AppServerClient, AppServerConfig
from .models import Notification
from .schema_types import TurnCompletedNotificationPayload, ThreadTokenUsageUpdatedNotificationPayload


@dataclass(slots=True)
class TurnResult:
    _completed: TurnCompletedNotificationPayload
    _usage: ThreadTokenUsageUpdatedNotificationPayload | None = None
    _text: str = ""

    def turn(self) -> Any:
        return self._completed.turn

    def turn_id(self) -> str:
        return self._completed.turn.id

    def status(self) -> str:
        return self._completed.turn.status

    def error(self) -> Any | None:
        return self._completed.turn.error

    def usage(self) -> ThreadTokenUsageUpdatedNotificationPayload | None:
        return self._usage

    def text(self) -> str:
        return self._text

    def items(self) -> list[Any]:
        return self._completed.turn.items

Input = list[dict[str, Any]] | dict[str, Any] | str


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

        return TurnResult(
            _completed=TurnCompletedNotificationPayload.from_dict(completed_payload),
            _usage=usage,
            _text="".join(chunks),
        )
