from pathlib import Path

from openmandel.gallery import generate_gallery
from openmandel.render import render_plan
from openmandel.schema import MandelbrotPlan


def test_gallery_created(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        width=128,
        height=128,
        max_iter=50,
    )
    render_plan(plan)

    result = generate_gallery(
        input_dir=str(tmp_path),
        title="Test Gallery",
        overwrite=True,
    )
    gallery_path = Path(result["gallery_path"])
    assert gallery_path.exists()
    assert gallery_path.suffix == ".html"
    assert result["image_count"] >= 1


def test_gallery_empty_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    result = generate_gallery(
        input_dir=str(tmp_path),
        title="Empty Gallery",
        overwrite=True,
    )
    assert result["image_count"] == 0
    assert Path(result["gallery_path"]).exists()
