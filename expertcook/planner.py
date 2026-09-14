"""High-level entry point: turn a dish + query parameters into a cooking guide.

``build_plan(dish, params)`` validates the parameters, computes the scaled
quantities and special-rule values, runs the matching experta engine, and
returns an ordered, ready-to-display plan.
"""

from . import scaling
from .recipes import DISHES, PARAM_SPECS, get_recipe
from .facts import Flag, Step
from .engines import ENGINES


def _validate(dish, params):
    """Coerce/validate raw params against PARAM_SPECS, filling in defaults."""
    specs = PARAM_SPECS[dish]
    clean = {}
    for spec in specs:
        name = spec["name"]
        val = params.get(name, spec.get("default"))
        if val is None or val == "":
            val = spec.get("default")
        if spec["type"] == "int":
            try:
                val = int(val)
            except (TypeError, ValueError):
                raise ValueError("%s must be a whole number." % spec["label"])
            lo = spec.get("min", 1)
            if val < lo:
                raise ValueError("%s must be at least %d." % (spec["label"], lo))
        elif spec["type"] == "choice":
            if val not in spec["choices"]:
                raise ValueError("%s must be one of: %s."
                                 % (spec["label"], ", ".join(spec["choices"])))
        clean[name] = val
    return clean


def _calc_jollof(p):
    r = get_recipe("jollof")
    ref = r["reference_servings"]
    factor = scaling.scaling_factor(p["servings"], ref)
    ing = {name: (scaling.scale_ingredient(qty, kind, factor), unit)
           for name, (qty, unit, kind) in r["proportional"].items()}
    rice_cups = ing["rice"][0]
    protein = p["protein"]
    return {
        "dish": r["name"], "ref": ref, "servings": p["servings"], "factor": factor,
        "ing": ing,
        "spice": p["spice"],
        "scotch_bonnet": scaling.scotch_bonnet_count(
            p["spice"], factor, r["scotch_bonnet_by_spice"]),
        "protein": protein,
        "protein_g": 0 if protein == "none"
                     else scaling.round_grams(r["protein_reference_g"] * factor),
        "liquid_cups": scaling.cooking_liquid_cups(rice_cups, r["liquid_to_rice_ratio"]),
        "style": p["style"],
        "pot_capacity": p["pot_capacity"],
        "pot_batches": scaling.pot_batches(p["servings"], p["pot_capacity"]),
    }


def _calc_fried(p):
    r = get_recipe("fried_rice")
    ref = r["reference_servings"]
    factor = scaling.scaling_factor(p["servings"], ref)
    ing = {name: (scaling.scale_ingredient(qty, kind, factor), unit)
           for name, (qty, unit, kind) in r["proportional"].items()}
    raw_rice = ing["rice"][0]
    variety = p["variety"]
    ratio = r["liquid_ratio_by_variety"][variety]
    cooked = scaling.cooked_rice_cups(raw_rice, r["rice_expansion"])
    protein = p["protein"]
    return {
        "dish": r["name"], "ref": ref, "servings": p["servings"], "factor": factor,
        "ing": ing,
        "variety": variety,
        "liquid_ratio": ratio,
        "liquid_cups": scaling.cooking_liquid_cups(raw_rice, ratio),
        "rice_expansion": r["rice_expansion"],
        "cooked_cups": cooked,
        "frying_capacity": p["frying_capacity"],
        "frying_batches": scaling.frying_batches(cooked, p["frying_capacity"]),
        "protein": protein,
        "protein_g": 0 if protein == "none"
                     else scaling.round_grams(r["protein_reference_g"] * factor),
        "oil_tbsp": scaling.oil_tbsp(p["servings"]),
    }


_CALC = {"jollof": _calc_jollof, "fried_rice": _calc_fried}


def _summary_lines(dish, c):
    """A short list of headline figures shown above the steps."""
    lines = ["Servings: %d" % c["servings"],
             "Scaling factor: %s (from a %d-serving reference)"
             % (scaling.fmt(c["factor"]), c["ref"])]
    if dish == "jollof":
        lines.append("Style: %s   Spice: %s   Protein: %s"
                     % (c["style"], c["spice"], c["protein"]))
        lines.append("Cooking liquid: ~%s cups" % scaling.fmt(c["liquid_cups"]))
        if c["pot_batches"] > 1:
            lines.append("Pot batches: %d (batch exceeds one pot)" % c["pot_batches"])
    else:
        lines.append("Rice variety: %s   Protein: %s" % (c["variety"], c["protein"]))
        lines.append("Cooking liquid: ~%s cups (ratio %s)"
                     % (scaling.fmt(c["liquid_cups"]), scaling.fmt(c["liquid_ratio"])))
        lines.append("Expected cooked rice: ~%s cups   Frying batches: %d"
                     % (scaling.fmt(c["cooked_cups"]), c["frying_batches"]))
    return lines


def build_plan(dish, params):
    """Build a cooking guide.

    Parameters
    ----------
    dish : str
        A key from :data:`expertcook.recipes.DISHES` ("jollof" / "fried_rice").
    params : dict
        Raw user answers keyed by the ``name`` fields in ``PARAM_SPECS``.
        Missing values fall back to each spec's default.

    Returns
    -------
    dict with keys: ``dish`` (display name), ``dish_key``, ``params`` (cleaned),
    ``summary`` (list of headline lines), ``steps`` (ordered list of
    ``{"order", "phase", "text"}``), and ``calc`` (the raw computed values).
    """
    if dish not in DISHES:
        raise ValueError("Unknown dish: %r (choose from %s)"
                         % (dish, ", ".join(DISHES)))

    clean = _validate(dish, params)
    calc = _CALC[dish](clean)

    engine = ENGINES[dish]()
    engine.calc = calc
    engine.reset()

    # Feed the query into the engine as facts, then let the rules fire.
    engine.declare(Flag(name="ready"))
    engine.declare(Flag(name="protein_none" if calc["protein"] == "none"
                        else "protein_present"))
    if dish == "jollof":
        engine.declare(Flag(name="style_party" if calc["style"] == "party"
                            else "style_regular"))
    engine.run()

    steps = sorted((f for f in engine.facts.values() if isinstance(f, Step)),
                   key=lambda f: f["order"])
    steps_out = [{"order": s["order"], "phase": s["phase"], "text": s["text"]}
                 for s in steps]

    return {
        "dish": calc["dish"],
        "dish_key": dish,
        "params": clean,
        "summary": _summary_lines(dish, calc),
        "steps": steps_out,
        "calc": calc,
    }
