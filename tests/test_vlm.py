from cell_to_pack.edge.simulator import render_synthetic_scene
from cell_to_pack.inference.vlm import analyze_fused_bgr


def test_mock_vlm_good_passes():
    _, _, fused = render_synthetic_scene(good=True, size=(240, 320))
    v = analyze_fused_bgr(fused)
    assert v.defect_found is False
    assert v.severity == "none"


def test_mock_vlm_bad_fails():
    _, _, fused = render_synthetic_scene(good=False, size=(240, 320))
    v = analyze_fused_bgr(fused)
    assert v.defect_found is True
    assert v.severity in {"high", "critical"}
