# Entourage

A coding agent that executes user requests in a sandboxed environment.

## What it does

Entourage takes natural language coding requests, generates and runs code, and returns the result — all inside an isolated sandbox so execution is safe by default.

## Sandbox strategy

The project is designed to progressively harden the execution environment:

1. **subprocess** — local process isolation (current)
2. **Docker** — containerized execution
3. **E2B / Firecracker** — cloud microVM sandboxes

## Interfaces

- **CLI** — run requests directly from the terminal
- **API** — HTTP server for programmatic access

## Getting started

```bash
# Requires Python 3.14+
git clone <repo>
cd entourage
pip install -e .
python main.py
```

## Status

Early development.
