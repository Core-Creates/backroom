import numpy as np
from PIL import Image
from pathlib import Path

def test_detect_shelf_gaps_smoke(tmp_path: Path):
    # Create a mostly uniform image with one noisy strip (fake product band)
    h, w = 240, 320
    base = np.full((h, w), 220, np.uint8)
    rng = np.random.default_rng(0)
    base[:, 100:140] = rng.integers(150, 255, size=(h, 40), dtype=np.uint8)
    p = tmp_path / "shelf.png"
    Image.fromarray(base, mode="L").save(p)

    # Local mode should report some uniform tiles
    res_local = detect_shelf_gaps(p, mode="local", tile=40, uniform_thresh=800.0)
    assert 0.0 <= res_local.gap_score <= 1.0
    assert "tiles" in res_local.notes

    # Global mode should produce a number in range and include variance
    res_global = detect_shelf_gaps(p, mode="global")
    assert 0.0 <= res_global.gap_score <= 1.0
    assert "var=" in res_global.notes