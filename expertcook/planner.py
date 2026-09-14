"""High-level entry point: turn a dish + query parameters into a cooking guide.

``build_plan(dish, params)`` validates the parameters, derives every ingredient
quantity from the RICE via the rules in ``proportions.json`` (each ingredient
has its own independent rice-relative relationship), runs the matching experta
engine, and returns an ordered, ready-to-display plan.
"""

from . import scaling
from . import proportions as props
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
        if spec["type"] in ("int", "float"):
            try:
                val = float(val)
                if spec["type"] == "int":
                    if abs(val - round(val)) > 1e-9:
                        raise ValueError
                    val = int(val)
            except (TypeError, ValueError):
                raise ValueError("%s must be a number." % spec["label"])
            lo = spec.get("min", 1)
            if val < lo:
                raise ValueError("%s must be at least %s." % (spec["label"], lo))
        elif spec["type"] == "choice":
            if val not in spec["choices"]:
                raise ValueError("%s must be one of: %s."
                                 % (spec["label"], ", ".join(spec["choices"])))
        clean[name] = val
    return clean


def _compute_ingredients(dish, p):
    """Derive every ingredient from the rice using proportions.json.

    Returns a dict ``key -> {label, amount, unit, note, special}`` where
    ``amount`` may be a number or a ``(lo, hi)`` range tuple. ``rice`` is
    always first (dicts preserve insertion order).
    """
    rice_cups = p["rice_cups"]
    rice_type = props.get_rice_type(dish, p["rice_type"])
    spice = p.get("spice", "medium")
    protein = p.get("protein", "none")

    ing = {"rice": {"label": "Rice", "amount": rice_cups, "unit": "cups",
                    "note": "the base ingredient - everything is relative to it"}}

    for key, rule in props.dish_ingredients(dish):
        special = rule.get("special")
        entry = {
            "label": rule.get("label", key.replace("_", " ").title()),
            "unit": rule.get("unit", ""),
            "note": rule.get("note"),
            "special": special,
        }
        if special == "spice":
            entry["amount"] = scaling.spice_quantity(
                rice_cups, spice, rule.get("per_rice_by_spice", {}),
                rule.get("rounding", "count"))
        elif special == "liquid":
            entry["amount"] = scaling.liquid_cups(
                rice_cups, rice_type["liquid_ratio"], rule.get("rounding", "quarter"))
        elif special == "protein":
            entry["amount"] = 0 if protein == "none" else scaling.per_rice_quantity(
                rice_cups, rule.get("per_rice", 0), rule.get("rounding", "grams"))
        elif special == "to_taste":
            entry["amount"] = None
            entry["note"] = rule.get("note", "to taste")
        else:
            entry["amount"] = scaling.per_rice_quantity(
                rice_cups, rule.get("per_rice", 0),
                rule.get("rounding", "quarter"))
        ing[key] = entry
    return ing


def _calc(dish, p):
    """Compute all derived values for one dish (individual recipes)."""
    r = get_recipe(dish)
    rice_cups = p["rice_cups"]
    rice_type = p["rice_type"]
    rt = props.get_rice_type(dish, rice_type)
    ing = _compute_ingredients(dish, p)

    calc = {
        "dish": r["name"],
        "rice_cups": rice_cups,
        "rice_type": rice_type,
        "liquid_ratio": rt["liquid_ratio"],
        "expansion": rt.get("expansion", 3.0),
        "ing": ing,
    }

    reserve_per_rice = props.load_proportions(dish).get(
        "liquid_reserve_per_rice", 0.25)
    calc["liquid_reserve"] = scaling.liquid_reserve(
        rice_cups, reserve_per_rice)
    calc["liquid_cups"] = ing["stock"]["amount"]
    calc["protein"] = p.get("protein", "none")
    calc["protein_g"] = ing["protein"]["amount"]

    if dish == "jollof":
        calc["style"] = p["style"]
        calc["pot_capacity"] = p["pot_capacity"]
        calc["pot_batches"] = scaling.pot_batches(
            rice_cups, p["pot_capacity"])
    else:
        calc["cooked_cups"] = scaling.cooked_rice_cups(
            rice_cups, calc["expansion"])
        calc["frying_capacity"] = p["frying_capacity"]
        calc["frying_batches"] = scaling.frying_batches(
            calc["cooked_cups"], p["frying_capacity"])
    return calc


def _summary_lines(dish, c):
    """A short list of headline figures shown above the steps."""
    lines = [
        "Rice (the base): %s %s of %s rice"
        % (scaling.fmt(c["rice_cups"]), "cup" if c["rice_cups"] == 1 else "cups",
           c["rice_type"]),
        "Every other quantity is derived from the rice using its own "
        "independent proportionality rule.",
        "Total cooking liquid target: %s (ratio %s)"
        % (scaling.qty(c["liquid_cups"], "cups"), scaling.fmt(c["liquid_ratio"])),
        "Hot liquid reserve: %s" % scaling.qty(c["liquid_reserve"], "cups"),
    ]
    if dish == "jollof":
        lines.append("Style: %s   Protein: %s" % (c["style"], c["protein"]))
        if c["pot_batches"] > 1:
            lines.append("Pot batches: %d (batch exceeds one pot)" % c["pot_batches"])
    else:
        lines.append("Protein: %s" % c["protein"])
        lines.append("Expected cooked rice: ~%s   Frying batches: %d"
                     % (scaling.qty(c["cooked_cups"], "cups"), c["frying_batches"]))
    return lines


def build_plan(dish, params):
    """Build a cooking guide.

    Parameters
    ----------
    dish : str
        A key from :data:`expertcook.recipes.DISHES` ("jollof" / "fried_rice").
    params : dict
        Raw user answers keyed by the ``name`` fields in ``PARAM_SPECS``.
        ``rice_cups`` is required-by-default and drives every other quantity.
        Missing values fall back to each spec's default.

    Returns
    -------
    dict with keys: ``dish`` (display name), ``dish_key``, ``params`` (cleaned),
    ``summary`` (list of headline lines), ``steps`` (ordered list of
    ``{"order", "phase", "text"}``), ``ingredients`` (rice-relative list) and
    ``calc`` (the raw computed values).
    """
    if dish not in DISHES:
        raise ValueError("Unknown dish: %r (choose from %s)"
                         % (dish, ", ".join(DISHES)))
    props.validate(dish)          # fail fast on a broken proportions.json

    clean = _validate(dish, params)
    calc = _calc(dish, clean)

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

    # Rice-relative ingredient list for the UI (amount pre-formatted, no
    # decimals - ranges become "lo-hi", fractions become "1/2" style).
    ingredients = []
    for key, entry in calc["ing"].items():
        if entry["amount"] is None:
            amount = None
        elif isinstance(entry["amount"], tuple):
            amount = "%s-%s" % tuple(scaling.fraction_str(v)
                                     for v in entry["amount"])
        else:
            amount = scaling.fraction_str(entry["amount"])
        ingredients.append({
            "key": key,
            "label": entry["label"],
            "amount": amount,
            "unit": entry["unit"],
            "note": entry.get("note"),
        })

    return {
        "dish": calc["dish"],
        "dish_key": dish,
        "params": clean,
        "summary": _summary_lines(dish, calc),
        "steps": steps_out,
        "ingredients": ingredients,
        "calc": calc,
    }
