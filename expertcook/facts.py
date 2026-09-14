"""experta Fact definitions shared by the recipe engines."""

from experta import Fact, Field


class Param(Fact):
    """A single query parameter supplied by the user (name -> value)."""
    name = Field(str, mandatory=True)
    value = Field(object, mandatory=True)


class Flag(Fact):
    """A derived boolean condition the rules branch on.

    Examples: ``ready``, ``protein_present``, ``protein_none``,
    ``style_party``, ``style_regular``.
    """
    name = Field(str, mandatory=True)


class Step(Fact):
    """One generated instruction in the cooking guide.

    ``order`` gives the recipe sequence (in tens, leaving room to insert),
    so the guide can be sorted deterministically regardless of the order in
    which the rules happened to fire.
    """
    order = Field(int, mandatory=True)
    phase = Field(str, default="")
    text = Field(str, mandatory=True)
