from __future__ import annotations

import time

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from cell_to_pack import __version__
from cell_to_pack.inference.vlm import analyze_fused_bgr
from cell_to_pack.schemas import AnalyzeResponse

app = FastAPI(
    title="Cell-to-Pack Vision Orchestrator",
    version=__version__,
    description="Reference HTTP API for fused-image analysis (mock VLM).",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/v1/analyze", response_model=AnalyzeResponse)
async def analyze(
    pack_id: str = Form(..., min_length=1, max_length=128),
    image: UploadFile = File(..., description="Fused PNG/JPEG: optical | depth"),
) -> AnalyzeResponse:
    if image.content_type not in {"image/png", "image/jpeg", "image/jpg", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported image content type")

    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty upload")

    buf = np.frombuffer(raw, dtype=np.uint8)
    decoded = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="Could not decode image")

    t0 = time.perf_counter()
    verdict = analyze_fused_bgr(decoded)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    return AnalyzeResponse(pack_id=pack_id, verdict=verdict, latency_ms=latency_ms)


def create_app() -> FastAPI:
    return app
