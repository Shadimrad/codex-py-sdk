from codex_app_server import Codex


EXISTING_THREAD_ID = "thr_123"  # replace with a real thread id

with Codex() as codex:
    thread = codex.thread(EXISTING_THREAD_ID)
    result = thread.turn("Continue from where we left off.").run()
    print(result.text)
