"""Pure maths helpers + per-ingredient rounding rules.

RICE IS THE BASE: every ingredient quantity is ``rice_cups * per_rice`` (its
own independent relationship from proportions.json). No shared scaling factor.

Rounding rules (per the recipe specs - decimal quantities are NEVER shown):
  * "count"   whole items, minimum 1 (tomatoes, onions, peppers, ...)
  * "half"    nearest 1/2, minimum 1/2 (seasoning cubes: 2.5 cubes is fine,
              2.25 cubes rounds to 2)
  * "quarter" nearest 1/4, minimum 1/4 (cups, oil, ...)
  * "range"   fractional values become a range, e.g. 2.65 tbsp -> "2-3 tbsp",
              2.25 tbsp -> "2 tbsp" (tsp/tbsp seasonings)
  * "grams"   nearest 50 g, minimum 50 (protein)

No experta here - just numbers in, numbers out - so this module is easy to
test on its own (see ``selftest.py``).
"""

import math
from decimal import Decimal, ROUND_CEILING

_EPS = 1e-9


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt(x):
    """Format a number for display: drop a trailing ``.0`` but keep fractions."""
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(xf - round(xf)) < _EPS:
        return str(int(round(xf)))
    return ("%.2f" % xf).rstrip("0").rstrip(".")


def fraction_str(x):
    """Pretty-print common fractions: 0.25 -> '1/4', 1.5 -> '1 1/2', ..."""
    whole = int(x)
    frac = x - whole
    names = {0.25: "1/4", 0.5: "1/2", 0.75: "3/4"}
    for val, name in names.items():
        if abs(frac - val) < _EPS:
            if whole == 0:
                return name
            return "%d %s" % (whole, name)
    return fmt(x)


def qty(amount, unit=""):
    """Format an amount + unit, e.g. ``7.5 cups`` / ``1 cup`` / ``2-3 tbsp``.

    ``amount`` may be a number or a ``(lo, hi)`` tuple (a measurement range).
    """
    if amount is None:                      # e.g. "to taste" ingredients
        return unit or "to taste"
    if isinstance(amount, tuple):
        return ("%s-%s %s" % (fmt(amount[0]), fmt(amount[1]), unit)).strip()
    s = fraction_str(amount)
    if not unit:
        return s
    if float(amount) <= 1.0 + _EPS and unit.endswith("s"):
        unit = unit[:-1]                   # singular: "1/2 cup" not "1/2 cups"
    return "%s %s" % (s, unit)


# ---------------------------------------------------------------------------
# Rounding rules (one per ingredient, chosen in proportions.json)
# ---------------------------------------------------------------------------

def round_count(x):
    """Whole items (tomatoes, cubes, ...), minimum 1."""
    return 0 if x == 0 else max(1, int(round(x)))


def round_half(x):
    """Nearest 1/2, minimum 1/2 (e.g. 2.25 -> 2, 2.6 -> 2.5)."""
    return 0 if x == 0 else max(0.5, round(x * 2) / 2.0)


def round_quarter(x):
    """Nearest 1/4, minimum 1/4 (cups, tbsp, tsp)."""
    return 0 if x == 0 else max(0.25, round(x * 4) / 4.0)


def round_range(x):
    """Fractional amounts become a practical range (spec: no decimals).

    2.65 tbsp  -> (2, 3)   displayed as "2-3 tbsp"
    2.25 tbsp  -> 2        displayed as "2 tbsp"   (spec example)
    2.75 tbsp  -> 3        near enough to a whole number
    """
    if x == 0:
        return 0
    whole = math.floor(x)
    frac = x - whole
    if frac <= 0.25 + _EPS:
        return max(1, whole)
    if frac >= 0.75 - _EPS:
        return max(1, whole + 1)
    return (whole, whole + 1)


def round_grams(x, step=50):
    """Mass in grams, rounded to a practical increment, minimum one step."""
    return 0 if x == 0 else max(step, int(round(x / step)) * step)


_ROUNDERS = {
    "count": round_count,
    "half": round_half,
    "quarter": round_quarter,
    "range": round_range,
    "grams": round_grams,
}


def apply_rounding(x, rule):
    """Round for presentation, preserving zero and rejecting invalid rules."""
    if rule not in _ROUNDERS:
        raise ValueError("Unknown rounding rule: %r" % rule)
    if not math.isfinite(x) or x < 0:
        raise ValueError("Quantity must be finite and non-negative")
    return 0 if x == 0 else _ROUNDERS[rule](x)


# ---------------------------------------------------------------------------
# Rice-relative quantity calculation
# ---------------------------------------------------------------------------

def multiply(left, right):
    """Multiply decimal input values before converting to a JSON number."""
    return float(Decimal(str(left)) * Decimal(str(right)))


def per_rice_quantity(rice_cups, per_rice, rule):
    """Quantity of one ingredient = rice x its own per-rice relationship."""
    return apply_rounding(multiply(rice_cups, per_rice), rule)


def spice_quantity(rice_cups, spice, per_rice_by_spice, rule="count"):
    """Spice-driven rule: base comes from the spice level, then the rice."""
    per_rice = per_rice_by_spice[spice]
    return apply_rounding(multiply(rice_cups, per_rice), rule)


def liquid_cups(rice_cups, ratio, rule="quarter"):
    """Total cooking liquid target = rice x the rice type's liquid ratio."""
    return apply_rounding(multiply(rice_cups, ratio), rule)


def liquid_reserve(rice_cups, per_rice, rule="quarter"):
    """Hot liquid kept aside for mid-cooking adjustments."""
    return apply_rounding(multiply(rice_cups, per_rice), rule)


def cooked_rice_cups(rice_cups, expansion, rule="half"):
    """Expected cooked volume = raw rice x the rice type's expansion."""
    return apply_rounding(multiply(rice_cups, expansion), rule)


# ---------------------------------------------------------------------------
# Equipment / batching rules (non-linear)
# ---------------------------------------------------------------------------

def pot_batches(rice_cups, capacity_cups):
    """How many pots are needed if the batch exceeds one pot's capacity."""
    if capacity_cups <= 0:
        return 1
    return max(1, int((Decimal(str(rice_cups)) / Decimal(str(capacity_cups))).to_integral_value(rounding=ROUND_CEILING)))


def frying_batches(cooked_cups, capacity_cups):
    """Number of frying batches = ceil(cooked rice / pan capacity)."""
    if capacity_cups <= 0:
        return 1
    return pot_batches(cooked_cups, capacity_cups)
