import asyncio

from codex_app_server.async_client import AsyncAppServerClient


async def main() -> None:
    async with AsyncAppServerClient() as client:
        metadata = await client.initialize()
        server = metadata.get("serverInfo", {})
        print("Server:", server.get("name"), server.get("version"))

        started = await client.thread_start(model="gpt-5")
        thread_id = started["thread"]["id"]

        turn = await client.turn_text(thread_id, "Say hello in one sentence.")
        turn_id = turn["turn"]["id"]

        chunks: list[str] = []
        async for event in _stream_turn(client, turn_id):
            if event.method == "item/agentMessage/delta":
                chunks.append((event.params or {}).get("delta", ""))

        print("Thread:", thread_id)
        print("Turn:", turn_id)
        print("Text:", "".join(chunks).strip())


async def _stream_turn(client: AsyncAppServerClient, turn_id: str):
    while True:
        event = await client.next_notification()
        yield event
        if event.method == "turn/completed" and (event.params or {}).get("turn", {}).get("id") == turn_id:
            break


if __name__ == "__main__":
    asyncio.run(main())
