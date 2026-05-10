import numpy as np

from cell_to_pack.edge.fusion import fuse_optical_depth


def test_fuse_optical_depth_shape_and_range():
    optical = np.zeros((64, 80, 3), dtype=np.uint8)
    depth = np.linspace(0, 1, 64 * 80, dtype=np.float32).reshape(64, 80)
    fused = fuse_optical_depth(optical, depth)
    assert fused.shape == (64, 160, 3)
    assert fused.dtype == np.uint8
