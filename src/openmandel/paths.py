import os
import re
from pathlib import Path

from openmandel.errors import PathSecurityError

OUTPUT_DIR_ENV = "OPENMANDEL_OUTPUT_DIR"
ALLOW_ARB_ENV = "OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS"
MAX_DIM_ENV = "OPENMANDEL_MAX_IMAGE_DIMENSION"
MAX_ITER_ENV = "OPENMANDEL_MAX_ITER"

_DEFAULT_OUTPUT_DIR = "~/Pictures/openmandel"
_MAX_IMAGE_DIMENSION = 2048
_MAX_ITER = 5000


def get_output_root() -> Path:
    raw = os.environ.get(OUTPUT_DIR_ENV, _DEFAULT_OUTPUT_DIR)
    return Path(raw).expanduser().resolve()


def arbitrary_output_dirs_allowed() -> bool:
    val = os.environ.get(ALLOW_ARB_ENV, "false").strip().lower()
    return val in ("1", "true", "yes", "on")


def get_max_image_dimension() -> int:
    raw = os.environ.get(MAX_DIM_ENV, str(_MAX_IMAGE_DIMENSION))
    try:
        val = int(raw)
    except (ValueError, TypeError):
        val = _MAX_IMAGE_DIMENSION
    return min(val, _MAX_IMAGE_DIMENSION)


def get_max_iter() -> int:
    raw = os.environ.get(MAX_ITER_ENV, str(_MAX_ITER))
    try:
        val = int(raw)
    except (ValueError, TypeError):
        val = _MAX_ITER
    return min(val, _MAX_ITER)


def resolve_output_dir(output_dir: str | None) -> Path:
    root = get_output_root()
    if output_dir is None:
        root.mkdir(parents=True, exist_ok=True)
        return root
    resolved = Path(output_dir).expanduser().resolve()
    if not arbitrary_output_dirs_allowed():
        if not resolved.is_relative_to(root):
            raise PathSecurityError(
                f"Output directory {resolved} is not inside the allowed output root {root}. "
                f"Set {ALLOW_ARB_ENV}=true to allow arbitrary output directories."
            )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def resolve_output_path(output_path: str | None, default_filename: str) -> Path:
    root = get_output_root()
    if output_path is None:
        return root / default_filename
    resolved = Path(output_path).expanduser().resolve()
    if not arbitrary_output_dirs_allowed():
        if not resolved.is_relative_to(root):
            raise PathSecurityError(
                f"Output path {resolved} is not inside the allowed output root {root}. "
                f"Set {ALLOW_ARB_ENV}=true to allow arbitrary output directories."
            )
    parent = resolved.parent
    parent.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_png_suffix(path: Path) -> Path:
    if path.suffix.lower() not in (".png",):
        return path.with_suffix(".png")
    return path


INVALID_FS_CHARS = re.compile(r"[^\w\-.]")


def slugify_filename(value: str, fallback: str = "mandelbrot") -> str:
    value = value.strip().lower()
    value = re.sub(r"[_\s]+", "-", value)
    value = INVALID_FS_CHARS.sub("", value)
    value = value.strip("-.")
    if not value:
        return fallback
    return value


def reserve_available_path(path: Path, overwrite: bool = False) -> Path:
    if overwrite:
        return path
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}-{counter:03d}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
