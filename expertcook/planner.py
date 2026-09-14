"""High-level entry point: turn a dish + query parameters into a cooking guide.

``build_plan(dish, params)`` validates the parameters, derives every ingredient
quantity from the RICE via the rules in ``proportions.json`` (each ingredient
has its own independent rice-relative relationship), runs the matching experta
engine, and returns an ordered, ready-to-display plan.
"""

import math
from uuid import uuid4

from . import scaling
from . import proportions as props
from .recipes import DISHES, PARAM_SPECS, get_recipe
from .facts import Flag, Step
from .engines import ENGINES
from .audit import ENGINE_LOCK, implementation_hash, runtime_versions, utc_now


def _validate(dish, params):
    """Coerce/validate raw params against PARAM_SPECS, filling in defaults."""
    if not isinstance(params, dict):
        raise ValueError("params must be an object")
    specs = PARAM_SPECS[dish]
    clean = {}
    for spec in specs:
        name = spec["name"]
        val = params.get(name, spec.get("default"))
        if val is None or val == "":
            val = spec.get("default")
        if spec["type"] in ("int", "float"):
            try:
                if isinstance(val, bool):
                    raise ValueError
                val = float(val)
                if not math.isfinite(val):
                    raise ValueError
                if spec["type"] == "int":
                    if abs(val - round(val)) > 1e-9:
                        raise ValueError
                    val = int(val)
            except (TypeError, ValueError, OverflowError):
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


def _compute_ingredients(dish, p, conf):
    """Derive every ingredient from the rice using proportions.json.

    Returns a dict ``key -> {label, amount, unit, note, special}`` where
    ``amount`` may be a number or a ``(lo, hi)`` range tuple. ``rice`` is
    always first (dicts preserve insertion order).
    """
    rice_cups = p["rice_cups"]
    rice_type = conf["rice_types"][p["rice_type"]]
    spice = p.get("spice", "medium")
    protein = p.get("protein", "none")

    ing = {"rice": {"label": "Rice", "amount": rice_cups, "raw_amount": rice_cups, "unit": "cups",
                    "derivation": {"formula": "User input", "raw_amount": rice_cups, "rounding": "none"},
                    "note": "the base ingredient - everything is relative to it"}}

    for key, rule in conf["ingredients"].items():
        special = rule.get("special")
        entry = {
            "label": rule.get("label", key.replace("_", " ").title()),
            "unit": rule.get("unit", ""),
            "note": rule.get("note"),
            "special": special,
        }
        source = "%s.ingredients.%s.per_rice" % (dish, key)
        ratio = rule.get("per_rice")
        formula = "rice_cups × ratio"
        if special == "spice":
            ratio = rule["per_rice_by_spice"][spice]
            source = "%s.ingredients.%s.per_rice_by_spice.%s" % (dish, key, spice)
        elif special == "liquid":
            ratio = rice_type["liquid_ratio"]
            source = "%s.rice_types.%s.liquid_ratio" % (dish, p["rice_type"])
        raw = None if special == "to_taste" else scaling.multiply(rice_cups, ratio)
        if special == "protein" and protein == "none":
            raw, formula = 0, "protein == none → 0"
        if special == "to_taste":
            formula, source = "To taste; no fixed amount", "%s.ingredients.%s" % (dish, key)
        entry["raw_amount"] = raw
        entry["amount"] = None if raw is None else scaling.apply_rounding(raw, rule["rounding"])
        entry["derivation"] = {"formula": formula, "rice_cups": rice_cups,
                               "ratio": ratio, "source": source,
                               "raw_amount": raw, "rounding": rule.get("rounding", "none")}
        ing[key] = entry
    return ing


def _calc(dish, p, conf):
    """Compute all derived values for one dish (individual recipes)."""
    r = get_recipe(dish)
    rice_cups = p["rice_cups"]
    rice_type = p["rice_type"]
    rt = conf["rice_types"][rice_type]
    ing = _compute_ingredients(dish, p, conf)

    calc = {
        "dish": r["name"],
        "rice_cups": rice_cups,
        "rice_type": rice_type,
        "liquid_ratio": rt["liquid_ratio"],
        "expansion": rt.get("expansion", 3.0),
        "ing": ing,
    }

    reserve_per_rice = conf["liquid_reserve_per_rice"]
    calc["liquid_reserve_raw"] = scaling.multiply(rice_cups, reserve_per_rice)
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
        calc["cooked_cups_raw"] = scaling.multiply(rice_cups, calc["expansion"])
        calc["cooked_cups"] = scaling.cooked_rice_cups(
            rice_cups, calc["expansion"])
        calc["frying_capacity"] = p["frying_capacity"]
        calc["frying_batches"] = scaling.frying_batches(
            calc["cooked_cups_raw"], p["frying_capacity"])
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


def build_plan(dish, params, *, knowledge=None):
    """Generate a plan using one snapshot; knowledge enables archived replays."""
    with ENGINE_LOCK:
        return _build_plan(dish, params, knowledge=knowledge)


def _build_plan(dish, params, *, knowledge=None):
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
    if not isinstance(dish, str) or dish not in DISHES:
        raise ValueError("Unknown dish: %r (choose from %s)"
                         % (dish, ", ".join(DISHES)))
    if knowledge is None:
        knowledge, config_hash = props.snapshot()
    else:
        from copy import deepcopy
        knowledge = deepcopy(knowledge)
        props.validate_data(knowledge)
        config_hash = props.fingerprint(knowledge)
    clean = _validate(dish, params)
    calc = _calc(dish, clean, knowledge[dish])

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
    initial_facts = []
    for fact in engine.facts.values():
        if isinstance(fact, Flag):
            name = fact["name"]
            source = "validated parameters and knowledge" if name == "ready" else (
                "params.protein" if name.startswith("protein_") else "params.style")
            initial_facts.append({"fact_id": fact.__factid__, "name": name, "source": source})
    engine.run()

    evidence_by_order = {output["order"]: event for event in engine.trace for output in event["outputs"]}

    steps = sorted((f for f in engine.facts.values() if isinstance(f, Step)),
                   key=lambda f: f["order"])
    steps_out = [{"order": s["order"], "phase": s["phase"], "text": s["text"],
                  "rule_id": evidence_by_order[s["order"]]["rule_id"],
                  "firing_sequence": evidence_by_order[s["order"]]["sequence"]}
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
            "raw_amount": entry["raw_amount"],
            "derivation": entry["derivation"],
        })

    return {
        "dish": calc["dish"],
        "dish_key": dish,
        "params": clean,
        "summary": _summary_lines(dish, calc),
        "steps": steps_out,
        "ingredients": ingredients,
        "calc": calc,
        "audit": {
            "schema_version": 1, "run_id": str(uuid4()), "generated_at": utc_now(),
            "config_hash": config_hash, "implementation_hash": implementation_hash(),
            "knowledge_snapshot": knowledge,
            "runtime": runtime_versions(), "initial_facts": initial_facts,
            "firings": engine.trace, "not_fired": engine.skipped_rules(),
            "derived": {k: v for k, v in calc.items() if k != "ing"},
            "scope": "Guide generation only. Cooking observations are advice, not sensed facts.",
        },
    }
