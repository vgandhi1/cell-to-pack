from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import cv2
import httpx
import numpy as np

from cell_to_pack.config import Settings
from cell_to_pack.edge.simulator import render_synthetic_scene
from cell_to_pack.factory.mes import append_audit_record
from cell_to_pack.factory.plc import signal_halt
from cell_to_pack.schemas import AnalyzeResponse, VLMVerdict
from cell_to_pack.inference.vlm import analyze_fused_bgr_timed

logger = logging.getLogger(__name__)


def _encode_png(bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise RuntimeError("PNG encode failed")
    return buf.tobytes()


def run_local_inference(fused_bgr: np.ndarray) -> tuple[VLMVerdict, float]:
    return analyze_fused_bgr_timed(fused_bgr)


def run_remote_inference(
    base_url: str,
    pack_id: str,
    fused_bgr: np.ndarray,
    timeout_s: float,
) -> AnalyzeResponse:
    url = base_url.rstrip("/") + "/v1/analyze"
    png = _encode_png(fused_bgr)
    files = {"image": ("fused.png", png, "image/png")}
    data = {"pack_id": pack_id}
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, data=data, files=files)
        r.raise_for_status()
        payload: dict[str, Any] = r.json()
    return AnalyzeResponse.model_validate(payload)


def orchestrate_once(
    settings: Settings,
    *,
    pack_id: str,
    good: bool,
    use_remote: str | None,
    save_dir: Path | None = None,
) -> VLMVerdict:
    """
    Full reference path: synthetic edge → inference → PLC + MES.
    """
    _, _, fused = render_synthetic_scene(good=good)

    image_path: str | None = None
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        out = save_dir / f"{pack_id}_fused.png"
        cv2.imwrite(str(out), fused)
        image_path = str(out.resolve())

    if use_remote:
        t0 = time.perf_counter()
        try:
            resp = run_remote_inference(use_remote, pack_id, fused, settings.request_timeout_s)
        except httpx.HTTPError as e:
            logger.error("Remote inference failed: %s", type(e).__name__)
            # Fail-safe: treat transport failure like a critical defect path for demo safety
            verdict = VLMVerdict(
                defect_found=True,
                reason="Inference transport failure — fail-safe stop recommended.",
                severity="critical",
            )
            signal_halt(settings, reason=verdict.reason)
            append_audit_record(
                settings,
                pack_id=pack_id,
                verdict=verdict,
                fused_image_path=image_path,
                extra={"error": "inference_transport", "latency_ms": (time.perf_counter() - t0) * 1000.0},
            )
            return verdict

        verdict = resp.verdict
        extra = {"latency_ms": resp.latency_ms, "remote": True}
    else:
        verdict, infer_ms = run_local_inference(fused)
        extra = {"latency_ms": infer_ms, "remote": False}

    if verdict.defect_found:
        signal_halt(settings, reason=verdict.reason)

    append_audit_record(settings, pack_id=pack_id, verdict=verdict, fused_image_path=image_path, extra=extra)
    return verdict
