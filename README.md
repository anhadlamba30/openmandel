# openmandel

openmandel is an MCP server that gives AI assistants deterministic Mandelbrot image-generation tools.

| | |
|:---:|:---:|
| ![Seahorse Valley in electric blue](https://raw.githubusercontent.com/anhadlamba30/openmandel/main/examples/images/seahorse-valley-blue.png)<br/>*Seahorse Valley deep zoom, electric blue, smooth coloring* | ![Boundary region in viridis](https://raw.githubusercontent.com/anhadlamba30/openmandel/main/examples/images/c5-boundary-viridis.png)<br/>*Boundary region, viridis, escape-time coloring* |
| ![Triple spiral in inferno](https://raw.githubusercontent.com/anhadlamba30/openmandel/main/examples/images/z9-triple.png)<br/>*Triple spiral, inferno, smooth coloring* | ![Elephant Valley in gold fire](https://raw.githubusercontent.com/anhadlamba30/openmandel/main/examples/images/elephant-valley-gold.png)<br/>*Elephant Valley organic coral, gold fire, smooth coloring* |

## Install from source

```bash
pip install openmandel
# or
uvx openmandel
```

## LM Studio setup

Add to `mcp.json`:

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

If LM Studio cannot find `uvx`, run `which uvx` and use the absolute path as `command`.

## Claude Desktop setup

Same setup in `claude_desktop_config.json`:

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

## Tools

| Tool | Description |
|------|-------------|
| `render_mandelbrot_plan` | Render one deterministic Mandelbrot image from explicit parameters (use `return_base64` for inline display) |
| `create_mandelbrot_variations` | Generate multiple deterministic variations with perturbations (use `return_base64` for inline display) |
| `inspect_mandelbrot_viewport` | Preview viewport bounds, iteration guidance, and cost before rendering |
| `list_mandelbrot_presets` | List known Mandelbrot region presets with coordinates |
| `list_mandelbrot_palettes` | List valid palette names with style guidance |
| `generate_mandelbrot_gallery` | Generate a static HTML gallery from generated images |
| `get_openmandel_config` | Show current server limits and output directory settings |

## CLI

```bash
openmandel          # Start MCP stdio server
openmandel serve    # Same
openmandel render plan.json    # Render from JSON plan file
openmandel presets             # List presets
openmandel palettes            # List palettes
openmandel gallery ~/Pictures/openmandel  # Generate gallery HTML
```

## Example prompts

> Use openmandel to inspect the seahorse_valley viewport at zoom 100000 and 1024x1024. Use the returned iteration guidance to choose a max_iter. Then render the image with electric_blue palette and smooth coloring.

> Use openmandel to list the available Mandelbrot presets and palettes. Then render a 1024x1024 icy blue spiral image using a good preset for intricate spirals.

> Use openmandel to create four Mandelbrot variations that look like molten gold recursive suns in a black void. Use a nested or recursive preset if available, and create a contact sheet.

## Output and security

- All output is written under `~/Pictures/openmandel` (configurable via `OPENMANDEL_OUTPUT_DIR`).
- The server will not write outside the output root unless `OPENMANDEL_ALLOW_ARBITRARY_OUTPUT_DIRS=true`.
- No network access required for normal operation. No telemetry.

## License

MIT
