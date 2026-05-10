# System Architecture: EV Battery "Cell-to-Pack" Vision Orchestrator

## 1. High-Level System Overview
The architecture is divided into three distinct layers: the Edge Layer (Data Acquisition & Pre-processing), the Inference Layer (Reasoning & VLM), and the Factory Integration Layer (Control & Logging).

## 2. Layer 1: The Edge (Hardware & Pre-processing)
* **Hardware Setup:**
  * 1x NVIDIA Jetson Orin Nano Super.
  * 2x High-resolution optical cameras.
  * 1x Structured Light / Time-of-Flight 3D sensor.
* **Processing Pipeline:**
  * The Jetson module continuously ingests data from the cameras.
  * Standard 2D CV (OpenCV) is used to detect the "Step Complete" trigger (e.g., the robotic arm retracts after applying thermal paste).
  * Upon trigger, the Jetson takes a snapshot: a 2D optical frame and a 3D point cloud.
  * **Data Reduction:** To save bandwidth, the point cloud is flattened into a 2.5D depth map (a 2D image where pixel intensity represents depth). The optical and depth maps are **concatenated** (e.g., side-by-side RGB | depth colormap) into a single fused image payload for transport.

### 2.1 Reference Implementation (This Repository)
| Component | Production intent | Reference behavior |
|-----------|-------------------|----------------------|
| Cameras / ToF | Live sensors | Synthetic or file-based optical + depth frames (`cell_to_pack.edge.simulator`) |
| Trigger | CV step-complete | CLI flag or simulated `StepComplete` event |
| Fusion | Jetson pre-processing | `cell_to_pack.edge.fusion` builds the fused PNG |

## 3. Layer 2: The Brain (Inference & Reasoning)
* **Transport:** The Jetson sends the fused image payload via gRPC or MQTT to a centralized on-premise GPU cluster.
* **VLM Engine:**
  * Framework: vLLM or Triton Inference Server.
  * Model: An open-source multimodal model (e.g., Qwen-VL or LLaVA) heavily quantized for speed.
* **The Prompt:** "Analyze the attached depth map and optical image of a battery module. 1. Is the thermal paste (grey material) continuous along the heat sink? 2. Are all orange high-voltage busbars flush with the cell surface? Output your response as a JSON object containing `defect_found`: boolean, `reason`: string, `severity`: string."

### 3.1 Reference Implementation
* **Transport:** **HTTP/JSON** (`POST /v1/analyze`) for simple lab integration; gRPC/MQTT remain the plant-network targets.
* **Engine:** **Mock VLM** — OpenCV heuristics on optical + depth halves (thermal paste continuity proxy via depth variance; busbar proxy via HSV "orange" coverage). Swap for a real VLM by implementing the same JSON schema behind the API.
* **Contract:** Pydantic models in `cell_to_pack.schemas` (`VLMVerdict`).

## 4. Layer 3: Factory Integration (Control & Logging)
* **Robotic Control (PLC):** If the VLM outputs `'defect_found': true`, the central server instantly sends a Modbus TCP / OPC UA signal to the robotic cell's PLC.
  * The PLC immediately halts the line and illuminates the physical red Andon light.
* **Data Logging (MES/ERP):**
  * The VLM's JSON output, along with the fused image, is stored in the factory's Manufacturing Execution System (MES).
  * This creates a digital twin/audit trail for every battery pack produced.

### 4.1 Reference Implementation
* **PLC:** Optional **Modbus TCP** coil write (`scripts/run_modbus_plc_sim.py` + `cell_to_pack.factory.plc`). Modes: `modbus` | `stdio` (safe default, no network).
* **MES:** Append-only **JSON Lines** log under configurable path (`cell_to_pack.factory.mes`).

## 5. Architecture Diagram (Text Representation)

```
[Robotic Arm] --> (3D/2D Cameras) --> [Jetson Orin Nano]
                                          |-- Pre-processing (Depth Map)
                                          |-- Trigger Logic
                                          v
                                   [Factory Network]
                                          v
                               [Local GPU Cluster (VLM)]
                                          |-- Reasoning / Prompt Execution
                                          |-- JSON Generation
                                          v
                -------------------------------------------------
                |                                               |
        [PLC / Robot Controller]                       [MES / ERP Database]
        (Halts line if defect)                         (Logs audit trail)
```

## 6. Repository Layout (Reference)

```
cell-to-pack/
├── src/cell_to_pack/     # Application package
├── tests/                # Pytest unit tests
├── scripts/              # Modbus PLC simulator, utilities
├── assets/samples/       # Optional demo images (or generated at runtime)
├── docs/
│   ├── plan/plan.md
│   └── architecture/architecture.md
└── README.md
```

## 7. End-to-End Sequence (Reference)

1. Edge builds fused image (RGB | depth heatmap).
2. Client sends image to `POST /v1/analyze` with `pack_id` and timeout.
3. Server returns `VLMVerdict` JSON.
4. If `defect_found`, orchestrator invokes PLC halt (Modbus or stdio).
5. Orchestrator appends audit row to MES JSONL (verdict + paths, no secrets).
