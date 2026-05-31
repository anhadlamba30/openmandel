from pathlib import Path

from openmandel.server import create_mandelbrot_variations


def test_variation_count_4(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    result = create_mandelbrot_variations(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        count=4,
        width=128,
        height=128,
        max_iter=50,
        overwrite=True,
    )
    assert len(result["images"]) == 4
    assert result["contact_sheet_path"] is not None
    assert Path(result["contact_sheet_path"]).exists()


def test_variation_same_seed_produces_same_plans(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    kw = dict(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        count=2,
        width=128,
        height=128,
        max_iter=50,
        seed=123,
        overwrite=True,
    )
    r1 = create_mandelbrot_variations(**kw)
    r2 = create_mandelbrot_variations(**kw)

    for img1, img2 in zip(r1["images"], r2["images"]):
        assert img1["seed"] == img2["seed"]


def test_variation_count_exceeds_max(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    result = create_mandelbrot_variations(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        count=20,
        width=128,
        height=128,
        max_iter=50,
        overwrite=True,
    )
    assert len(result["images"]) <= 8


def test_variation_contact_sheet_produced(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    result = create_mandelbrot_variations(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        count=3,
        width=128,
        height=128,
        max_iter=50,
        make_contact_sheet=True,
        overwrite=True,
    )
    assert result["contact_sheet_path"] is not None
    assert Path(result["contact_sheet_path"]).exists()


def test_variation_no_contact_sheet(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))

    result = create_mandelbrot_variations(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
        count=2,
        width=128,
        height=128,
        max_iter=50,
        make_contact_sheet=False,
        overwrite=True,
    )
    assert result["contact_sheet_path"] is None
