"""Pure scaling helpers and the recipes' special (non-linear) rules.

No experta here - just numbers in, numbers out - so this module is easy to test
on its own (see ``selftest.py``).
"""

import math


def scaling_factor(desired_servings, reference_servings):
    """Ratio between the desired batch and the reference batch."""
    if reference_servings <= 0:
        raise ValueError("reference servings must be > 0")
    return desired_servings / float(reference_servings)


def scale(quantity, factor):
    """Straight proportional scaling: Q = Q_reference * factor."""
    return quantity * factor


def round_count(x):
    """Round a countable item (tomatoes, cubes, ...) to a whole number, min 1."""
    return max(1, int(round(x)))


def round_volume(x, step=0.25):
    """Round a volume (cups/tbsp/tsp) to a practical fraction (default 1/4)."""
    return round(round(x / step) * step, 2)


def round_grams(x, step=50):
    """Round a mass in grams to a practical increment, min one step."""
    return max(step, int(round(x / step)) * step)


def scale_ingredient(qty, kind, factor):
    """Scale one proportional ingredient and round it by its kind."""
    raw = qty * factor
    if kind == "count":
        return round_count(raw)
    return round_volume(raw)


# --------------------------------------------------------------------------
# Special rules - these parameters do NOT scale by a straight multiplication.
# --------------------------------------------------------------------------

def scotch_bonnet_count(spice, factor, by_spice):
    """Heat is driven by the chosen spice level, then scaled with the batch."""
    base = by_spice.get(spice, by_spice.get("medium", 2))
    return max(1, int(round(base * factor)))


def cooking_liquid_cups(rice_cups, ratio):
    """Initial liquid = rice quantity * rice-specific liquid-to-rice ratio."""
    return round_volume(rice_cups * ratio)


def oil_tbsp(servings, base=2, per_serving=0.5):
    """Fried-rice oil: a base amount plus a batch-dependent amount.

    Deliberately NOT a straight multiple of servings (see fried_rice spec S6).
    """
    return round_volume(base + per_serving * servings)


def cooked_rice_cups(raw_rice_cups, expansion):
    """Cooked volume = raw volume * variety/method expansion factor."""
    return round_volume(raw_rice_cups * expansion)


def frying_batches(cooked_cups, capacity_cups):
    """Non-linear rule: number of frying batches = ceil(rice / pan capacity)."""
    if capacity_cups <= 0:
        return 1
    return max(1, int(math.ceil(cooked_cups / float(capacity_cups))))


def pot_batches(desired_servings, capacity_servings):
    """How many pots are needed if the batch exceeds a single pot's capacity."""
    if capacity_servings <= 0:
        return 1
    return max(1, int(math.ceil(desired_servings / float(capacity_servings))))


def fmt(x):
    """Format a number for display: drop a trailing ``.0`` but keep real fractions."""
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(xf - round(xf)) < 1e-9:
        return str(int(round(xf)))
    return ("%.2f" % xf).rstrip("0").rstrip(".")


def qty(amt, unit):
    """Format an amount with its unit, e.g. ``7.5 cups`` / ``1 cup`` / ``5``.

    Singularises "cups" -> "cup" when the amount is exactly one; other units
    (tbsp, tsp, medium, ...) are left unchanged.
    """
    s = fmt(amt)
    if not unit:
        return s
    if unit == "cups":
        try:
            if abs(float(amt) - 1.0) < 1e-9:
                unit = "cup"
        except (TypeError, ValueError):
            pass
    return "%s %s" % (s, unit)
