from __future__ import annotations

import numpy as np
import cv2


def fuse_optical_depth(optical_bgr: np.ndarray, depth_map: np.ndarray) -> np.ndarray:
    """
    Build a single transport payload: optical RGB | depth colormap (2.5D proxy).

    Args:
        optical_bgr: uint8 HxWx3 BGR frame.
        depth_map: HxW float32 or uint16 depth; same height as optical; width may differ (resized to optical width).

    Returns:
        uint8 H x (2*W) x3 side-by-side image.
    """
    if optical_bgr.ndim != 3 or optical_bgr.shape[2] != 3:
        raise ValueError("optical_bgr must be HxWx3 uint8 BGR")
    if depth_map.ndim != 2:
        raise ValueError("depth_map must be HxW")

    h, w = optical_bgr.shape[:2]
    if depth_map.shape[0] != h or depth_map.shape[1] != w:
        depth_map = cv2.resize(depth_map, (w, h), interpolation=cv2.INTER_NEAREST)

    d = depth_map.astype(np.float32)
    if d.max() > d.min():
        d_norm = ((d - d.min()) / (d.max() - d.min()) * 255.0).astype(np.uint8)
    else:
        d_norm = np.zeros_like(d, dtype=np.uint8)

    depth_color = cv2.applyColorMap(d_norm, cv2.COLORMAP_INFERNO)
    return np.hstack([optical_bgr, depth_color])
