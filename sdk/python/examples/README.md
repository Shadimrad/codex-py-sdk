# Python SDK Examples

Scenario-based index for `sdk/python/examples`.

## Which example should I run first?

Run `01_quickstart_constructor.py` first. It verifies your environment and shows the shortest successful turn flow.

```bash
cd sdk/python
python examples/01_quickstart_constructor.py
```

## Core conversation flow

- `01_quickstart_constructor.py`
  - Use when: first run / sanity check
  - Expected outcome: prints server metadata, then a completed turn status and text
- `02_turn_run.py`
  - Use when: you need all `TurnResult` fields
  - Expected outcome: prints `thread_id`, `turn_id`, `status`, `error`, `text`, `items`, `usage`
- `03_turn_stream_events.py`
  - Use when: you need raw event stream handling
  - Expected outcome: prints notification methods/params until `turn/completed`

## Discovery and metadata

- `04_models_and_metadata.py`
  - Use when: you want startup metadata and available models
  - Expected outcome: prints metadata plus model count and first model id

## Working with existing threads

- `05_existing_thread.py`
  - Use when: continuing a previously saved `thread_id`
  - Expected outcome: appends one turn and prints assistant text
- `06_thread_lifecycle_and_controls.py`
  - Use when: testing lifecycle RPCs and turn controls
  - Expected outcome: exercises list/read/fork/archive/unarchive/setName/compact and steer/interrupt

## Multimodal input

- `07_image_and_text.py`
  - Use when: sending remote image URL + text in one turn
  - Expected outcome: prints completed status and image-grounded response text
- `08_local_image_and_text.py`
  - Use when: sending local image file + text
  - Expected outcome: prints completed status and response text (after replacing sample path)

## Async and integration patterns

- `09_async_parity.py`
  - Use when: integrating with asyncio code
  - Expected outcome: prints metadata, thread/turn IDs, and streamed response text
- `10_error_handling_and_retry.py`
  - Use when: adding typed error handling and overload retry backoff
  - Expected outcome: successful retried turn output plus handled JSON-RPC error example
- `11_cli_mini_app.py`
  - Use when: building a local interactive shell
  - Expected outcome: persistent multi-turn chat loop until `/exit`
- `12_production_pattern.py`
  - Use when: robust long-running loop with retry + graceful failures
  - Expected outcome: resilient interactive session with clean shutdown and categorized errors
