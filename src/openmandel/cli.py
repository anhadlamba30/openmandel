import argparse
import json
import sys

from openmandel import __version__
from openmandel.gallery import generate_gallery
from openmandel.palettes import PALETTES
from openmandel.presets import PRESETS
from openmandel.render import render_plan
from openmandel.schema import MandelbrotPlan


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="openmandel",
        description="MCP server for deterministic Mandelbrot image generation",
    )
    parser.add_argument(
        "--version", action="version", version=f"openmandel {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("serve", help="Start MCP stdio server")

    render_parser = sub.add_parser("render", help="Render from a plan JSON file")
    render_parser.add_argument("plan_file", help="Path to MandelbrotPlan JSON file")
    render_parser.add_argument(
        "--output", "-o", default=None, help="Output PNG path"
    )
    render_parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing file"
    )

    sub.add_parser("presets", help="List available presets")

    sub.add_parser("palettes", help="List available palettes")

    gallery_parser = sub.add_parser(
        "gallery", help="Generate HTML gallery from rendered images"
    )
    gallery_parser.add_argument(
        "input_dir", nargs="?", default=None, help="Directory with PNG/JSON files"
    )
    gallery_parser.add_argument(
        "--output", "-o", default=None, help="Output HTML path"
    )
    gallery_parser.add_argument("--title", default="openmandel gallery")

    args = parser.parse_args()

    if args.command is None or args.command == "serve":
        from openmandel.server import run_server
        run_server()
    elif args.command == "render":
        with open(args.plan_file) as f:
            data = json.load(f)
        plan = MandelbrotPlan(**data)
        result = render_plan(
            plan,
            output_path=args.output,
            overwrite=args.overwrite,
        )
        print(json.dumps(result.model_dump(mode="json"), indent=2))
    elif args.command == "presets":
        for p in PRESETS:
            print(f"{p.name}: {p.description}")
    elif args.command == "palettes":
        for p in PALETTES:
            print(f"{p.name}: {p.description}")
    elif args.command == "gallery":
        result = generate_gallery(
            input_dir=args.input_dir,
            title=args.title,
            output_path=args.output,
            overwrite=True,
        )
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
