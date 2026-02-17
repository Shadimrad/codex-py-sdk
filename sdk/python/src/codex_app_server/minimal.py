from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Literal, TypedDict

from .client import AppServerClient, AppServerConfig
from .models import Notification
from .generated.v2_types import (
    ModelListResponse,
    ThreadReadResponse,
    ThreadListResponse,
    ThreadCompactStartResponse,
    TurnSteerResponse,
    TurnCompletedNotificationPayload,
    ThreadTokenUsageUpdatedNotification,
    ThreadItem,
)


@dataclass(slots=True)
class TurnResult:
    thread_id: str
    turn_id: str
    status: str
    error: Any | None
    text: str
    items: list[ThreadItem]
    usage: ThreadTokenUsageUpdatedNotification | None = None

class TextInput(TypedDict):
    type: Literal["text"]
    text: str


class ImageInput(TypedDict):
    type: Literal["image"]
    url: str


class LocalImageInput(TypedDict):
    type: Literal["localImage"]
    path: str


class SkillInput(TypedDict):
    type: Literal["skill"]
    name: str
    path: str


class MentionInput(TypedDict):
    type: Literal["mention"]
    name: str
    path: str


InputItem = TextInput | ImageInput | LocalImageInput | SkillInput | MentionInput
Input = list[InputItem] | InputItem | str


@dataclass(slots=True)
class InitializeResult:
    server_name: str | None = None
    server_version: str | None = None


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
        if not isinstance(payload, dict):
            raise TypeError("initialize response must be a dict")
        server = payload.get("serverInfo")
        if not isinstance(server, dict):
            raise ValueError("initialize response missing serverInfo")
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

    def thread_resume(self, thread_id: str, **opts: Any) -> Thread:
        resumed = self._client.thread_resume(thread_id, **opts)
        tid = (resumed.get("thread") or {}).get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError("thread/resume response missing thread.id")
        return Thread(self._client, tid)

    def thread_list(self, **opts: Any) -> ThreadListResponse:
        result = self._client.thread_list(**opts)
        if not isinstance(result, dict):
            raise TypeError("thread/list response must be a dict")
        return ThreadListResponse.model_validate(result)

    def thread_read(self, thread_id: str, *, include_turns: bool = False) -> ThreadReadResponse:
        result = self._client.thread_read(thread_id, include_turns=include_turns)
        if not isinstance(result, dict):
            raise TypeError("thread/read response must be a dict")
        return ThreadReadResponse.model_validate(result)

    def thread_fork(self, thread_id: str, **opts: Any) -> Thread:
        forked = self._client.thread_fork(thread_id, **opts)
        tid = (forked.get("thread") or {}).get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError("thread/fork response missing thread.id")
        return Thread(self._client, tid)

    def thread_archive(self, thread_id: str) -> None:
        self._client.thread_archive(thread_id)

    def thread_unarchive(self, thread_id: str) -> Thread:
        unarchived = self._client.thread_unarchive(thread_id)
        tid = (unarchived.get("thread") or {}).get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError("thread/unarchive response missing thread.id")
        return Thread(self._client, tid)

    def thread_set_name(self, thread_id: str, name: str) -> None:
        self._client.thread_set_name(thread_id, name)

    def thread_compact(self, thread_id: str) -> ThreadCompactStartResponse:
        result = self._client.request("thread/compact", {"threadId": thread_id})
        if not isinstance(result, dict):
            raise TypeError("thread/compact response must be a dict")
        return ThreadCompactStartResponse.model_validate(result)

    def turn_steer(self, thread_id: str, expected_turn_id: str, input: Input) -> TurnSteerResponse:
        result = self._client.turn_steer(thread_id, expected_turn_id, input)
        if not isinstance(result, dict):
            raise TypeError("turn/steer response must be a dict")
        return TurnSteerResponse.model_validate(result)

    def turn_interrupt(self, thread_id: str, turn_id: str) -> None:
        self._client.turn_interrupt(thread_id, turn_id)

    def models(self, *, include_hidden: bool = False) -> ModelListResponse:
        result = self._client.model_list(include_hidden=include_hidden)
        if not isinstance(result, dict):
            raise TypeError("model/list response must be a dict")
        return ModelListResponse.model_validate(result)


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
        usage: ThreadTokenUsageUpdatedNotification | None = None
        chunks: list[str] = []

        for event in self.stream():
            if event.method == "item/agentMessage/delta":
                chunks.append((event.params or {}).get("delta", ""))
            elif event.method == "thread/tokenUsageUpdated":
                params = event.params or {}
                if params.get("turnId") == self.id:
                    usage = ThreadTokenUsageUpdatedNotification.model_validate(params)
            elif event.method == "turn/completed" and (event.params or {}).get("turn", {}).get("id") == self.id:
                completed_payload = event.params or {}

        if completed_payload is None:
            raise RuntimeError("turn completed event not received")

        completed = TurnCompletedNotificationPayload.model_validate(completed_payload)
        status = completed.turn.status
        status_str = status.value if hasattr(status, "value") else str(status)
        return TurnResult(
            thread_id=completed.threadId,
            turn_id=completed.turn.id,
            status=status_str,
            error=completed.turn.error,
            text="".join(chunks),
            items=list(completed.turn.items or []),
            usage=usage,
        )
