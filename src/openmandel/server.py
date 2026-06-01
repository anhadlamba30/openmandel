import base64
import hashlib
import math
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from openmandel.gallery import create_contact_sheet, generate_gallery
from openmandel.palettes import PALETTES
from openmandel.paths import (
    arbitrary_output_dirs_allowed,
    get_max_image_dimension,
    get_max_iter,
    get_output_root,
    reserve_available_path,
    resolve_output_dir,
    slugify_filename,
)
from openmandel.presets import PRESETS
from openmandel.render import render_plan
from openmandel.schema import MandelbrotPlan, RenderResult, VariationResult

mcp = FastMCP("openmandel")


@mcp.tool()
def list_mandelbrot_presets() -> list[dict]:
    """Return all known Mandelbrot region presets with coordinates and guidance.
    Call this first if you need good known coordinates for a render.
    Returns a list of presets with name, description, coordinates, vibes, and suggested palettes."""
    return [p.model_dump(mode="json") for p in PRESETS]


@mcp.tool()
def list_mandelbrot_palettes() -> list[dict]:
    """Return all valid palette names with descriptions and style guidance.
    Call this first if you need to choose a color palette.
    Returns a list of palettes with name, description, and vibes (no raw color arrays)."""
    return [
        {"name": p.name, "description": p.description, "vibes": p.vibes}
        for p in PALETTES
    ]


@mcp.tool()
def render_mandelbrot_plan(
    center_real: float,
    center_imag: float,
    zoom: float,
    max_iter: int = 1000,
    width: int = 1024,
    height: int = 1024,
    palette: str = "electric_blue",
    coloring: str = "smooth",
    background: str = "black",
    contrast: float = 1.0,
    gamma: float = 1.0,
    seed: int | None = None,
    output_path: str | None = None,
    description: str | None = None,
    overwrite: bool = False,
    custom_palette: list[str] | None = None,
    return_base64: bool = False,
) -> dict:
    """Render a deterministic Mandelbrot image from explicit fractal parameters.
    Use this when you know the region, zoom, palette, and style you want.
    Call list_mandelbrot_presets first if you need good known coordinates.
    Call list_mandelbrot_palettes first if you need valid palette names.

    Coordinate guidance:
    - Use seahorse_valley-like coordinates for spirals/cathedrals/deep intricate prompts.
    - Use elephant_valley-like coordinates for organic/coral/alien reef prompts.
    - Use mini_mandelbrot-like coordinates for nested/recursive/symbolic prompts.
    - Use antenna_tip-like coordinates for minimal/stark/needle-like prompts.

    Custom palette: pass a list of color strings (hex like "#ff6432", named like "coral",
    or rgb like "rgb(255,100,50)") with 2 to 32 stops. Overrides the named palette.

    Set return_base64=True to get the image bytes as a base64 string in the response
    (image_base64 field), so the AI can display the image inline."""
    plan = MandelbrotPlan(
        center_real=center_real,
        center_imag=center_imag,
        zoom=zoom,
        max_iter=max_iter,
        width=width,
        height=height,
        palette=palette,
        coloring=coloring,
        background=background,
        contrast=contrast,
        gamma=gamma,
        seed=seed,
        description=description,
        custom_palette=custom_palette,
    )
    result = render_plan(plan, output_path=output_path, overwrite=overwrite)
    data = result.model_dump(mode="json")
    if return_base64:
        with open(result.image_path, "rb") as f:
            data["image_base64"] = base64.b64encode(f.read()).decode("ascii")
        data["image_mime_type"] = "image/png"
    return data


