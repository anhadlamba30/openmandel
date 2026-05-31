import datetime

from openmandel import __version__
from openmandel.schema import MandelbrotPlan


def build_metadata(
    image_path: str,
    plan: MandelbrotPlan,
    elapsed_ms: float,
    seed: int,
) -> dict:
    plan_data = plan.model_dump(mode="json")
    plan_data["seed"] = seed
    return {
        "schema_version": "0.1",
        "generator": "openmandel",
        "openmandel_version": __version__,
        "created_at": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(timespec="seconds"),
        "image_path": image_path,
        "plan": plan_data,
        "elapsed_ms": round(elapsed_ms, 1),
    }
