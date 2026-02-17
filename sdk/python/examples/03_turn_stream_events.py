from codex_app_server import Codex


with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")
    turn = thread.turn("Write a short haiku about compilers.")

    for event in turn.stream():
        print(event.method, event.params)
