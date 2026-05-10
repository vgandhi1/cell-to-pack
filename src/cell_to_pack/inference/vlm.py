from __future__ import annotations

import time

import cv2
import numpy as np

from cell_to_pack.schemas import VLMVerdict


def _split_panels(fused_bgr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    h, w, _ = fused_bgr.shape
    mid = w // 2
    optical = fused_bgr[:, :mid].copy()
    depth_vis = fused_bgr[:, mid:].copy()
    return optical, depth_vis


def analyze_fused_bgr(fused_bgr: np.ndarray) -> VLMVerdict:
    """
    Mock multimodal reasoning: proxies for paste continuity (depth texture) and busbars (orange HSV).

    Replace this function with a real VLM + structured JSON parser in production.
    """
    optical, depth_vis = _split_panels(fused_bgr)
    gray_depth = cv2.cvtColor(depth_vis, cv2.COLOR_BGR2GRAY)
    dh, dw = gray_depth.shape
    roi = gray_depth[dh // 4 : 3 * dh // 4, dw // 4 : 3 * dw // 4]
    depth_std = float(np.std(roi)) if roi.size else 0.0

    hsv = cv2.cvtColor(optical, cv2.COLOR_BGR2HSV)
    # Orange busbar-ish range in OpenCV HSV
    lower = np.array([5, 80, 80])
    upper = np.array([22, 255, 255])
    mask = cv2.inRange(hsv, lower, upper)
    orange_ratio = float(np.count_nonzero(mask)) / float(mask.size) if mask.size else 0.0

    reasons: list[str] = []
    severity = "none"
    defect = False

    # Tunable thresholds for synthetic demo imagery
    if depth_std < 14.0:
        defect = True
        reasons.append("Depth map shows insufficient texture in paste region (continuity risk).")
        severity = "high"

    if orange_ratio < 0.018:
        defect = True
        reasons.append("High-voltage busbar coverage below expected (flush / presence check).")
        severity = "critical" if severity != "high" else "critical"

    if not defect:
        return VLMVerdict(
            defect_found=False,
            reason="Thermal paste and busbar proxies within expected ranges.",
            severity="none",
        )

    return VLMVerdict(
        defect_found=True,
        reason="; ".join(reasons),
        severity=severity,
    )


def analyze_fused_bgr_timed(fused_bgr: np.ndarray) -> tuple[VLMVerdict, float]:
    t0 = time.perf_counter()
    verdict = analyze_fused_bgr(fused_bgr)
    ms = (time.perf_counter() - t0) * 1000.0
    return verdict, ms