@mcp.tool()
def create_mandelbrot_variations(
    center_real: float,
    center_imag: float,
    zoom: float,
    count: int = 4,
    max_iter: int = 1000,
    width: int = 1024,
    height: int = 1024,
    palette: str = "electric_blue",
    coloring: str = "smooth",
    background: str = "black",
    contrast: float = 1.0,
    gamma: float = 1.0,
    seed: int | None = None,
    output_dir: str | None = None,
    basename: str | None = None,
    make_contact_sheet: bool = True,
    overwrite: bool = False,
    return_base64: bool = False,
) -> dict:
    """Generate multiple deterministic Mandelbrot variations from a base plan.
    Use this when you want several related images exploring a neighborhood.
    The server applies small deterministic perturbations to center, zoom, contrast, and gamma.

    Args:
        count: Number of variations to generate (1-8).
        basename: Base filename for output images (without extension). Auto-derived if omitted.
        return_base64: When True, includes base64-encoded image bytes in each result
                       so the AI can display images inline.

    Returns paths to all generated images, metadata files, and optional contact sheet."""
    count = max(1, min(count, 8))

    base_plan = MandelbrotPlan(
        center_real=center_real,
        center_imag=center_imag,
        zoom=zoom,
        max_iter=max_iter,
        width=width,
        height=height,
        palette=palette,
        coloring=coloring,
        background=background,
        contrast=contrast,
        gamma=gamma,
        seed=seed,
    )

    base_seed = seed if seed is not None else base_plan.derive_seed()

    out_dir = resolve_output_dir(output_dir)
    if basename:
        slug = slugify_filename(basename)
    else:
        short_hash = base_seed
        slug = f"mandelbrot-variations-{short_hash:08x}"

    span_x = 3.5 / max(zoom, 1.0)
    span_y = span_x * height / width
    offset_scale = min(span_x, span_y) * 0.15

    images: list[RenderResult] = []
    image_paths: list[Path] = []

    for i in range(count):
        vs = _stable_hash(f"{base_seed}:{i}")

        dz_real = math.sin(vs * 0.1) * offset_scale
        dz_imag = math.cos(vs * 0.13) * offset_scale
        zoom_mult = 1.0 + math.sin(vs * 0.07) * 0.3
        zoom_mult = max(0.75, min(1.35, zoom_mult))

        var_contrast = max(0.25, min(4.0, contrast + math.sin(vs * 0.11) * 0.3))
        var_gamma = max(0.25, min(4.0, gamma + math.cos(vs * 0.17) * 0.3))

        var_plan = MandelbrotPlan(
            center_real=center_real + dz_real,
            center_imag=center_imag + dz_imag,
            zoom=max(1.0, zoom * zoom_mult),
            max_iter=max_iter,
            width=width,
            height=height,
            palette=palette,
            coloring=coloring,
            background=background,
            contrast=round(var_contrast, 4),
            gamma=round(var_gamma, 4),
            seed=vs,
        )

        fname = f"{slug}-{i+1:03d}.png"
        out_path = out_dir / fname
        out_path = reserve_available_path(out_path, overwrite=overwrite)

        result = render_plan(var_plan, output_path=str(out_path), overwrite=overwrite)
        images.append(result)
        image_paths.append(Path(result.image_path))

    contact_sheet_path: str | None = None
    if make_contact_sheet and image_paths:
        cs_path = out_dir / f"{slug}-contact-sheet.png"
        cs_path = reserve_available_path(cs_path, overwrite=overwrite)
        create_contact_sheet(image_paths, cs_path)
        contact_sheet_path = str(cs_path)

    result = VariationResult(
        images=images,
        contact_sheet_path=contact_sheet_path,
        output_dir=str(out_dir),
        base_seed=base_seed,
    )
    data = result.model_dump(mode="json")
    if return_base64:
        for img in data["images"]:
            with open(img["image_path"], "rb") as f:
                img["image_base64"] = base64.b64encode(f.read()).decode("ascii")
            img["image_mime_type"] = "image/png"
        if contact_sheet_path:
            with open(contact_sheet_path, "rb") as f:
                data["contact_sheet_base64"] = base64.b64encode(f.read()).decode("ascii")
            data["contact_sheet_mime_type"] = "image/png"
    return data


