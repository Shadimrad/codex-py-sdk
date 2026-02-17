from __future__ import annotations

from pathlib import Path

from codex_app_server import Codex
from codex_app_server.client import AppServerConfig


HERE = Path(__file__).parent
FAKE = HERE / "fake_app_server.py"


def test_minimal_turn_run_and_stream() -> None:
    codex = Codex(AppServerConfig(launch_args_override=("python3", str(FAKE))))
    assert codex.metadata.server_name == "fake"

    thread = codex.thread_start(model="gpt-5")

    listed = codex.thread_list(limit=10)
    assert isinstance(listed.data, list)

    resumed = codex.thread_resume(thread.id)
    assert resumed.id == thread.id

    read = codex.thread_read(thread.id, include_turns=True)
    assert read.thread.id == thread.id

    forked = codex.thread_fork(thread.id)
    assert forked.id

    codex.thread_set_name(thread.id, "renamed")
    codex.thread_archive(thread.id)
    unarchived = codex.thread_unarchive(thread.id)
    assert unarchived.id == thread.id

    compacted = codex.thread_compact(thread.id)
    assert compacted is not None

    result = thread.turn("hello").run()
    assert result.turn_id
    assert result.status == "completed"
    assert isinstance(result.items, list)
    assert result.text == "hello world"
    # fake server emits token usage after turn/completed, so this may be None in this fixture
    usage = result.usage
    assert (usage is None) or (usage.turnId == result.turn_id)

    events = list(thread.turn("hello again").stream())
    assert any(e.method == "turn/completed" for e in events)

    started = thread.turn("steer me")
    steer = codex.turn_steer(thread.id, started.id, "next input")
    assert steer.turnId == started.id
    codex.turn_interrupt(thread.id, started.id)

    codex.close()
