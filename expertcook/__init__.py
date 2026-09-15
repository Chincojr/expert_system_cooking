"""ExpertCook - an experta-based cooking expert system.

Query it with a dish and a few parameters (rice quantity, rice type, style,
spice, protein, ...) and it generates an ordered, rice-relative, step-by-step
cooking guide.

RICE IS THE BASE INGREDIENT: every other ingredient quantity is derived from
the rice via the independent proportionality rules in ``proportions.json``,
which can be edited like any dict/JSON without touching code.

Public entry point: :func:`expertcook.planner.build_plan`.
"""

# Experta 1.9.4 requires frozendict 1.2, whose Mapping import predates Python
# 3.10. Restore that alias before importing Experta instead of installing an
# incompatible dependency version or modifying third-party packages on disk.
import collections
import collections.abc

if not hasattr(collections, "Mapping"):
    collections.Mapping = collections.abc.Mapping

from .planner import build_plan  # noqa: F401,E402
from .recipes import DISHES, PARAM_SPECS  # noqa: F401
from . import proportions  # noqa: F401

__all__ = ["build_plan", "DISHES", "PARAM_SPECS", "proportions"]
