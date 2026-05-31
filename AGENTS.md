# AGENTS.md

Python MCP server for deterministic Mandelbrot image generation.

## Toolchain

| Command | Action |
|---|---|
| `uv sync` | Install all deps (prod + dev) |
| `uv run openmandel` | Start MCP stdio server |
| `uv run openmandel serve` | Same |
| `uv run openmandel render plan.json` | Render from plan file |
| `uv run openmandel presets` | List presets |
| `uv run openmandel palettes` | List palettes |
| `uv run python -m pytest` | Run all tests |
| `uv run pytest tests/foo.py -xvs` | Focused test |

Lint: `uv run ruff check src/ tests/` (line-length=100, select E,F,I,N,W).  
Typecheck: `uv run mypy src/` (not strict, `ignore_missing_imports = true`).

No CI, no pre-commit, no Makefile.

## Project structure

```
src/openmandel/
├── cli.py        # argparse entrypoint (openmandel.cli:main)
├── server.py     # FastMCP tools (primary interface)
├── render.py     # numpy-based fractal computation + PIL output
├── schema.py     # Pydantic models: MandelbrotPlan, RenderResult, etc.
├── paths.py      # Output root / security boundary logic
├── palettes.py   # Color palette definitions
├── presets.py    # Named coordinate presets
├── gallery.py    # HTML gallery + contact sheet generation
├── metadata.py   # JSON metadata builder
└── errors.py     # OpenmandelError hierarchy
```

## Key constraints

- **Determinism is a core property.** Same seed + same params must produce identical pixels and metadata. `MandelbrotPlan.derive_seed()` hashes the canonical JSON (excluding `seed`/`description`).
- **Security boundary.** Output defaults to `~/Pictures/openmandel`. The server rejects paths outside the root unless `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS=true`.
- **No network calls, no telemetry, no second LLM call.**
- **Env vars:** `OPENMANDEL_OUTPUT_DIR`, `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS`, `OPENMANDEL_MAX_IMAGE_DIMENSION` (cap 2048), `OPENMANDEL_MAX_ITER` (cap 5000).

## Testing

- All tests use `monkeypatch.setenv("OPENMANDEL_OUTPUT_DIR", str(tmp_path))` — **never forget this** or tests write to `~/Pictures/openmandel`.
- No external services, fixtures are tiny (128x128 renders are fast).
- Test validation: schema validation (pydantic), deterministic output (byte-identical PNGs), path security, variations, gallery generation.

## Conventions

- **No docstrings on tool functions** — the function docstring *is* the MCP tool description shown to the AI client. Keep them concise and user-facing.
- Imports: stdlib, then third-party, then `openmandel.*`.
- No code generation, no migrations, no build artifacts to commit.
