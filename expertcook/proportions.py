"""Validated recipe snapshots and atomic updates to the knowledge base."""

from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import tempfile

from .recipes import DISHES, PARAM_SPECS

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "proportions.json"
_PROPORTIONS_PATH = os.environ.get("PROPORTIONS_PATH", str(_DEFAULT_PATH))
ROUNDINGS = {"count", "half", "quarter", "range", "grams"}
SPECIALS = {"spice", "liquid", "protein", "seasoning", "to_taste"}
# Ingredients referenced by procedural rules cannot be deleted.
REQUIRED = {
    "jollof": {"tomatoes", "bell_peppers", "scotch_bonnet", "onions",
               "tomato_paste", "vegetable_oil", "curry_powder", "thyme",
               "seasoning_cubes", "bay_leaves", "stock", "protein"},
    "fried_rice": {"carrots", "bell_peppers", "green_beans", "green_peas",
                   "sweet_corn", "scotch_bonnet", "onions", "vegetable_oil",
                   "curry_powder", "thyme", "seasoning_cubes", "stock", "protein"},
}


class ProportionsError(ValueError):
    """The knowledge base cannot safely produce a guide."""


def _number(value, path, positive=False):
    try:
        finite = math.isfinite(value)
    except (TypeError, OverflowError):
        finite = False
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not finite or value < 0
            or (positive and value == 0)):
        raise ProportionsError("%s must be a finite %s number" % (
            path, "positive" if positive else "non-negative"))


def validate_data(data):
    """Validate an in-memory candidate before it can become active."""
    if not isinstance(data, dict):
        raise ProportionsError("Proportions must be a JSON object")
    dishes = {k for k in data if not k.startswith("_")}
    if dishes != set(DISHES):
        raise ProportionsError("Proportions must define exactly jollof and fried_rice")
    for dish in DISHES:
        conf = data[dish]
        if not isinstance(conf, dict):
            raise ProportionsError("%s must be an object" % dish)
        types, ingredients = conf.get("rice_types"), conf.get("ingredients")
        if not isinstance(types, dict) or not isinstance(ingredients, dict):
            raise ProportionsError("%s requires rice_types and ingredients objects" % dish)
        choices = next(s["choices"] for s in PARAM_SPECS[dish] if s["name"] == "rice_type")
        if set(types) != set(choices):
            raise ProportionsError("%s rice_types must match supported rice choices" % dish)
        for name, rt in types.items():
            if not isinstance(rt, dict):
                raise ProportionsError("%s rice type %s must be an object" % (dish, name))
            for field in ("liquid_ratio", "expansion"):
                _number(rt.get(field), "%s.%s.%s" % (dish, name, field), positive=True)
        _number(conf.get("liquid_reserve_per_rice"), dish + ".liquid_reserve_per_rice")
        missing = REQUIRED[dish] - set(ingredients)
        if missing:
            raise ProportionsError("%s is missing required ingredients: %s" % (dish, ", ".join(sorted(missing))))
        if "rice" in ingredients:
            raise ProportionsError("rice is the input base and cannot be redefined")
        for key, rule in ingredients.items():
            path = "%s.ingredients.%s" % (dish, key)
            if not isinstance(rule, dict):
                raise ProportionsError(path + " must be an object")
            special = rule.get("special")
            if special is not None and (not isinstance(special, str) or special not in SPECIALS):
                raise ProportionsError(path + " has an unknown special rule")
            for field in ("label", "unit", "note"):
                if field in rule and not isinstance(rule[field], str):
                    raise ProportionsError(path + "." + field + " must be text")
            if special == "to_taste":
                if key in REQUIRED[dish]:
                    raise ProportionsError(path + " must have a numeric quantity")
                continue
            if (not isinstance(rule.get("unit"), str)
                    or not isinstance(rule.get("rounding"), str)
                    or rule["rounding"] not in ROUNDINGS):
                raise ProportionsError(path + " requires a unit and a supported rounding rule")
            expected = {"stock": "liquid", "protein": "protein", "scotch_bonnet": "spice"}.get(key)
            if expected and special != expected:
                raise ProportionsError(path + " must use special=" + expected)
            if special == "liquid" and (rule["unit"] != "cups" or rule["rounding"] == "range"):
                raise ProportionsError(path + " liquid must use cups and scalar rounding")
            if special == "protein" and (rule["unit"] != "g" or rule["rounding"] != "grams"):
                raise ProportionsError(path + " protein must use g and grams rounding")
            if special == "spice":
                levels = rule.get("per_rice_by_spice")
                if not isinstance(levels, dict) or set(levels) != {"mild", "medium", "hot"}:
                    raise ProportionsError(path + " requires mild, medium and hot ratios")
                for level, value in levels.items():
                    _number(value, path + "." + level)
            elif special != "liquid":
                _number(rule.get("per_rice"), path + ".per_rice")
    return True


def _load_raw():
    try:
        with open(_PROPORTIONS_PATH, encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, ValueError) as exc:
        raise ProportionsError("Cannot read proportions: %s" % exc) from exc


def fingerprint(data):
    try:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise ProportionsError("Proportions must contain finite JSON values") from exc
    return sha256(canonical.encode()).hexdigest()


def snapshot():
    data = _load_raw()
    validate_data(data)
    return deepcopy(data), fingerprint(data)


def save(data):
    """Atomically publish a valid candidate; concurrent editors are last-write wins."""
    validate_data(data)
    path = Path(_PROPORTIONS_PATH)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
            temporary = stream.name
            json.dump(data, stream, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return fingerprint(data)


def initialize_storage():
    """Seed an explicitly configured persistent volume on first startup."""
    path = Path(_PROPORTIONS_PATH)
    if path != _DEFAULT_PATH and not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with _DEFAULT_PATH.open(encoding="utf-8") as stream:
            save(json.load(stream))


def load_proportions(dish):
    data, _ = snapshot()
    if dish not in data:
        raise ProportionsError("Unknown dish: %r" % dish)
    return data[dish]


def list_dishes():
    return list(DISHES)


def dish_ingredients(dish):
    return list(load_proportions(dish)["ingredients"].items())


def rice_types(dish):
    return load_proportions(dish)["rice_types"]


def get_rice_type(dish, variety):
    return rice_types(dish)[variety]


def validate(dish):
    load_proportions(dish)
    return True
