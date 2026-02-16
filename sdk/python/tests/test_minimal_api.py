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
    assert result.text == "hello world"
    assert result.completed.method == "turn/completed"
    assert isinstance(result.items, list)

    events = list(thread.turn("hello again").stream())
    assert any(e.method == "turn/completed" for e in events)

    codex.close()
