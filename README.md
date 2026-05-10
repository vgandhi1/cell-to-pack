<div align="center">

# Cell-to-Pack Vision Orchestrator

### Advanced ML & AI engineering for EV battery assembly

**Industry reference stack:** edge **2.5D fusion** → **VLM-style inference** (mock or production) → **PLC halt** + **MES audit trail** — with latency budgets and fail-safe policies you can take to the plant floor.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge)](LICENSE)

<br />

| Domain | Stack highlights |
|:------:|------------------|
| **Computer vision & multimodal** | Fused optical + depth payload; swap mock heuristics for **Qwen-VL / LLaVA** behind **vLLM / Triton** |
| **Factory integration** | Modbus TCP PLC stub, JSON Lines MES log, stdio-safe defaults |
| **Systems** | Sub-500 ms client timeout, transport failure → **critical + halt** (demo policy) |

<br />

*Product & systems design:* [`docs/plan/plan.md`](docs/plan/plan.md) · [`docs/architecture/architecture.md`](docs/architecture/architecture.md)

</div>

---

## Table of contents

- [Why this exists](#why-this-exists)
- [Architecture](#architecture)
- [Features](#features)
- [MLOps & production path](#mlops--production-path)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Project layout](#project-layout)
- [Tests & quality](#tests--quality)
- [Replacing the mock VLM](#replacing-the-mock-vlm)
- [License](#license)

---

## Why this exists

Manufacturing and ML teams need a **repeatable integration pattern** before Jetson hardware and plant networks are fully wired. This repository implements **Phase 0** of the product plan: a **fully runnable** pipeline that mirrors a three-layer architecture so you can validate **latency**, **JSON contracts**, and **factory hooks** on a laptop — then promote the same boundaries to **gRPC/MQTT**, **GPU inference servers**, and real **PLC/MES** endpoints.

---

## Architecture

```mermaid
flowchart LR
  subgraph Edge["Edge (simulated)"]
    A[Optical + depth] --> B[Fused RGB | depth]
  end
  subgraph Brain["Inference"]
    B --> C["POST /v1/analyze"]
    C --> D[VLM or mock heuristics]
  end
  subgraph Factory["Factory integration"]
    D -->|defect| E[PLC halt signal]
    D --> F[MES JSONL audit]
  end
```

---

## Features

| Capability | Description |
|------------|-------------|
| **2.5D fusion** | Side-by-side **optical BGR** and **depth colormap** for a bandwidth-friendly multimodal payload |
| **HTTP inference API** | `POST /v1/analyze` — production may use **gRPC/MQTT** on the plant network |
| **JSON contract** | `defect_found`, `reason`, `severity` — stable for PLC/MES consumers |
| **PLC stub** | Default **stdio** halt line; optional **Modbus TCP** with bundled simulator |
| **MES stub** | Append-only **`var/mes_audit.jsonl`** audit trail |
| **Fail-safe path** | Remote inference errors → **critical** verdict + halt (configurable demo policy) |

---

## MLOps & production path

This repo is a **reference implementation**; the table below maps what you get today to a typical **MLOps** rollout for vision + factory systems.

| Concern | In this repo | Typical next steps (industry) |
|---------|--------------|------------------------------|
| **Model serving** | FastAPI handler + mock VLM | **Triton Inference Server** or **vLLM** for quantized VLMs; gRPC/HTTP behind an API gateway |
| **Schema & contracts** | Pydantic `VLMVerdict` | Version the JSON schema; contract tests in CI; reject unknown model outputs at the edge |
| **Data & labels** | Synthetic / sample assets | Curated image store + label workflow; **train/val/test** splits aligned with line variants |
| **CI/CD** | `pytest`, `ruff` (dev extras) | Pipeline: lint → unit tests → **container build** → deploy to staging cell; smoke `POST /v1/analyze` |
| **Observability** | Structured logs via app | Request IDs, latency histograms, defect rate dashboards; **no PII/secrets** in client-visible errors |
| **Governance** | MES JSONL append-only log | Retention policy, immutable audit store, correlation with pack serial / work order (your IDs) |

Treat **timeout + fail-safe halt** as part of the **serving SLO**: the orchestrator already encodes a strict client timeout (`CTP_REQUEST_TIMEOUT_S`) suitable for discussing real-time line-stop policies with controls engineers.

---

## Quick start

### 1. Install

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Run one end-to-end cycle (local inference)

```bash
# Good pack → no defect, audit row still written
cell-to-pack run --good

# Bad pack → defect, PLC_HALT on stdout, exit code 2
cell-to-pack run --bad
```

Audit log: `var/mes_audit.jsonl` · Fused image: `assets/samples/<pack-id>_fused.png` (skip with `--no-save`).

### 3. Run with the HTTP server (remote inference path)

**Terminal A — API**

```bash
cell-to-pack serve
```

**Terminal B — orchestrator calling the API**

```bash
cell-to-pack run --good --remote http://127.0.0.1:8765
```

### 4. Optional: Modbus TCP PLC simulator

**Terminal A**

```bash
python scripts/run_modbus_plc_sim.py --port 5020
```

**Terminal B**

```bash
cell-to-pack run --bad --plc-modbus --plc-host 127.0.0.1 --plc-port 5020
```

---

## Configuration

Environment variables use the **`CTP_`** prefix (see `cell_to_pack.config.Settings`):

| Variable | Default | Meaning |
|----------|---------|---------|
| `CTP_INFERENCE_HOST` | `127.0.0.1` | API bind address |
| `CTP_INFERENCE_PORT` | `8765` | API port |
| `CTP_REQUEST_TIMEOUT_S` | `0.45` | Client timeout (**450 ms** production budget) |
| `CTP_MES_LOG_PATH` | `var/mes_audit.jsonl` | MES JSONL path |
| `CTP_PLC_MODE` | `stdio` | `stdio` or `modbus` |
| `CTP_PLC_HOST` / `CTP_PLC_PORT` | `127.0.0.1` / `5020` | Modbus target |

---

## Project layout

```
cell-to-pack/
├── src/cell_to_pack/       # Application package
│   ├── edge/               # Fusion + synthetic scenes
│   ├── inference/          # Mock VLM + FastAPI server
│   ├── factory/            # PLC + MES stubs
│   ├── orchestrator.py     # End-to-end wiring
│   └── cli.py              # `serve` / `run` commands
├── scripts/run_modbus_plc_sim.py
├── tests/
├── docs/
│   ├── plan/plan.md
│   └── architecture/architecture.md
└── README.md
```

---

## Tests & quality

```bash
pytest -q
ruff check src tests
```

---

## Replacing the mock VLM

`cell_to_pack.inference.vlm.analyze_fused_bgr` is intentionally small: OpenCV heuristics stand in for **Qwen-VL / LLaVA** behind **vLLM / Triton**. For production:

1. Keep the **`VLMVerdict`** schema stable for PLC/MES consumers.
2. Implement your model server and either call it from `analyze_fused_bgr` or swap the FastAPI handler body.
3. Enforce the **edge timeout** and fail-safe halt policy from the product plan.

---

## License

MIT — see `LICENSE` if present in your fork.

---

<div align="center">

**Advanced machine learning & AI engineering for manufacturing — vision, contracts, and factory integration in one loop.**

</div>
