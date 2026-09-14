"""Reference-recipe data (4-serving base) and the user-facing parameter specs.

This is the single source of truth for both interfaces: the CLI and the Tkinter
UI build their prompts from ``PARAM_SPECS`` so they never drift apart.

Each proportional ingredient is ``(quantity, unit, kind)`` where ``kind`` is
either ``"count"`` (whole items) or ``"volume"`` (cups/tbsp/tsp).
"""

JOLLOF = {
    "key": "jollof",
    "name": "Jollof Rice",
    "reference_servings": 4,
    "proportional": {
        "rice": (3, "cups", "volume"),
        "tomatoes": (4, "medium", "count"),
        "bell_peppers": (2, "", "count"),
        "onions": (2, "medium", "count"),
        "tomato_paste": (2, "tbsp", "volume"),
        "vegetable_oil": (0.5, "cups", "volume"),
        "curry_powder": (1, "tbsp", "volume"),
        "thyme": (1, "tsp", "volume"),
        "seasoning_cubes": (2, "", "count"),
        "bay_leaves": (2, "", "count"),
    },
    # Special-rule data
    "protein_reference_g": 500,
    "liquid_to_rice_ratio": 1.5,          # long-grain parboiled reference
    "scotch_bonnet_by_spice": {"mild": 1, "medium": 2, "hot": 4},
}

FRIED_RICE = {
    "key": "fried_rice",
    "name": "Fried Rice",
    "reference_servings": 4,
    "proportional": {
        "rice": (2, "cups", "volume"),
        "carrot": (0.5, "cups", "volume"),
        "green_peas": (0.5, "cups", "volume"),
        "green_beans": (0.5, "cups", "volume"),
        "sweet_corn": (0.5, "cups", "volume"),
        "bell_pepper": (0.5, "cups", "volume"),
        "spring_onion": (0.25, "cups", "volume"),
        "onion": (1, "medium", "count"),
        "curry_powder": (1, "tbsp", "volume"),
        "thyme": (1, "tsp", "volume"),
    },
    # Special-rule data
    "protein_reference_g": 300,
    "liquid_ratio_by_variety": {"parboiled": 1.5, "basmati": 1.25, "other": 1.75},
    "rice_expansion": 3.0,
}

_RECIPES = {"jollof": JOLLOF, "fried_rice": FRIED_RICE}

# Menu order + display names.
DISHES = {"jollof": "Jollof Rice", "fried_rice": "Fried Rice"}


def get_recipe(key):
    """Return the reference-recipe dict for a dish key."""
    try:
        return _RECIPES[key]
    except KeyError:
        raise ValueError("Unknown dish: %r" % key)


# Parameters the user is asked for, per dish. ``type`` is "int" or "choice".
PARAM_SPECS = {
    "jollof": [
        {"name": "servings", "label": "Servings", "type": "int",
         "default": 4, "min": 1, "help": "How many people to cook for"},
        {"name": "style", "label": "Style", "type": "choice",
         "choices": ["party", "regular"], "default": "party",
         "help": "Party-style adds a smoky, caramelised finish"},
        {"name": "spice", "label": "Spice level", "type": "choice",
         "choices": ["mild", "medium", "hot"], "default": "medium",
         "help": "Controls how many scotch bonnet peppers go in"},
        {"name": "protein", "label": "Protein", "type": "choice",
         "choices": ["chicken", "beef", "goat", "none"], "default": "chicken",
         "help": "Choose 'none' for a vegetarian version"},
        {"name": "pot_capacity", "label": "Pot capacity (servings)", "type": "int",
         "default": 12, "min": 1,
         "help": "Most servings your largest pot cooks well at once"},
    ],
    "fried_rice": [
        {"name": "servings", "label": "Servings", "type": "int",
         "default": 4, "min": 1, "help": "How many people to cook for"},
        {"name": "protein", "label": "Protein", "type": "choice",
         "choices": ["chicken", "liver", "chicken+liver", "none"],
         "default": "chicken", "help": "Choose 'none' for a vegetarian version"},
        {"name": "variety", "label": "Rice variety", "type": "choice",
         "choices": ["parboiled", "basmati", "other"], "default": "parboiled",
         "help": "Affects the water-to-rice ratio"},
        {"name": "frying_capacity", "label": "Frying capacity (cups/batch)",
         "type": "int", "default": 6, "min": 1,
         "help": "Cooked rice your pan/wok can fry well in one batch"},
    ],
}
