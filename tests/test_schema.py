import pytest
from pydantic import ValidationError

from openmandel.schema import MandelbrotPlan


def test_valid_plan():
    plan = MandelbrotPlan(
        center_real=-0.5,
        center_imag=0.0,
        zoom=1,
    )
    assert plan.width == 1024
    assert plan.height == 1024
    assert plan.max_iter == 1000
    assert plan.palette == "electric_blue"
    assert plan.coloring == "smooth"


def test_invalid_palette():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=1,
            palette="nonexistent",
        )


def test_invalid_coloring_mode():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=1,
            coloring="invalid",
        )


def test_width_too_large():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=1,
            width=3000,
        )


def test_height_too_large():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=1,
            height=3000,
        )


def test_max_iter_too_large():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=1,
            max_iter=10000,
        )


def test_coordinate_out_of_range():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-5.0,
            center_imag=0.0,
            zoom=1,
        )
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=0.0,
            center_imag=-5.0,
            zoom=1,
        )


def test_zoom_too_small():
    with pytest.raises(ValidationError):
        MandelbrotPlan(
            center_real=-0.5,
            center_imag=0.0,
            zoom=0.5,
        )


def test_canonical_json_stable():
    p1 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=1, seed=42, description="test")
    p2 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=1, seed=99, description="other")
    assert p1.canonical_json() == p2.canonical_json()
    assert "seed" not in p1.canonical_json()
    assert "description" not in p1.canonical_json()


def test_derive_seed_deterministic():
    p1 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=1)
    p2 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=1)
    assert p1.derive_seed() == p2.derive_seed()


def test_derive_seed_changes_with_params():
    p1 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=1)
    p2 = MandelbrotPlan(center_real=-0.5, center_imag=0.0, zoom=2)
    assert p1.derive_seed() != p2.derive_seed()
