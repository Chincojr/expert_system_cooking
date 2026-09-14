"""ExpertCook - an experta-based cooking expert system.

Query it with a dish and a few parameters (servings, style, spice, protein, ...)
and it generates an ordered, scaled, step-by-step cooking guide.

Public entry point: :func:`expertcook.planner.build_plan`.
"""

from .planner import build_plan  # noqa: F401
from .recipes import DISHES, PARAM_SPECS  # noqa: F401

__all__ = ["build_plan", "DISHES", "PARAM_SPECS"]