@mcp.tool()
def generate_mandelbrot_gallery(
    input_dir: str | None = None,
    title: str = "openmandel gallery",
    output_path: str | None = None,
    overwrite: bool = True,
) -> dict:
    """Generate a local static HTML gallery from generated PNG/JSON files.
    Use this to create a browsable gallery of previously rendered images.
    Scans input_dir for PNG files with matching JSON metadata."""
    return generate_gallery(
        input_dir=input_dir,
        title=title,
        output_path=output_path,
        overwrite=overwrite,
    )


@mcp.tool()
def get_openmandel_config() -> dict:
    """Return current server configuration, limits, and output directory settings.
    Use this to understand what the server allows before rendering."""
    return {
        "output_root": str(get_output_root()),
        "arbitrary_output_dirs_allowed": arbitrary_output_dirs_allowed(),
        "max_image_dimension": get_max_image_dimension(),
        "max_iter": get_max_iter(),
        "supported_palettes": [p.name for p in PALETTES],
        "supported_coloring_modes": ["escape_time", "smooth"],
    }


def _viewport_iteration_guidance(zoom: float, coloring: str) -> dict:
    recommended = int(200 + 175 * math.log10(max(zoom, 1.0)))
    if zoom >= 10_000:
        recommended += 150
    if zoom >= 100_000:
        recommended += 250
    if coloring == "smooth":
        recommended += 100
    recommended = round(recommended / 50) * 50
    recommended = max(50, min(5000, recommended))
    return {
        "recommended_max_iter": recommended,
        "min_reasonable_max_iter": max(50, int(recommended * 0.5)),
        "max_reasonable_max_iter": min(5000, int(recommended * 1.5)),
    }


def _viewport_cost_hint(width: int, height: int, max_iter: int) -> dict:
    units = width * height * max_iter
    if units < 200_000_000:
        hint = "low"
    elif units < 1_000_000_000:
        hint = "medium"
    else:
        hint = "high"
    return {"estimated_work_units": units, "cost_hint": hint}


@mcp.tool()
def inspect_mandelbrot_viewport(
    center_real: float,
    center_imag: float,
    zoom: float,
    width: int = 1024,
    height: int = 1024,
    max_iter: int | None = None,
    coloring: str = "smooth",
) -> dict:
    """Inspect a Mandelbrot camera view without rendering an image.
    Use this before render_mandelbrot_plan when you want to understand what area
    of the complex plane a center/zoom/size covers, get an iteration recommendation,
    and estimate render cost.

    Returns viewport bounds, pixel count, iteration guidance, and cost hints.
    If you already have a max_iter in mind, pass it in to get an assessment.
    This tool does not write any files and does not render."""
    baseline_zoom = max(zoom, 1.0)
    span_x = 3.5 / baseline_zoom
    span_y = span_x * height / width
    half_x = span_x / 2.0
    half_y = span_y / 2.0

    real_min = center_real - half_x
    real_max = center_real + half_x
    imag_min = center_imag - half_y
    imag_max = center_imag + half_y

    iters = _viewport_iteration_guidance(zoom, coloring)
    total_pixels = width * height

    result: dict = {
        "viewport": {
            "real_min": real_min,
            "real_max": real_max,
            "imag_min": imag_min,
            "imag_max": imag_max,
            "span_real": span_x,
            "span_imag": span_y,
        },
        "pixels": {
            "width": width,
            "height": height,
            "total": total_pixels,
        },
        "iteration_guidance": iters,
        "cost": _viewport_cost_hint(width, height, iters["recommended_max_iter"]),
    }

    if max_iter is not None:
        result["provided_max_iter"] = max_iter
        result["cost"]["estimated_work_units_at_provided_iter"] = total_pixels * max_iter
        if max_iter < iters["min_reasonable_max_iter"]:
            result["provided_max_iter_assessment"] = "too_low"
        elif max_iter > iters["max_reasonable_max_iter"]:
            result["provided_max_iter_assessment"] = "too_high"
        else:
            result["provided_max_iter_assessment"] = "reasonable"

    return result


def _stable_hash(value: str) -> int:
    return int(hashlib.sha256(value.encode()).hexdigest(), 16) % (2**31)


def run_server() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
