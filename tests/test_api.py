import io

import cv2
from fastapi.testclient import TestClient

from cell_to_pack.edge.simulator import render_synthetic_scene
from cell_to_pack.inference.server import app


def test_analyze_good_pack():
    _, _, fused = render_synthetic_scene(good=True, size=(120, 160))
    ok, buf = cv2.imencode(".png", fused)
    assert ok
    client = TestClient(app)
    files = {"image": ("fused.png", io.BytesIO(buf.tobytes()), "image/png")}
    r = client.post("/v1/analyze", data={"pack_id": "T-API-1"}, files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["pack_id"] == "T-API-1"
    assert body["verdict"]["defect_found"] is False
