# Codex App Server Python SDK

Python SDK for `codex app-server` JSON-RPC v2 over stdio, with a small default surface optimized for real scripts and apps.

## Install

```bash
cd sdk/python
python -m pip install -e .
```

## Quickstart

```python
from codex_app_server import Codex, TextInput

with Codex() as codex:
    thread = codex.thread_start(model="gpt-5")
    result = thread.turn(TextInput("Say hello in one sentence.")).run()
    print(result.text)
```

## Docs map

- Golden path tutorial: `docs/getting-started.md`
- API reference (signatures + behavior): `docs/api-reference.md`
- Common decisions and pitfalls: `docs/faq.md`
- Runnable examples index: `examples/README.md`
- Jupyter walkthrough notebook: `notebooks/sdk_walkthrough.ipynb`

## Examples

Start here:

```bash
cd sdk/python
python examples/01_quickstart_constructor/sync.py
python examples/01_quickstart_constructor/async.py
```

## Pinned release binary workflow

Use this script to pin the SDK to the latest release binary (stable or alpha) and regenerate types:

```bash
cd sdk/python
python scripts/update_codex_binary_and_types.py --channel stable
# or
python scripts/update_codex_binary_and_types.py --channel alpha
```

What it does:

- downloads latest release `codex` binary for current OS/arch into `sdk/python/bin/codex`
- regenerates protocol-derived Python types

Runtime binary precedence:

1. `CODEX_APP_SERVER_BIN` env var (if set)
2. pinned `sdk/python/bin/codex` (if present)
3. `codex` from `PATH`

## Compatibility and versioning

- Package: `codex-app-server-sdk`
- Current SDK version in this repo: `0.2.0`
- Python: `>=3.10`
- Target protocol: Codex `app-server` JSON-RPC v2
- Recommendation: keep SDK and `codex` CLI reasonably up to date together

## Notes

- `Codex()` is eager and performs startup + `initialize` in the constructor.
- Use context managers (`with Codex() as codex:`) to ensure shutdown.
- For transient overload, use `codex_app_server.retry.retry_on_overload`.
