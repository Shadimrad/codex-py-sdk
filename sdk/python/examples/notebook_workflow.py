"""Notebook-style SDK workflow demo.

Run this as a normal script, or copy cells into Jupyter/VSCode notebooks.
Uses the fake app server so it is deterministic and test-friendly.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from codex_app_server import AppServerClient, AppServerConfig, AsyncAppServerClient


HERE = Path(__file__).resolve().parent
FAKE_SERVER = HERE.parent / "tests" / "fake_app_server.py"
CFG = AppServerConfig(launch_args_override=("python3", str(FAKE_SERVER)))


# %% Client start + initialize
with AppServerClient(CFG) as client:
    init = client.initialize()
    print("server:", init["serverInfo"]["name"])

    # %% thread_start_session + turn_text
    thread = client.thread_start_session(model="gpt-5")
    turn = thread.turn_text("Say hello in two words")
    done = client.wait_for_turn_completed(turn["turn"]["id"])
    print("turn status:", done.params["turn"]["status"])

    # %% ask helper (old tuple API)
    thread_id, answer = client.ask("Summarize: rain is wet.", thread_id=thread.thread_id)
    print("ask tuple:", thread_id, answer)

    # %% ask_result helper (new ergonomic API)
    ask_result = thread.ask_result("Name two colors")
    print("ask_result:", ask_result.thread_id, ask_result.text)

    # %% stream raw notifications
    print("raw stream methods:", [evt.method for evt in thread.stream("stream me")])

    # %% stream_text helper (new ergonomic API)
    print("stream_text chunks:", list(thread.stream_text("stream text")))

    # %% typed + schema wrappers
    typed = thread.turn_text_typed("typed please")
    _ = client.wait_for_turn_completed(typed.turn.id)
    schema = thread.turn_text_schema("schema please")
    _ = client.wait_for_turn_completed(schema.turn.id)
    print("typed turn:", typed.turn.id, "schema turn:", schema.turn.id)


# %% async usage
async def async_demo() -> None:
    async with AsyncAppServerClient(CFG) as client:
        await client.initialize()
        thread = await client.thread_start_session(model="gpt-5")

        text = await thread.ask("async ask")
        print("async ask:", text)

        ask_result = await thread.ask_result("async ask_result")
        print("async ask_result:", ask_result.text)

        chunks = [chunk async for chunk in thread.stream_text("async stream text")]
        print("async stream_text chunks:", chunks)


if __name__ == "__main__":
    asyncio.run(async_demo())
