from codex_app_server import Codex, TextInput, LocalImageInput


with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")

    result = thread.turn([
        TextInput("Read this local image and summarize what you see."),
        LocalImageInput("./image.png"),  # replace with a real local path
    ]).run()

    print(result.status)
    print(result.text)
