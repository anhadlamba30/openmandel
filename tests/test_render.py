from pathlib import Path

from openmandel.render import render_plan
from openmandel.schema import MandelbrotPlan


def test_smoke_render_128(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        width=128,
        height=128,
        max_iter=100,
    )
    result = render_plan(plan)

    img_path = Path(result.image_path)
    assert img_path.exists()
    assert img_path.suffix == ".png"

    meta_path = Path(result.metadata_path)
    assert meta_path.exists()
    assert meta_path.suffix == ".json"

    assert result.width == 128
    assert result.height == 128
    assert result.elapsed_ms > 0


def test_deterministic_render_same_seed(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        width=128,
        height=128,
        max_iter=50,
        seed=42,
    )
    r1 = render_plan(plan, overwrite=True)
    r2 = render_plan(plan, overwrite=True)

    assert r1.seed == r2.seed


def test_deterministic_render_byte_identical(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        width=128,
        height=128,
        max_iter=50,
        seed=42,
    )
    r1 = render_plan(plan)
    r2 = render_plan(plan)

    with open(r1.image_path, "rb") as f:
        data1 = f.read()
    with open(r2.image_path, "rb") as f:
        data2 = f.read()
    assert data1 == data2


def test_deterministic_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        width=128,
        height=128,
        max_iter=50,
        seed=42,
    )
    import json
    r = render_plan(plan)
    with open(r.metadata_path) as f:
        meta = json.load(f)
    assert meta["plan"]["seed"] == 42
    assert meta["generator"] == "openmandel"
    assert "elapsed_ms" in meta
    assert "created_at" in meta
    assert "image_path" in meta
