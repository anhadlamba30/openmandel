import json
import time
from pathlib import Path

import numpy as np
from PIL import Image

from openmandel.errors import RenderError
from openmandel.metadata import build_metadata
from openmandel.palettes import PALETTE_MAP
from openmandel.paths import (
    ensure_png_suffix,
    get_max_image_dimension,
    get_max_iter,
    reserve_available_path,
    resolve_output_path,
    slugify_filename,
)
from openmandel.schema import MandelbrotPlan, RenderResult


def _compute_mandelbrot(plan: MandelbrotPlan):
    width, height = plan.width, plan.height
    max_iter = plan.max_iter
    zoom = plan.zoom
    center_real, center_imag = plan.center_real, plan.center_imag

    base_span = 3.5
    span_x = base_span / zoom
    span_y = span_x * height / width

    x = np.linspace(center_real - span_x / 2, center_real + span_x / 2, width)
    y = np.linspace(center_imag - span_y / 2, center_imag + span_y / 2, height)
    xv, yv = np.meshgrid(x, y)
    c = xv + 1j * yv

    z = np.zeros_like(c, dtype=np.complex128)
    escape_iter = np.zeros(c.shape, dtype=np.int32)
    final_z = np.zeros_like(c, dtype=np.complex128)
    still_active = np.ones(c.shape, dtype=bool)

    cap_hard = get_max_iter()
    effective_max = min(max_iter, cap_hard)

    for i in range(1, effective_max + 1):
        z[still_active] = z[still_active] ** 2 + c[still_active]
        active_escaped = still_active & (np.abs(z) > 2.0)
        escape_iter[active_escaped] = i
        final_z[active_escaped] = z[active_escaped]
        still_active[active_escaped] = False
        if not still_active.any():
            break

    return escape_iter, final_z, effective_max


def _iterations_to_color(
    escape_iter: np.ndarray,
    final_z: np.ndarray,
    max_iter: int,
    plan: MandelbrotPlan,
) -> np.ndarray:
    height, width = escape_iter.shape
    rgb = np.zeros((height, width, 3), dtype=np.uint8)

    palette_info = PALETTE_MAP.get(plan.palette)
    colors = palette_info.colors if palette_info else [(0, 0, 0)]
    background_rgb = _parse_background(plan.background)

    interior_mask = escape_iter == 0
    rgb[interior_mask] = background_rgb

    escaped_mask = escape_iter > 0
    if not escaped_mask.any():
        return rgb

    if plan.coloring == "escape_time":
        values = escape_iter.astype(np.float64) / max_iter
    else:
        smooth = escape_iter.astype(np.float64)
        z_abs = np.abs(final_z[escaped_mask])
        smooth_vals = np.zeros_like(z_abs)
        np.log(z_abs, where=z_abs > 1.0, out=smooth_vals)
        np.log2(smooth_vals, where=smooth_vals > 0.0, out=smooth_vals)
        smooth_vals = np.nan_to_num(smooth_vals, nan=0.0, posinf=0.0, neginf=0.0)
        smooth[escaped_mask] = smooth[escaped_mask] - smooth_vals
        values = np.zeros_like(escape_iter, dtype=np.float64)
        values[escaped_mask] = smooth[escaped_mask] / max_iter

    values[escaped_mask] = np.clip(values[escaped_mask], 0, 1)

    contrast = plan.contrast
    gamma = plan.gamma
    norm = np.power(values * contrast, gamma, where=escaped_mask, out=values)
    norm = np.clip(norm, 0, 1)

    stops = np.array(colors, dtype=np.float64)
    n_stops = len(stops) - 1
    positions = norm[escaped_mask] * n_stops
    idx = np.floor(positions).astype(np.int32)
    frac = positions - idx
    idx = np.clip(idx, 0, n_stops - 1)
    f = frac[:, np.newaxis]
    c0 = stops[idx]
    c1 = stops[idx + 1]
    interpolated = np.clip(c0 + (c1 - c0) * f, 0, 255).astype(np.uint8)
    rgb[escaped_mask] = interpolated

    return rgb


def _parse_background(color_str: str) -> tuple[int, int, int]:
    try:
        from PIL.ImageColor import getrgb
        rgb = getrgb(color_str)
        if len(rgb) == 4:
            return rgb[:3]
        return rgb
    except (ValueError, OSError):
        return (0, 0, 0)


def render_plan(
    plan: MandelbrotPlan,
    output_path: str | None = None,
    overwrite: bool = False,
) -> RenderResult:
    max_dim = get_max_image_dimension()
    if plan.width > max_dim:
        raise RenderError(
            f"Width {plan.width} exceeds maximum allowed dimension {max_dim}"
        )
    if plan.height > max_dim:
        raise RenderError(
            f"Height {plan.height} exceeds maximum allowed dimension {max_dim}"
        )

    start = time.perf_counter()
    escape_iter, final_z, effective_max = _compute_mandelbrot(plan)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    image_array = _iterations_to_color(escape_iter, final_z, effective_max, plan)

    if output_path is None:
        if plan.description:
            slug = slugify_filename(plan.description[:60])
        else:
            slug = "mandelbrot"
        short_hash = plan.derive_seed()
        filename = f"{slug}-{short_hash:08x}.png"
        filename = slugify_filename(filename, fallback="mandelbrot.png")
        if not filename.endswith(".png"):
            filename = filename + ".png"
    else:
        filename = ""
        out_path = Path(output_path)

    if output_path is not None:
        out_path = ensure_png_suffix(Path(output_path))
    else:
        out_path = ensure_png_suffix(
            resolve_output_path(None, filename)
        )

    resolved = resolve_output_path(str(out_path), filename) if output_path is None else out_path
    if output_path is not None:
        resolved = ensure_png_suffix(Path(output_path).expanduser().resolve())
        resolved.parent.mkdir(parents=True, exist_ok=True)

    resolved = reserve_available_path(resolved, overwrite=overwrite)
    metadata_path = resolved.with_suffix(".json")

    actual_seed = plan.seed if plan.seed is not None else plan.derive_seed()

    image = Image.fromarray(image_array, mode="RGB")
    image.save(resolved, format="PNG")

    meta = build_metadata(str(resolved), plan, elapsed_ms, actual_seed)
    metadata_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return RenderResult(
        image_path=str(resolved),
        metadata_path=str(metadata_path),
        plan=plan,
        width=plan.width,
        height=plan.height,
        elapsed_ms=round(elapsed_ms, 1),
        seed=actual_seed,
        overwritten=overwrite,
    )
