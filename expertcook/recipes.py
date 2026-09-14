"""Recipe definitions and the user-facing parameter specs.

Each recipe is an INDIVIDUAL definition - recipes do not share parameters.
Ingredient quantities are NOT defined here: every non-rice ingredient has its
own rice-relative proportionality rule in ``proportions.json`` (see
:mod:`expertcook.proportions`).

This module holds only:
  * recipe metadata (key, display name, description)
  * PARAM_SPECS: the parameters the user is asked for, per dish

All interfaces (CLI, Tkinter UI, web) build their prompts from PARAM_SPECS,
so they never drift apart.
"""

# ---------------------------------------------------------------------------
# Individual recipe definitions (metadata only - quantities live in
# proportions.json, cooking rules in engines.py)
# ---------------------------------------------------------------------------

JOLLOF = {
    "key": "jollof",
    "name": "Jollof Rice",
    "description": "Nigerian jollof rice - a smoky, tomato-pepper party classic.",
    "spec": "reciepies/jollof_rice.md",
}

FRIED_RICE = {
    "key": "fried_rice",
    "name": "Fried Rice",
    "description": "Nigerian fried rice - vegetables and rice stir-fried in seasoning.",
    "spec": "reciepies/fried_rice.md",
}

_RECIPES = {"jollof": JOLLOF, "fried_rice": FRIED_RICE}

# Menu order + display names.
DISHES = {"jollof": "Jollof Rice", "fried_rice": "Fried Rice"}


def get_recipe(key):
    """Return the recipe dict for a dish key."""
    try:
        return _RECIPES[key]
    except KeyError:
        raise ValueError("Unknown dish: %r" % key)


# ---------------------------------------------------------------------------
# Parameters the user is asked for, per dish. ``type`` is "int", "float" or
# "choice". RICE IS THE BASE: the user always states how much rice to cook and
# every other ingredient is derived from it via proportions.json.
# ---------------------------------------------------------------------------

PARAM_SPECS = {
    "jollof": [
        {"name": "rice_cups", "label": "Rice (cups)", "type": "float",
         "default": 3, "min": 0.5, "step": 0.5,
         "help": "Rice is the base - everything else follows from this"},
        {"name": "rice_type", "label": "Rice type", "type": "choice",
         "choices": ["parboiled", "basmati", "other"], "default": "parboiled",
         "help": "Sets the liquid-to-rice ratio"},
        {"name": "style", "label": "Cooking style", "type": "choice",
         "choices": ["party", "regular"], "default": "party",
         "help": "Party-style adds a smoky, caramelised finish"},
        {"name": "spice", "label": "Spice level", "type": "choice",
         "choices": ["mild", "medium", "hot"], "default": "medium",
         "help": "Controls the scotch bonnet quantity"},
        {"name": "protein", "label": "Protein", "type": "choice",
         "choices": ["chicken", "beef", "goat", "none"], "default": "chicken",
         "help": "Choose 'none' for a vegetarian version"},
        {"name": "pot_capacity", "label": "Pot capacity (cups of rice)",
         "type": "float", "default": 10, "min": 1, "step": 1,
         "help": "Raw rice your largest pot cooks well at once"},
    ],
    "fried_rice": [
        {"name": "rice_cups", "label": "Rice (cups)", "type": "float",
         "default": 2, "min": 0.5, "step": 0.5,
         "help": "Rice is the base - everything else follows from this"},
        {"name": "rice_type", "label": "Rice type", "type": "choice",
         "choices": ["parboiled", "basmati", "other"], "default": "parboiled",
         "help": "Sets the liquid-to-rice ratio"},
        {"name": "spice", "label": "Spice level", "type": "choice",
         "choices": ["mild", "medium", "hot"], "default": "mild",
         "help": "Controls the scotch bonnet quantity"},
        {"name": "protein", "label": "Protein", "type": "choice",
         "choices": ["chicken", "liver", "chicken+liver", "none"],
         "default": "chicken", "help": "Choose 'none' for a vegetarian version"},
        {"name": "frying_capacity", "label": "Frying capacity (cups/batch)",
         "type": "float", "default": 6, "min": 1, "step": 1,
         "help": "Cooked rice your pan/wok can fry well in one batch"},
    ],
}
