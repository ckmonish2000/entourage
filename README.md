# Entourage

<p align="center">
  <img src="https://github.com/ckmonish2000/entourage/blob/main/assets/entourage_logo.png" alt="entourage Logo" width="250">
</p>

**An open-source multi-agent orchestrator for autonomous coding tasks**

Entourage is a transparent, interactive coding assistant that solves complex software engineering problems through multi-agent orchestration — think of it as an open-source alternative to Warp's Oz.

## What makes Entourage different

### 🤖 Multi-Agent Orchestration
Instead of a single monolithic AI, Entourage coordinates multiple specialized agents that collaborate to solve coding problems. Each agent focuses on specific tasks (analysis, implementation, testing, refactoring) and works together systematically.

### 👁️ Real-Time Transparency
Watch every decision unfold on an interactive dashboard. See what the agents are thinking, which tools they're using, and how they're approaching your problem — all in real-time.

### 🎯 Human-in-the-Loop Control
Step in anytime to guide the agents if they're going off track. Provide feedback, redirect efforts, or approve critical decisions before they execute.

### 🔒 Sandboxed Execution
All code runs in isolated environments (Docker/Firecracker), so experimentation is safe by default. No risk to your local system.

## Core Features

- **Multi-agent collaboration** — Specialized agents working together on complex tasks
- **Live decision tracking** — Real-time dashboard showing agent reasoning and actions
- **Interactive intervention** — Guide agents mid-execution to stay on track
- **Safe execution** — Sandboxed environments prevent unintended consequences
- **Tool-use transparency** — See exactly which tools and APIs agents invoke
- **Progressive enhancement** — Agents learn from corrections and adapt

## Architecture

```
User Request
    ↓
Orchestrator (coordinates agent workflow)
    ↓
┌─────────────┬──────────────┬─────────────┬──────────────┐
│  Analyzer   │ Implementer  │   Tester    │  Refactorer  │
│   Agent     │    Agent     │    Agent    │    Agent     │
└─────────────┴──────────────┴─────────────┴──────────────┘
    ↓
Sandbox Environment (Docker/Firecracker)
    ↓
Execution Results + Decision Log
```

## Sandbox Strategy

Entourage progressively hardens execution environments:

1. **subprocess** — Local process isolation (development)
2. **Docker** — Containerized execution (current)
3. **Firecracker** — Lightweight microVM sandboxes (planned)

## Interfaces

- **CLI** — Terminal-based interaction for quick requests
- **API** — HTTP server for programmatic access and integration
- **Dashboard** — Real-time web UI for monitoring agent decisions

## Getting Started

```bash
# Requires Python 3.14+
git clone https://github.com/yourusername/entourage
cd entourage
pip install -e .

# Start the orchestrator
python main.py

# Or run via API server
python api.py
```

## Example Usage

```bash
# CLI mode
entourage "Refactor the authentication module to use JWT tokens"

# Watch agents:
# 1. Analyzer examines current auth implementation
# 2. Implementer proposes JWT integration strategy
# 3. You intervene: "Use the jose library, not pyjwt"
# 4. Implementer adapts and generates code
# 5. Tester creates test cases
# 6. Refactorer optimizes final implementation
```

## Why Open Source?

Warp's Oz is powerful but proprietary. Entourage brings similar multi-agent orchestration capabilities to the open-source community with full transparency:

- **See the reasoning** — No black box decisions
- **Control the process** — Intervene and guide at any point
- **Extend the system** — Add your own specialized agents
- **Own your data** — Everything runs locally or in your infrastructure

## Roadmap

- [x] Multi-agent orchestration framework
- [x] Real-time decision logging
- [x] Subprocess sandbox isolation
- [ ] Docker-based sandboxing
- [ ] Interactive web dashboard
- [ ] Human intervention checkpoints
- [ ] Firecracker microVM support
- [ ] Custom agent plugin system
- [ ] Multi-language support (beyond Python)
- [ ] Cloud deployment options

## Status

Early development — core orchestration and sandboxing functional, dashboard in progress.

