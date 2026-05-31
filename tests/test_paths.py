
import pytest

from openmandel.errors import PathSecurityError
from openmandel.paths import (
    get_output_root,
    reserve_available_path,
    resolve_output_dir,
    resolve_output_path,
    slugify_filename,
)


def test_default_output_root_resolves(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    root = get_output_root()
    assert root.is_absolute()


def test_tilde_expands(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    root = get_output_root()
    assert "~" not in str(root)
    assert root == tmp_path.resolve()


def test_output_dir_inside_root_passes(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    inside = tmp_path / "sub"
    inside.mkdir(parents=True)
    result = resolve_output_dir(str(inside))
    assert result == inside.resolve()


def test_output_dir_outside_root_fails_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS", "false")
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    outside = tmp_path.parent / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    with pytest.raises(PathSecurityError):
        resolve_output_dir(str(outside))


def test_output_dir_outside_root_passes_when_enabled(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS", "true")
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    outside = tmp_path.parent / "outside"
    outside.mkdir(parents=True, exist_ok=True)
    result = resolve_output_dir(str(outside))
    assert result == outside.resolve()


def test_path_traversal_attempt_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS", "false")
    monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))
    traversal = str(tmp_path / ".." / ".." / "etc" / "passwd")
    with pytest.raises(PathSecurityError):
        resolve_output_path(traversal, "test.png")


def test_existing_file_gets_suffix(tmp_path):
    existing = tmp_path / "test.png"
    existing.touch()
    result = reserve_available_path(existing, overwrite=False)
    assert result != existing
    assert result.name.startswith("test-")
    assert result.suffix == ".png"


def test_nonexistent_file_no_suffix(tmp_path):
    path = tmp_path / "new.png"
    result = reserve_available_path(path, overwrite=False)
    assert result == path


def test_overwrite_returns_same(tmp_path):
    existing = tmp_path / "test.png"
    existing.touch()
    result = reserve_available_path(existing, overwrite=True)
    assert result == existing


def test_slugify_filename():
    assert slugify_filename("Hello World") == "hello-world"
    assert slugify_filename("  Spaces  ") == "spaces"
    assert slugify_filename("") == "mandelbrot"
    assert slugify_filename("special!@#chars") == "specialchars"
