# OPENMANDEL_SPEC.md

# openmandel: MCP Server Specification

**Status:** v0.1 implementation specification  
**Project type:** Python MCP server + minimal utility CLI  
**Primary target host:** LM Studio MCP via `mcp.json`  
**Secondary target hosts:** Claude Desktop, Cursor-style MCP clients, MCP Inspector  
**License:** MIT

> **Amendments / Implementation Clarifications**  
> The following clarifications are authoritative v0.1 decisions. If any implementation detail conflicts with the body of this spec, prefer these clarifications.  
> See [§27. Amendments](#27-amendments--implementation-clarifications).  

---

## 1. Project Summary

`openmandel` is a local MCP server that gives AI assistants deterministic Mandelbrot image-generation tools.

The core idea is:

> The client LLM chooses the artistic direction and calls structured MCP tools. `openmandel` validates the requested parameters, renders deterministic Mandelbrot images locally, writes PNG/JSON artifacts, and returns file paths plus metadata.

`openmandel` is not a diffusion model and does not call another LLM internally. It is a deterministic fractal rendering tool exposed through MCP.

---

## 2. Design Principles

1. **MCP-first**
   - The primary product is an MCP stdio server.
   - It should work when added to LM Studio's `mcp.json`.

2. **No second LLM call**
   - `openmandel` must not call OpenAI, Ollama, LM Studio, Claude, or any other model internally in v0.1.
   - The host/client LLM is expected to read the MCP tool descriptions and provide deterministic rendering arguments.

3. **Deterministic rendering**
   - Same explicit arguments and same seed must produce the same image and metadata.
   - Variations use deterministic seed derivation from a base seed and variation index.

4. **Safe local filesystem behavior**
   - By default, all output is written under a known output root.
   - The server must not read arbitrary user files.
   - The server must not write outside the allowed output root unless explicitly enabled by environment variable.

5. **Offline by default**
   - No network access is required for normal operation.
   - No telemetry.
   - No hidden downloads.

6. **Simple renderer first**
   - Use CPU NumPy + Pillow in v0.1.
   - No GPU, no arbitrary precision, no animations in v0.1.

---

## 3. MVP Scope

### 3.1 Must Have

- MCP stdio server using the official Python MCP SDK FastMCP interface.
- Minimal CLI entry point.
- Deterministic Mandelbrot renderer.
- PNG output.
- JSON metadata output next to every generated image.
- Tools:
  - `render_mandelbrot_plan`
  - `create_mandelbrot_variations`
  - `list_mandelbrot_presets`
  - `list_mandelbrot_palettes`
  - `generate_mandelbrot_gallery`
  - `get_openmandel_config`
- Path validation and output sandboxing.
- LM Studio `mcp.json` example.
- Claude Desktop config example.
- Unit tests for schemas, path validation, renderer smoke tests, and variation determinism.

### 3.2 Should Have

- Contact sheet generation for variations.
- Rich metadata including render time, parameters, seed, package version.
- CLI commands for local testing without MCP host.
- Gallery HTML generation.

### 3.3 Non-goals for v0.1

- Internal LLM planner.
- Prompt-to-plan natural language planning inside `openmandel`.
- Vision/image analysis.
- Web UI.
- HTTP MCP server transport.
- Claude `.mcpb` extension bundle.
- Arbitrary precision deep zoom.
- GPU rendering.
- Video/animation generation.
- Reading user files outside generated metadata/images.

---

## 4. Technology Choices

### 4.1 Language

Python 3.11+.

### 4.2 Package/dependency manager

Canonical development workflow uses `uv` and `uvx`, while remaining pip-compatible.

### 4.3 Runtime dependencies

Required dependencies:

```toml
mcp[cli]
numpy
pillow
pydantic
```

Recommended dev dependencies:

```toml
pytest
ruff
mypy
```

### 4.4 MCP SDK

Use the official Python MCP SDK FastMCP import:

```python
from mcp.server.fastmcp import FastMCP
```

### 4.5 Package command

The installed console script should be:

```bash
openmandel
```

Default behavior:

```bash
openmandel
```

starts the MCP stdio server.

Optional explicit behavior:

```bash
openmandel serve
```

also starts the MCP stdio server.

---

## 5. Repository Structure

```text
openmandel/
  README.md
  OPENMANDEL_SPEC.md
  pyproject.toml
  LICENSE
  .gitignore

  src/
    openmandel/
      __init__.py
      __main__.py
      server.py
      cli.py
      schema.py
      render.py
      presets.py
      palettes.py
      gallery.py
      paths.py
      errors.py
      metadata.py

  examples/
    lmstudio_mcp.json
    claude_desktop_config.json
    prompts.md
    plans/
      seahorse_valley_blue.json
      gold_fire_minibrot.json

  tests/
    test_schema.py
    test_paths.py
    test_render.py
    test_variations.py
    test_gallery.py
```

---

## 6. Environment Variables

### 6.1 `OPENMANDEL_OUTPUT_DIR`

Default:

```text
~/Pictures/openmandel
```

Purpose:

- Sets the default output root for generated files.
- Created automatically if it does not exist.

### 6.2 `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS`

Default:

```text
false
```

Allowed truthy values:

```text
1, true, yes, on
```

Purpose:

- If false, requested output paths must resolve inside `OPENMANDEL_OUTPUT_DIR`.
- If true, custom output directories are allowed after path normalization and safety checks.

### 6.3 `OPENMANDEL_MAX_IMAGE_DIMENSION`

Default:

```text
2048
```

Purpose:

- Hard upper bound for width and height.
- The implementation must never allow dimensions above this value.
- If this env var is set above `2048`, cap it to `2048` in v0.1.

### 6.4 `OPENMANDEL_MAX_ITER`

Default:

```text
5000
```

Purpose:

- Hard upper bound for `max_iter`.
- If this env var is set above `5000`, cap it to `5000` in v0.1.

---

## 7. Filesystem Security Model

### 7.1 Output root

By default, generated outputs must be written under:

```text
~/Pictures/openmandel
```

The path should be expanded with `Path.home()` and resolved.

### 7.2 Allowed output paths

If `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS` is false:

- `output_dir` may be omitted.
- If provided, `output_dir` must resolve inside the configured output root.
- `output_path` may be omitted.
- If provided, `output_path` must resolve inside the configured output root.

If `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS` is true:

- Custom output directories are allowed.
- Paths must still be normalized and must not contain unsafe traversal behavior after resolution.
- Parent directories may be created.

### 7.3 Path validation requirements

Implement these functions in `paths.py`:

```python
def get_output_root() -> Path: ...
def arbitrary_output_dirs_allowed() -> bool: ...
def resolve_output_dir(output_dir: str | None) -> Path: ...
def resolve_output_path(output_path: str | None, default_filename: str) -> Path: ...
def ensure_png_suffix(path: Path) -> Path: ...
def slugify_filename(value: str, fallback: str = "mandelbrot") -> str: ...
```

Rules:

- Always expand `~`.
- Always call `.resolve()` before comparisons.
- Use `Path.is_relative_to()` on Python 3.11+ to enforce sandboxing.
- Create directories only after validation.
- Only write `.png`, `.json`, and `.html` files in v0.1.
- Never delete files.
- Never overwrite existing files unless `overwrite=True` is explicitly passed to the tool.
- If a file already exists and `overwrite=False`, append a deterministic or monotonic suffix such as `-001`, `-002`.

---

## 8. Rendering Limits

### 8.1 Image size

- Default width: `1024`
- Default height: `1024`
- Minimum width/height: `128`
- Maximum width/height: `2048`

Reject invalid dimensions with a clear validation error.

### 8.2 Iteration limits

- Default `max_iter`: `1000`
- Minimum `max_iter`: `50`
- Maximum `max_iter`: `5000`

### 8.3 Geometry limits

- `center_real`: `-2.5` to `1.5`
- `center_imag`: `-1.5` to `1.5`
- `zoom`: `1` to `1_000_000_000`

### 8.4 Styling limits

- `contrast`: `0.25` to `4.0`; default `1.0`
- `gamma`: `0.25` to `4.0`; default `1.0`
- `escape_radius`: fixed to `2.0` in v0.1 unless explicitly included later.

---

## 9. Mandelbrot Semantics

### 9.1 Coordinate model

`zoom` controls the visible width of the complex plane.

Define:

```python
base_span = 3.5
span_x = base_span / zoom
span_y = span_x * height / width
```

For each pixel, map to:

```python
real = center_real + (x - width / 2) * span_x / width
imag = center_imag + (y - height / 2) * span_y / height
```

### 9.2 Iteration

Compute:

```python
z = 0
c = real + imag*i
z = z*z + c
```

A point escapes if:

```python
abs(z) > 2.0
```

### 9.3 Coloring modes

Implement two coloring modes in v0.1:

1. `escape_time`
   - Color based on integer escape iteration.

2. `smooth`
   - Use normalized smooth iteration count when possible.
   - For escaped points, use:

```python
smooth_iter = n + 1 - log(log(abs(z))) / log(2)
```

Guard against invalid logs and divide-by-zero.

### 9.4 Interior points

Points that do not escape by `max_iter` are considered inside the set.

Interior color behavior:

- Default background/interior is black.
- The `background` field may support named colors in v0.1, but black should be the default and most stable.

---

## 10. Palettes

Implement `palettes.py` with a registry of named palettes.

Required palette names:

```text
classic
inferno
magma
viridis
electric_blue
neon_purple
gold_fire
ice
toxic_green
rose_gold
monochrome
```

Each palette must include:

- `name`
- `description`
- `vibes`: list of keywords useful to the client LLM
- gradient stops as RGB triples

Example model:

```python
class PaletteInfo(BaseModel):
    name: str
    description: str
    vibes: list[str]
    colors: list[tuple[int, int, int]]
```

Color interpolation:

- Input normalized value in `[0, 1]`.
- Apply contrast and gamma before color lookup.
- Interpolate linearly between gradient stops.

---

## 11. Presets

Implement `presets.py` with curated Mandelbrot regions. These are meant for the host LLM to inspect through `list_mandelbrot_presets` and then use as deterministic arguments in `render_mandelbrot_plan`.

Required presets:

```text
full_set
seahorse_valley
elephant_valley
mini_mandelbrot
triple_spiral
antenna_tip
lightning_filaments
spiral_galaxy
```

Each preset must include:

- `name`
- `description`
- `center_real`
- `center_imag`
- `recommended_zoom`
- `recommended_max_iter`
- `vibes`
- `suggested_palettes`

Suggested values:

```python
PRESETS = [
    {
        "name": "full_set",
        "description": "The iconic full Mandelbrot set silhouette.",
        "center_real": -0.5,
        "center_imag": 0.0,
        "recommended_zoom": 1,
        "recommended_max_iter": 500,
        "vibes": ["classic", "iconic", "simple", "educational"],
        "suggested_palettes": ["classic", "magma", "monochrome"],
    },
    {
        "name": "seahorse_valley",
        "description": "Classic deep-zoom spiral structures near Seahorse Valley.",
        "center_real": -0.743643887037151,
        "center_imag": 0.13182590420533,
        "recommended_zoom": 100000,
        "recommended_max_iter": 1200,
        "vibes": ["spiral", "intricate", "cosmic", "cathedral", "deep zoom"],
        "suggested_palettes": ["electric_blue", "ice", "neon_purple"],
    },
    {
        "name": "elephant_valley",
        "description": "Organic bulb-like and coral-like structures.",
        "center_real": 0.275,
        "center_imag": 0.0,
        "recommended_zoom": 80,
        "recommended_max_iter": 800,
        "vibes": ["organic", "coral", "rounded", "alien", "reef"],
        "suggested_palettes": ["rose_gold", "toxic_green", "magma"],
    },
    {
        "name": "mini_mandelbrot",
        "description": "Nested Mandelbrot-like structures showing recursion.",
        "center_real": -1.749,
        "center_imag": 0.0,
        "recommended_zoom": 12000,
        "recommended_max_iter": 1500,
        "vibes": ["nested", "recursive", "symbolic", "mirrored"],
        "suggested_palettes": ["gold_fire", "classic", "inferno"],
    },
    {
        "name": "triple_spiral",
        "description": "Energetic spiral-heavy region with radial motion.",
        "center_real": -0.088,
        "center_imag": 0.654,
        "recommended_zoom": 3000,
        "recommended_max_iter": 1200,
        "vibes": ["spiral", "galaxy", "radial", "energetic"],
        "suggested_palettes": ["electric_blue", "neon_purple", "gold_fire"],
    },
    {
        "name": "antenna_tip",
        "description": "Sparse, stark details near the left antenna of the Mandelbrot set.",
        "center_real": -1.999,
        "center_imag": 0.0,
        "recommended_zoom": 250,
        "recommended_max_iter": 1000,
        "vibes": ["minimal", "needle", "dark", "stark"],
        "suggested_palettes": ["monochrome", "ice", "classic"],
    },
    {
        "name": "lightning_filaments",
        "description": "Thin high-contrast boundary filaments suitable for lightning-like renders.",
        "center_real": -0.77568377,
        "center_imag": 0.13646737,
        "recommended_zoom": 60000,
        "recommended_max_iter": 1600,
        "vibes": ["lightning", "filament", "electric", "sharp", "storm"],
        "suggested_palettes": ["electric_blue", "ice", "toxic_green"],
    },
    {
        "name": "spiral_galaxy",
        "description": "A rich spiral region suitable for galaxy-like compositions.",
        "center_real": -0.761574,
        "center_imag": -0.0847596,
        "recommended_zoom": 8000,
        "recommended_max_iter": 1200,
        "vibes": ["galaxy", "spiral", "nebula", "cosmic"],
        "suggested_palettes": ["neon_purple", "electric_blue", "magma"],
    },
]
```

---

## 12. Pydantic Schemas

Implement schemas in `schema.py`.

### 12.1 Enums / Literal types

```python
PaletteName = Literal[
    "classic",
    "inferno",
    "magma",
    "viridis",
    "electric_blue",
    "neon_purple",
    "gold_fire",
    "ice",
    "toxic_green",
    "rose_gold",
    "monochrome",
]

ColoringMode = Literal["escape_time", "smooth"]
```

### 12.2 `MandelbrotPlan`

```python
class MandelbrotPlan(BaseModel):
    center_real: float = Field(..., ge=-2.5, le=1.5)
    center_imag: float = Field(..., ge=-1.5, le=1.5)
    zoom: float = Field(..., ge=1, le=1_000_000_000)
    max_iter: int = Field(1000, ge=50, le=5000)
    width: int = Field(1024, ge=128, le=2048)
    height: int = Field(1024, ge=128, le=2048)
    palette: PaletteName = "electric_blue"
    coloring: ColoringMode = "smooth"
    background: str = "black"
    contrast: float = Field(1.0, ge=0.25, le=4.0)
    gamma: float = Field(1.0, ge=0.25, le=4.0)
    seed: int | None = None
    description: str | None = None
```

### 12.3 `RenderResult`

```python
class RenderResult(BaseModel):
    image_path: str
    metadata_path: str
    plan: MandelbrotPlan
    width: int
    height: int
    elapsed_ms: float
    seed: int
    overwritten: bool = False
```

### 12.4 `VariationResult`

```python
class VariationResult(BaseModel):
    images: list[RenderResult]
    contact_sheet_path: str | None = None
    output_dir: str
    base_seed: int
```

### 12.5 `PresetInfo`

```python
class PresetInfo(BaseModel):
    name: str
    description: str
    center_real: float
    center_imag: float
    recommended_zoom: float
    recommended_max_iter: int
    vibes: list[str]
    suggested_palettes: list[str]
```

---

## 13. MCP Tools

All MCP tool docstrings must be written as instructions to the host LLM. They must clearly explain when to use the tool and what each argument means.

### 13.1 `render_mandelbrot_plan`

Purpose:

- Render one deterministic Mandelbrot image from exact parameters chosen by the host LLM.
- This is the primary tool.

Signature:

```python
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
) -> dict:
    ...
```

Required docstring content:

```text
Render a deterministic Mandelbrot image from explicit fractal parameters.
Use this when you know the region, zoom, palette, and style you want.
Call list_mandelbrot_presets first if you need good known coordinates.
Call list_mandelbrot_palettes first if you need valid palette names.

Coordinate guidance:
- Use seahorse_valley-like coordinates for spirals/cathedrals/deep intricate prompts.
- Use elephant_valley-like coordinates for organic/coral/alien reef prompts.
- Use mini_mandelbrot-like coordinates for nested/recursive/symbolic prompts.
- Use antenna_tip-like coordinates for minimal/stark/needle-like prompts.

Returns paths to the PNG image and JSON metadata. Does not return embedded image bytes.
```

Behavior:

1. Validate input with `MandelbrotPlan`.
2. Validate output path.
3. Render image.
4. Save PNG.
5. Save metadata JSON next to PNG.
6. Return `RenderResult` as plain JSON-serializable dict.

Metadata filename:

```text
same basename as PNG + .json
```

Example:

```text
seahorse-blue.png
seahorse-blue.json
```

### 13.2 `create_mandelbrot_variations`

Purpose:

- Generate multiple deterministic variations from a base plan.
- The host LLM provides the base coordinates and style.
- The server applies small deterministic parameter perturbations based on seed and index.

Signature:

```python
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
) -> dict:
    ...
```

Validation:

- `count`: minimum `1`, maximum `8`.
- Uses the same image and iteration limits as `render_mandelbrot_plan`.

Variation algorithm:

- If `seed` is None, derive a stable seed from a canonical serialization of the base plan.
- For each `i` in `0..count-1`:
  - `variation_seed = stable_hash(f"{base_seed}:{i}")`
  - Apply tiny deterministic offsets to center:
    - offset scale should be proportional to visible span.
    - Never move so far that the render leaves the intended neighborhood.
  - Apply zoom multiplier in approximately `[0.75, 1.35]`.
  - Optionally adjust contrast/gamma slightly within limits.
- Save files as:

```text
{basename}-001.png
{basename}-001.json
{basename}-002.png
{basename}-002.json
...
```

Contact sheet:

- If `make_contact_sheet=True`, create `{basename}-contact-sheet.png`.
- Contact sheet should arrange images in a grid.
- Include no text labels in v0.1 unless simple and reliable.

### 13.3 `list_mandelbrot_presets`

Purpose:

- Return known Mandelbrot regions and guidance so the host LLM can choose good deterministic render arguments.

Signature:

```python
@mcp.tool()
def list_mandelbrot_presets() -> list[dict]:
    ...
```

Behavior:

- Return all presets from `presets.py`.
- Do not render anything.
- Do not write files.

### 13.4 `list_mandelbrot_palettes`

Purpose:

- Return valid palette names and style guidance.

Signature:

```python
@mcp.tool()
def list_mandelbrot_palettes() -> list[dict]:
    ...
```

Behavior:

- Return all palettes from `palettes.py`, excluding raw color arrays if too verbose.
- Include `name`, `description`, and `vibes`.

### 13.5 `generate_mandelbrot_gallery`

Purpose:

- Generate a local static HTML gallery from generated PNG/JSON files.

Signature:

```python
@mcp.tool()
def generate_mandelbrot_gallery(
    input_dir: str | None = None,
    title: str = "openmandel gallery",
    output_path: str | None = None,
    overwrite: bool = True,
) -> dict:
    ...
```

Behavior:

- Validate `input_dir` and `output_path` using the same filesystem security model.
- Scan for `.png` files with matching `.json` metadata.
- Create `gallery.html` by default in `input_dir`.
- Use relative paths in HTML when possible.
- Return:

```json
{
  "gallery_path": "...",
  "image_count": 4
}
```

### 13.6 `get_openmandel_config`

Purpose:

- Help the user/client understand current server limits and output directory behavior.

Signature:

```python
@mcp.tool()
def get_openmandel_config() -> dict:
    ...
```

Return:

```json
{
  "output_root": "~/Pictures/openmandel resolved path",
  "arbitrary_output_dirs_allowed": false,
  "max_image_dimension": 2048,
  "max_iter": 5000,
  "supported_palettes": [...],
  "supported_coloring_modes": ["escape_time", "smooth"]
}
```

---

## 14. Metadata Format

Every PNG must have a JSON metadata file next to it.

Example:

```json
{
  "schema_version": "0.1",
  "generator": "openmandel",
  "openmandel_version": "0.1.0",
  "created_at": "2026-05-31T01:25:00-04:00",
  "image_path": "/Users/example/Pictures/openmandel/seahorse-blue.png",
  "plan": {
    "center_real": -0.743643887037151,
    "center_imag": 0.13182590420533,
    "zoom": 100000,
    "max_iter": 1200,
    "width": 1024,
    "height": 1024,
    "palette": "electric_blue",
    "coloring": "smooth",
    "background": "black",
    "contrast": 1.2,
    "gamma": 0.9,
    "seed": 12345,
    "description": "Blue spiral deep zoom in Seahorse Valley."
  },
  "elapsed_ms": 842.1
}
```

---

## 15. Minimal CLI

Implement `cli.py` using either `argparse` or a minimal dependency-free approach. Avoid adding `typer` unless needed.

Required commands:

### 15.1 Serve MCP

```bash
openmandel
openmandel serve
```

Starts MCP stdio server.

### 15.2 Render from plan JSON

```bash
openmandel render examples/plans/seahorse_valley_blue.json
```

Behavior:

- Loads a JSON object matching `MandelbrotPlan`.
- Renders an image.
- Prints output paths.

### 15.3 List presets

```bash
openmandel presets
```

### 15.4 List palettes

```bash
openmandel palettes
```

### 15.5 Generate gallery

```bash
openmandel gallery ~/Pictures/openmandel
```

---

## 16. LM Studio Configuration

Create `examples/lmstudio_mcp.json`:

```json
{
  "mcpServers": {
    "openmandel": {
      "command": "uvx",
      "args": ["openmandel"],
      "env": {
        "OPENMANDEL_OUTPUT_DIR": "~/Pictures/openmandel"
      }
    }
  }
}
```

For local development, document this variant:

```json
{
  "mcpServers": {
    "openmandel-dev": {
      "command": "uv",
      "args": ["run", "openmandel"],
      "env": {
        "OPENMANDEL_OUTPUT_DIR": "~/Pictures/openmandel"
      }
    }
  }
}
```

Important LM Studio README note:

- In LM Studio, open the Program tab.
- Click Install / Edit `mcp.json`.
- Add the `openmandel` entry under `mcpServers`.
- Restart or refresh tools if needed.
- Use a model with decent tool-calling ability.

---

## 17. Claude Desktop Configuration

Create `examples/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "openmandel": {
      "command": "uvx",
      "args": ["openmandel"],
      "env": {
        "OPENMANDEL_OUTPUT_DIR": "~/Pictures/openmandel"
      }
    }
  }
}
```

Local development variant:

```json
{
  "mcpServers": {
    "openmandel-dev": {
      "command": "uv",
      "args": ["run", "openmandel"],
      "env": {
        "OPENMANDEL_OUTPUT_DIR": "~/Pictures/openmandel"
      }
    }
  }
}
```

---

## 18. Example Host Prompts

Put these in `examples/prompts.md`.

```text
Use openmandel to list the available Mandelbrot presets and palettes. Then render a 1024x1024 icy blue spiral image using a good preset for intricate spirals.
```

```text
Use openmandel to create four Mandelbrot variations that look like molten gold recursive suns in a black void. Use a nested or recursive preset if available, and create a contact sheet.
```

```text
Use openmandel to generate a stark monochrome Mandelbrot image near a minimal antenna-like region. Keep the composition dark and high contrast.
```

```text
Use openmandel to create a gallery from the images generated today.
```

---

## 19. Example Plan JSON

Create `examples/plans/seahorse_valley_blue.json`:

```json
{
  "center_real": -0.743643887037151,
  "center_imag": 0.13182590420533,
  "zoom": 100000,
  "max_iter": 1200,
  "width": 1024,
  "height": 1024,
  "palette": "electric_blue",
  "coloring": "smooth",
  "background": "black",
  "contrast": 1.2,
  "gamma": 0.9,
  "seed": 12345,
  "description": "Blue spiral deep zoom in Seahorse Valley."
}
```

---

## 20. Testing Requirements

### 20.1 Schema tests

`tests/test_schema.py`:

- Valid plan passes.
- Invalid palette fails.
- Invalid coloring mode fails.
- Width > 2048 fails.
- Height > 2048 fails.
- `max_iter > 5000` fails.
- Coordinate out of range fails.

### 20.2 Path tests

`tests/test_paths.py`:

- Default output root resolves.
- `~` expands.
- Output directory inside root passes.
- Output directory outside root fails when arbitrary dirs disabled.
- Output directory outside root passes when arbitrary dirs enabled.
- Path traversal attempts fail.
- Existing file gets suffix if `overwrite=False`.

### 20.3 Renderer tests

`tests/test_render.py`:

- Render 128x128 smoke test.
- Output image exists.
- Output image is valid PNG.
- Metadata exists.
- Same plan + same seed creates byte-identical or metadata-identical deterministic output.

If byte-identical image tests are fragile across platforms, use stable metadata and basic image hash tolerance.

### 20.4 Variation tests

`tests/test_variations.py`:

- Count 4 produces 4 images.
- Same base plan + same seed produces same variation plans.
- Count > 8 fails.
- Contact sheet is produced when requested.

### 20.5 Gallery tests

`tests/test_gallery.py`:

- Gallery HTML is created.
- Gallery includes generated image filenames.
- Empty directory produces valid gallery with zero images or a clear message.

---

## 21. Acceptance Criteria for v0.1

A coding agent is done with v0.1 when all of the following are true:

1. `uv run openmandel` starts an MCP stdio server without crashing.
2. LM Studio can load the server from `mcp.json`.
3. `list_mandelbrot_presets` returns the required presets.
4. `list_mandelbrot_palettes` returns the required palettes.
5. `render_mandelbrot_plan` creates a PNG and JSON metadata file.
6. `create_mandelbrot_variations` creates multiple PNGs and a contact sheet.
7. `generate_mandelbrot_gallery` creates `gallery.html`.
8. Default output goes to `~/Pictures/openmandel` or env override.
9. The server does not write outside the output root unless `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS=true`.
10. Width/height above `2048` are rejected.
11. `max_iter` above `5000` is rejected.
12. Tests pass with `uv run pytest`.
13. `ruff` passes or issues are intentionally documented.
14. README contains install, LM Studio config, examples, and security notes.

---

## 22. README Requirements

The README must include:

1. One-sentence pitch:

```text
openmandel is an MCP server that gives AI assistants deterministic Mandelbrot image-generation tools.
```

2. Install instructions:

```bash
uvx openmandel
```

and local dev:

```bash
git clone <repo-url>
cd openmandel
uv sync
uv run openmandel
```

3. LM Studio setup with `mcp.json`.
4. Claude Desktop setup.
5. Example prompts.
6. Tool list.
7. Output/security model.
8. Screenshots or generated sample images once available.
9. License.

---

## 23. Implementation Order for Coding Agents

Follow this order exactly:

1. Create `pyproject.toml`, package skeleton, MIT license, empty tests.
2. Implement schemas in `schema.py`.
3. Implement path security in `paths.py`.
4. Implement palettes in `palettes.py`.
5. Implement presets in `presets.py`.
6. Implement renderer in `render.py`.
7. Implement metadata writing in `metadata.py`.
8. Implement gallery and contact sheet in `gallery.py`.
9. Implement MCP server tools in `server.py`.
10. Implement minimal CLI in `cli.py` and `__main__.py`.
11. Add examples.
12. Add tests.
13. Write README.
14. Run tests and fix issues.
15. Manually test in LM Studio.

---

## 24. Manual LM Studio Test Script

After implementation:

1. Open LM Studio.
2. Load a local model with tool-calling ability.
3. Open Program tab.
4. Edit `mcp.json`.
5. Add local dev config:

```json
{
  "mcpServers": {
    "openmandel-dev": {
      "command": "uv",
      "args": ["run", "openmandel"],
      "env": {
        "OPENMANDEL_OUTPUT_DIR": "~/Pictures/openmandel"
      }
    }
  }
}
```

6. Ask:

```text
Use openmandel to list Mandelbrot presets and palettes, then render a 1024x1024 icy blue spiral image. Save it in the default output directory.
```

Expected:

- The model calls `list_mandelbrot_presets`.
- The model calls `list_mandelbrot_palettes`.
- The model calls `render_mandelbrot_plan`.
- A PNG and JSON file appear under `~/Pictures/openmandel`.
- The chat response includes the output paths.

---

## 25. Roadmap After v0.1

### v0.2

- Streamable HTTP transport.
- More coloring algorithms.
- More presets.
- Optional embedded image content in MCP responses.
- Claude Desktop `.mcpb` package.

### v0.3

- Arbitrary precision deep zoom.
- GPU or Numba acceleration.
- Animation/video zoom generation.
- Benchmark mode for local LLM tool-calling quality.

### v0.4

- Optional local LLM planner mode as a separate tool, not default behavior.
- Web gallery UI.
- Import/export curated prompt packs.

---

## 26. Hard Rules for Agents

- Do not add an internal LLM dependency in v0.1.
- Do not add network calls.
- Do not silently write outside the output root.
- Do not increase max image dimension above 2048.
- Do not increase max iterations above 5000.
- Do not skip metadata JSON generation.
- Do not remove deterministic seed behavior.
- Do not make the CLI the primary product; MCP server is primary.
- Keep tool docstrings descriptive because the host LLM depends on them.

---

## 27. Amendments / Implementation Clarifications

The following are authoritative v0.1 decisions resolving ambiguities found during pre-implementation review.

### 27.1 Default filename when `output_path` is `None`

For `render_mandelbrot_plan`:

- If `description` is provided and non-empty, slugify the first ~60 chars.
- Else use a deterministic name derived from the plan.

Format:

```text
{slug}-{short_hash}.png
```

Where:

- `slug` comes from `description` or fallback `"mandelbrot"`
- `short_hash` is the first 8 hex chars of a stable SHA-256 hash of the canonical plan JSON
- Canonical plan JSON means sorted keys, excluding output path fields

Examples:

```text
blue-spiral-deep-zoom-a13f92c0.png
mandelbrot-91de88ab.png
```

For `create_mandelbrot_variations`:

- If `basename` is provided, slugify it.
- Else if `description` is provided, use that.
- Else use `mandelbrot-variations-{short_hash}`.

Files:

```text
{basename}-001.png
{basename}-001.json
{basename}-002.png
{basename}-002.json
...
{basename}-contact-sheet.png
```

### 27.2 Seed behavior when `seed=None`

Use deterministic seed derivation everywhere.

For `render_mandelbrot_plan`:

- If `seed` is provided, use it.
- If `seed=None`, derive:

```text
seed = int(SHA-256(canonical plan JSON)[:16], 16) % 2**31
```

Exclude the `seed` field itself and filesystem/output fields from the canonical JSON when deriving.

For `create_mandelbrot_variations`:

- If base `seed` is provided, use it as `base_seed`.
- Else derive `base_seed` from canonical base plan JSON using the same method.
- Each variation: `variation_seed = stable_hash(f"{base_seed}:{index}")`

### 27.3 Concurrent write safety

Implement a helper:

```python
def reserve_available_path(path: Path, overwrite: bool = False) -> Path
```

Behavior:

- If `overwrite=True`, return the requested path.
- If `overwrite=False` and path does not exist, return it.
- If it exists, try suffixes `-001`, `-002`, etc.
- Use exclusive creation (or save-to-temp + rename) where possible.
- Same suffix behavior applies to metadata JSON.
- Never delete existing files.

### 27.4 Gallery HTML styling

- Single self-contained `gallery.html`
- No external JS/CSS dependencies
- Responsive CSS grid
- Each card shows: image, filename, palette, center, zoom, max_iter, optional description
- Use relative image paths where possible

### 27.5 Ruff / mypy config

- `ruff check .` must pass.
- `pytest` must pass.
- `mypy` config can exist but is not a hard blocker for v0.1.
- Reasonable Python 3.11 settings in `pyproject.toml`.

### 27.6 Contact sheet grid layout

```python
cols = ceil(sqrt(count))
rows = ceil(count / cols)
```

- 1→1×1, 2→2×1, 3→2×2, 4→2×2, 5→3×2, 7→3×3, 8→3×3
- Generated images resized to thumbnails, aspect ratio preserved
- Small padding/gutter, dark or neutral background
- No text labels in v0.1
