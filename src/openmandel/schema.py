import hashlib
import json
from typing import Literal

from pydantic import BaseModel, Field

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

    def canonical_json(self) -> str:
        excluded = {"seed", "description"}
        data = self.model_dump(mode="json", exclude=excluded)
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    def derive_seed(self) -> int:
        canonical = self.canonical_json()
        h = hashlib.sha256(canonical.encode()).hexdigest()
        return int(h, 16) % (2**31)


class RenderResult(BaseModel):
    image_path: str
    metadata_path: str
    plan: MandelbrotPlan
    width: int
    height: int
    elapsed_ms: float
    seed: int
    overwritten: bool = False


class VariationResult(BaseModel):
    images: list[RenderResult]
    contact_sheet_path: str | None = None
    output_dir: str
    base_seed: int


class PresetInfo(BaseModel):
    name: str
    description: str
    center_real: float
    center_imag: float
    recommended_zoom: float
    recommended_max_iter: int
    vibes: list[str]
    suggested_palettes: list[str]


class PaletteInfo(BaseModel):
    name: str
    description: str
    vibes: list[str]
    colors: list[tuple[int, int, int]]
