from codex_app_server import Codex, TextInput, ImageInput


with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")

    result = thread.turn([
        TextInput("What is in this image? Give 3 bullets."),
        ImageInput("https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg"),
    ]).run()

    print(result.status)
    print(result.text)
