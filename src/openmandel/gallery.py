import json
import math
import re
from pathlib import Path

from PIL import Image

from openmandel.paths import resolve_output_dir

IMAGE_RE = re.compile(r"^(.+)\.png$")


def _safe_read_metadata(meta_path: Path) -> dict | None:
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def generate_gallery(
    input_dir: str | None = None,
    title: str = "openmandel gallery",
    output_path: str | None = None,
    overwrite: bool = True,
) -> dict:
    in_dir = resolve_output_dir(input_dir)
    images_dir = in_dir

    if output_path is None:
        out_path = images_dir / "gallery.html"
    else:
        out_path = Path(output_path).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    for f in sorted(images_dir.iterdir()):
        m = IMAGE_RE.match(f.name)
        if not m:
            continue
        meta_path = f.with_suffix(".json")
        meta = _safe_read_metadata(meta_path) if meta_path.exists() else None
        entries.append((f, meta))

    cards_html = ""
    for img_path, meta in entries:
        rel = img_path.name
        desc = ""
        palette = ""
        center = ""
        zoom = ""
        max_iter = ""
        if meta and "plan" in meta:
            p = meta["plan"]
            palette = p.get("palette", "")
            center = f"({p.get('center_real', '?')}, {p.get('center_imag', '?')})"
            zoom = str(p.get("zoom", ""))
            max_iter = str(p.get("max_iter", ""))
            desc = p.get("description", "") or ""
        details = f"<p><strong>{rel}</strong></p>"
        parts = []
        if palette:
            parts.append(f"palette: {palette}")
        if center:
            parts.append(f"center: {center}")
        if zoom:
            parts.append(f"zoom: {zoom}")
        if max_iter:
            parts.append(f"iter: {max_iter}")
        if parts:
            details += f"<p>{' | '.join(parts)}</p>"
        if desc:
            details += f"<p><em>{desc}</em></p>"
        cards_html += f"""
    <div class="card">
      <a href="{rel}"><img src="{rel}" loading="lazy" alt="{rel}"></a>
      <div class="card-body">{details}</div>
    </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif;
           background: #111; color: #eee; padding: 2rem; }}
  h1 {{ margin-bottom: 1.5rem; font-weight: 300; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
           gap: 1.5rem; }}
  .card {{ background: #1a1a1a; border-radius: 8px; overflow: hidden; }}
  .card img {{ width: 100%; height: auto; display: block; }}
  .card-body {{ padding: 0.75rem; font-size: 0.85rem; line-height: 1.4; }}
  .card-body p {{ margin-bottom: 0.25rem; }}
  a {{ color: inherit; text-decoration: none; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="grid">
{cards_html}
</div>
</body>
</html>"""

    out_path.write_text(html, encoding="utf-8")
    return {
        "gallery_path": str(out_path),
        "image_count": len(entries),
    }


def create_contact_sheet(
    image_paths: list[Path],
    output_path: Path,
    cell_size: tuple[int, int] = (256, 256),
) -> Path:
    count = len(image_paths)
    if count == 0:
        raise ValueError("No images to include in contact sheet")
    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)
    thumb_w, thumb_h = cell_size
    gutter = 4
    sheet_w = cols * thumb_w + (cols - 1) * gutter
    sheet_h = rows * thumb_h + (rows - 1) * gutter
    sheet = Image.new("RGB", (sheet_w, sheet_h), (20, 20, 20))
    for idx, img_path in enumerate(image_paths):
        img = Image.open(img_path)
        img.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = idx % cols
        y = idx // cols
        paste_x = x * (thumb_w + gutter)
        paste_y = y * (thumb_h + gutter)
        cx = paste_x + (thumb_w - img.width) // 2
        cy = paste_y + (thumb_h - img.height) // 2
        sheet.paste(img, (cx, cy))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="PNG")
    return output_path
