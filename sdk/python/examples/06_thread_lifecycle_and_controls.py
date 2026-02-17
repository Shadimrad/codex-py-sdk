from codex_app_server import Codex, TextInput


with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")

    # Thread lifecycle
    _ = codex.thread_list(limit=20)
    _ = codex.thread_read(thread.id, include_turns=True)
    forked = codex.thread_fork(thread.id)
    codex.thread_set_name(thread.id, "Renamed Thread")
    codex.thread_archive(thread.id)
    thread = codex.thread_unarchive(thread.id)
    _ = codex.thread_compact(thread.id)

    # Turn controls
    turn = thread.turn(TextInput("Start a task")).run()
    _ = codex.turn_steer(thread.id, turn.turn_id, TextInput("Continue with this adjustment"))
    codex.turn_interrupt(thread.id, turn.turn_id)

    print("Forked thread:", forked.id)
