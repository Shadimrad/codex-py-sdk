from __future__ import annotations

from pathlib import Path

from codex_app_server import Codex, AppServerConfig


HERE = Path(__file__).parent
FAKE = HERE / "fake_app_server.py"


def test_minimal_turn_run_and_stream() -> None:
    codex = Codex(AppServerConfig(launch_args_override=("python3", str(FAKE))))
    codex.start()
    codex.initialize()

    thread = codex.thread_start(model="gpt-5")

    result = thread.turn("hello").run()
    completed = result.completed()
    assert completed.turn.id
    assert completed.turn.status == "completed"
    assert isinstance(result.items(), list)
    assert result.text() == "hello world"
    # fake server emits token usage after turn/completed, so this may be None in this fixture
    usage = result.usage()
    assert (usage is None) or (usage.turnId == completed.turn.id)

    events = list(thread.turn("hello again").stream())
    assert any(e.method == "turn/completed" for e in events)

    codex.close()
