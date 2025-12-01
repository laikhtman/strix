# LLM Configuration

Core files: `llm/config.py`, `llm/llm.py`, `llm/request_queue.py`, `llm/memory_compressor.py`, `llm/utils.py`.

## Providers and models
- `LLMConfig` defines provider/model id (e.g., `openai/gpt-5`) and auth.
- Extend providers by adding client setup and request paths in `llm/llm.py`; expose config knobs in `config.py`.

## Request handling
- Requests queued via `request_queue.py` to manage concurrency and order.
- Retries/backoff handled in `llm.py` using tenacity; errors wrapped in `LLMRequestFailedError`.
- Streaming support depends on provider implementation in `llm.py`.

## Context management
- `memory_compressor.py` trims conversation/state to fit provider token limits.
- `llm/utils.py` cleans content before sending to providers.

## Tuning
- Control parallelism and rate limits in request queue.
- Adjust model choice to balance cost vs. latency.
- Customize temperature/other params in `LLMConfig`.

## Telemetry
- LLM calls can be logged via tracer; ensure sensitive data is redacted before emission.

## Adding a new provider
1) Define config fields in `config.py`.
2) Add client creation and request method in `llm.py`.
3) Wire retries/backoff and error normalization.
4) Update docs and examples in `setup-and-running.md`.

## Maintenance
- Revise when providers/models or retry/queue logic change; ensure env var expectations are documented.
