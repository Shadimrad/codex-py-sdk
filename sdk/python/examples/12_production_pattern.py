from __future__ import annotations

from codex_app_server import Codex, TextInput
from codex_app_server.errors import (
    InvalidParamsError,
    JsonRpcError,
    MethodNotFoundError,
    ServerBusyError,
    TransportClosedError,
)
from codex_app_server.retry import retry_on_overload


PROMPT = "you> "
EXIT_COMMANDS = {"/exit", "/quit"}


def main() -> None:
    print("Codex production pattern demo. Type /exit to quit.")

    try:
        with Codex() as codex:
            thread = retry_on_overload(
                lambda: codex.thread_start(model="gpt-5"),
                max_attempts=3,
                initial_delay_s=0.25,
                max_delay_s=2.0,
            )
            print("Thread:", thread.id)

            while True:
                try:
                    user_input = input(PROMPT).strip()
                except EOFError:
                    print("EOF received, shutting down.")
                    break

                if not user_input:
                    continue
                if user_input in EXIT_COMMANDS:
                    print("Exit command received, shutting down.")
                    break

                try:
                    result = retry_on_overload(
                        lambda: thread.turn(TextInput(user_input)).run(),
                        max_attempts=4,
                        initial_delay_s=0.25,
                        max_delay_s=3.0,
                    )
                except ServerBusyError as exc:
                    print("assistant> [busy]", exc.message)
                    continue
                except InvalidParamsError as exc:
                    print("assistant> [invalid params]", exc.message)
                    continue
                except MethodNotFoundError as exc:
                    print("assistant> [method not found]", exc.message)
                    continue
                except TransportClosedError:
                    print("assistant> [transport closed] app-server stopped unexpectedly.")
                    break
                except JsonRpcError as exc:
                    print(f"assistant> [rpc error {exc.code}] {exc.message}")
                    continue

                if result.status == "failed":
                    print("assistant> [turn failed]", result.error)
                    continue

                print("assistant>", result.text.strip())

    except KeyboardInterrupt:
        print("Interrupted, shutting down.")


if __name__ == "__main__":
    main()
