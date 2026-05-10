# Product Plan: EV Battery "Cell-to-Pack" Vision Orchestrator

## 1. Executive Summary
The EV Battery "Cell-to-Pack" Vision Orchestrator is a mission-critical edge AI system designed to ensure zero-defect battery assembly in real-time. By leveraging the NVIDIA Jetson Orin Nano Super at the edge to fuse 3D machine vision and 2D optical data, and utilizing a centralized Vision-Language Model (VLM) for deep contextual reasoning, this product proactively stops robotic assembly lines before irreversible and costly errors occur.

## 2. Product Objectives & Key Results (OKRs)

### Objective 1: Eliminate Thermal Runaway Risks from Assembly Defects
* **KR1:** Reduce unseated high-voltage busbar incidents escaping the workstation by 99.9%.
* **KR2:** Ensure 100% verification of thermal paste distribution volume and geometry before pack sealing.

### Objective 2: Maximize Assembly Line Throughput and Yield
* **KR3:** Reduce false-positive defect flags by 40% compared to legacy 2D vision systems.
* **KR4:** Maintain a sub-500ms end-to-end latency for edge-to-VLM-to-PLC halt commands.

### Objective 3: Reduce Battery Pack Scrap Costs
* **KR5:** Save $2.5M annually in scrapped EV battery packs (assuming a baseline of $15k per scrapped pack).

## 3. Target Users & Stakeholders
* **Manufacturing Engineers:** Require deep diagnostic data to adjust robotic paths and calibrate dispensers.
* **Quality Assurance (QA) Managers:** Need an immutable audit log of every battery pack's internal state.
* **Plant Directors:** Focused on OEE (Overall Equipment Effectiveness) and scrap reduction ROI.

## 4. Phased Implementation Roadmap

### Phase 0: Reference Software Stack (Developer / Lab)
* **Purpose:** De-risk integration before hardware lands on the line.
* **Deliverables:** Simulated edge fusion, HTTP inference API with pluggable mock-VLM heuristics, JSONL MES-style audit log, optional Modbus TCP PLC simulator, CLI and automated tests (see repository [`README.md`](../../README.md) and [`docs/architecture/architecture.md`](../architecture/architecture.md)).

### Phase 1: R&D & Shadow Mode (Months 1-3)
* **Hardware Procurement:** Deploy stereoscopic cameras and Jetson Orin Nano Super modules on a single test cell.
* **Data Ingestion Pipeline:** Begin capturing and logging 3D point clouds and 2D images.
* **Shadow Inference:** Run the VLM pipeline in parallel to production without PLC halt authority. Compare VLM defect flags against human QA logs.

### Phase 2: Pilot Deployment (Months 4-6)
* **PLC Integration:** Grant the Orchestrator "stop" authority on a single robotic cell.
* **Edge Optimization:** Refine the 3D-to-2D depth map conversion to minimize payload size over the factory network.
* **UI/UX Deployment:** Roll out the QA dashboard to line operators for overriding/reviewing VLM halt commands.

### Phase 3: Plant-Wide Scaling (Months 7-12)
* **Scale-Out:** Deploy to all battery assembly lines across the facility.
* **Model Fine-Tuning:** Use the logged defect data from the Pilot phase to fine-tune a smaller, localized VLM to reduce cloud compute dependency.

## 5. Risk Mitigation
* **Risk:** Factory network latency spikes causing robot crashes.
  * *Mitigation:* Implement a hard timeout at the edge. If the VLM does not respond within 450ms, the Jetson Nano triggers a default fail-safe halt.
* **Risk:** High reflectivity of metallic battery cells confusing the cameras.
  * *Mitigation:* Rely heavily on the 3D structured light / time-of-flight (ToF) sensors for volumetric data, using 2D optical only for contextual overlay.

## 6. Success Metrics (Reference Implementation)
* **Functional:** End-to-end run produces a VLM-style JSON verdict, optional PLC halt signal, and append-only audit record per pack ID.
* **Latency (lab):** Inference HTTP round-trip target **under 500 ms** on localhost; production budget remains **450 ms** VLM timeout at edge.
* **Safety:** Production deployments must never skip the edge timeout and fail-safe path described in section 5.
