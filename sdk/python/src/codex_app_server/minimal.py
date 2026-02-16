from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator

from .client import AppServerClient, AppServerConfig

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

    def turn(self, input: Input, **opts: Any) -> dict[str, Any]:
        return self._client.turn_start(self.id, input, **opts)

    def run(self, input: Input, **opts: Any) -> str:
        chunks = [chunk for chunk in self.stream(input, **opts)]
        return "".join(chunks)

    def stream(self, input: Input, **opts: Any) -> Iterator[str]:
        turn = self.turn(input, **opts)
        turn_id = turn["turn"]["id"]
        while True:
            event = self._client.next_notification()
            if event.method == "item/agentMessage/delta":
                yield (event.params or {}).get("delta", "")
            if event.method == "turn/completed" and (event.params or {}).get("turn", {}).get("id") == turn_id:
                break
