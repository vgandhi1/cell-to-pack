from __future__ import annotations

import numpy as np
import cv2

from cell_to_pack.edge.fusion import fuse_optical_depth


def render_synthetic_scene(
    *,
    good: bool = True,
    size: tuple[int, int] = (480, 640),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Render a toy optical frame + depth map for lab demos.

    Returns:
        optical_bgr, depth_map, fused_bgr
    """
    h, w = size
    optical = np.zeros((h, w, 3), dtype=np.uint8)
    # Grey "module base"
    optical[:] = (55, 55, 55)

    rng = np.random.default_rng(42 if good else 99)

    margin = max(8, int(0.04 * w))
    bar_h = max(20, h // 8)

    if good:
        # Orange busbar strips (BGR-ish orange), scale with resolution for stable HSV coverage
        y1 = h // 3
        y2 = 2 * h // 3
        cv2.rectangle(optical, (margin, y1), (w - margin, y1 + bar_h), (30, 120, 255), thickness=-1)
        cv2.rectangle(optical, (margin, y2), (w - margin, y2 + bar_h), (40, 140, 255), thickness=-1)
        # Grey thermal paste smear
        ax, ay = int(0.28 * w), int(0.19 * h)
        cv2.ellipse(optical, (w // 2, h // 2), (ax, ay), 0, 0, 360, (120, 120, 120), thickness=-1)
    else:
        # Wrong-color "busbar" (not in orange HSV band) + incomplete paste arc
        cv2.rectangle(
            optical,
            (margin + 40, h // 3),
            (w // 2 - 10, h // 3 + bar_h // 2),
            (200, 60, 40),
            thickness=-1,
        )
        paste_cx, paste_cy = w // 2 + w // 8, h // 2
        paste_rx, paste_ry = max(40, w // 6), max(24, h // 10)
        cv2.ellipse(
            optical,
            (paste_cx, paste_cy),
            (paste_rx, paste_ry),
            0,
            0,
            200,
            (90, 90, 90),
            thickness=-1,
        )

    # Depth: good = textured paste; bad = globally flat so depth-panel ROI has low variance
    if good:
        depth = np.full((h, w), 0.4, dtype=np.float32)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        depth += 0.08 * np.sin(xx / 25.0) * np.cos(yy / 31.0)
        depth += 0.12 * rng.standard_normal((h, w)).astype(np.float32) * 0.5
        mask = np.zeros((h, w), dtype=np.uint8)
        ax, ay = int(0.28 * w), int(0.19 * h)
        cv2.ellipse(mask, (w // 2, h // 2), (ax, ay), 0, 0, 360, 255, thickness=-1)
        depth = np.where(mask > 0, depth + 0.25 + 0.05 * rng.standard_normal((h, w)), depth)
    else:
        depth = np.full((h, w), 0.5, dtype=np.float32)
        depth += 0.002 * rng.standard_normal((h, w)).astype(np.float32)

    fused = fuse_optical_depth(optical, depth)
    return optical, depth, fused


def load_fused_from_files(optical_path: str, depth_path: str) -> np.ndarray:
    """Load optical (BGR) and depth (16-bit PNG or any single-channel) from disk and fuse."""
    optical = cv2.imread(optical_path, cv2.IMREAD_COLOR)
    if optical is None:
        raise FileNotFoundError(optical_path)
    depth = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
    if depth is None:
        raise FileNotFoundError(depth_path)
    if depth.ndim == 3:
        depth = cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY)
    depth_f = depth.astype(np.float32)
    return fuse_optical_depth(optical, depth_f)
