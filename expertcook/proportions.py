"""Rice-relative proportionality rules, loaded from ``proportions.json``.

THE CORE IDEA
-------------
Rice is the most important ingredient. Every other ingredient defines its OWN
independent relationship to rice - there is no shared "scaling factor".

The relationships live in ``proportions.json`` (plain, dict-like JSON) so they
can be inserted / modified / deleted the same way you would edit any JSON
object, without touching any code. Recipes are independent and do NOT share
parameters.

Each ingredient entry supports:

    "per_rice"          amount per 1 cup of rice (simple linear rule)
    "per_rice_by_spice" spice-driven rules (special: "spice")
    "special"           "liquid" | "protein" | "seasoning" | "to_taste"
    "unit"              display unit
    "rounding"          "count" | "half" | "quarter" | "range" | "grams"
    "note"              free-text caveat shown in the UI

The file is re-read on every call to :func:`load_proportions`, so edits are
picked up without restarting anything (turn caching off via the module
variable ``CACHE_SECONDS = 0``).
"""

import json
import os
import time

# Path to proportions.json (project root / package parent).
_PROPORTIONS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "proportions.json")

CACHE_SECONDS = 0          # 0 -> always re-read (edit-friendly)
_cache = {"t": 0.0, "data": None}

REQUIRED_FIELDS = ("unit", "rounding")

SPECIALS = ("spice", "liquid", "protein", "seasoning", "to_taste")


class ProportionsError(ValueError):
    """Raised when proportions.json is missing, invalid or incomplete."""


def _load_raw():
    now = time.time()
    if CACHE_SECONDS > 0 and _cache["data"] is not None \
            and now - _cache["t"] < CACHE_SECONDS:
        return _cache["data"]
    try:
        with open(_PROPORTIONS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (IOError, OSError) as exc:
        raise ProportionsError(
            "Cannot read proportions file %s: %s" % (_PROPORTIONS_PATH, exc))
    except json.JSONDecodeError as exc:
        raise ProportionsError(
            "proportions.json is not valid JSON (line %d: %s)"
            % (exc.lineno, exc.msg))
    if not isinstance(data, dict):
        raise ProportionsError("proportions.json must contain a JSON object")
    _cache["t"], _cache["data"] = now, data
    return data


def load_proportions(dish):
    """Return the raw proportions dict for one dish (fresh from disk)."""
    data = _load_raw()
    if dish not in data:
        raise ProportionsError(
            "proportions.json has no entry for dish %r (found: %s)"
            % (dish, ", ".join(k for k in data if not k.startswith("_"))))
    return data[dish]


def list_dishes():
    """Dish keys defined in proportions.json (leading '_' entries ignored)."""
    return [k for k in _load_raw() if not k.startswith("_")]


def dish_ingredients(dish):
    """Ordered [(key, rule_dict)] for a dish."""
    props = load_proportions(dish)
    return list(props.get("ingredients", {}).items())


def rice_types(dish):
    """{variety: {"liquid_ratio": ..., "expansion": ...}} for a dish."""
    return load_proportions(dish).get("rice_types", {})


def get_rice_type(dish, variety):
    """Rice-type parameters (liquid ratio, expansion) for one variety."""
    types = rice_types(dish)
    if variety not in types:
        raise ProportionsError(
            "proportions.json (%s) has no rice type %r (found: %s)"
            % (dish, variety, ", ".join(types)))
    return types[variety]


def validate(dish):
    """Sanity-check one dish's rules; raises ProportionsError on problems."""
    props = load_proportions(dish)
    for section in ("rice_types", "ingredients"):
        if section not in props or not isinstance(props[section], dict) \
                or not props[section]:
            raise ProportionsError(
                "Dish %r is missing a non-empty '%s' section" % (dish, section))
    for variety, rt in props["rice_types"].items():
        if "liquid_ratio" not in rt:
            raise ProportionsError(
                "Rice type %r (dish %r) has no 'liquid_ratio'" % (variety, dish))
    for key, rule in props["ingredients"].items():
        special = rule.get("special")
        if special == "spice":
            if "per_rice_by_spice" not in rule:
                raise ProportionsError(
                    "Ingredient %r (dish %r) is spice-driven but has no "
                    "'per_rice_by_spice'" % (key, dish))
        elif special in ("liquid", "to_taste"):
            pass                     # no numeric rule needed
        else:
            if "per_rice" not in rule:
                raise ProportionsError(
                    "Ingredient %r (dish %r) has no 'per_rice' value"
                    % (key, dish))
    return True
