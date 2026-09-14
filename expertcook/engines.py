"""The expert system itself: one experta KnowledgeEngine per dish.

Design notes
------------
* The scaling maths is done in :mod:`expertcook.scaling` and handed to the engine
  on ``engine.calc`` (a plain dict) by :mod:`expertcook.planner`.
* The RULES here hold the *procedural* knowledge: which steps apply, how they
  branch on the query (protein present/absent, party vs regular finish, whether
  the batch must be split), and the order they belong in.
* Every rule declares a :class:`~expertcook.facts.Step` tagged with an ``order``
  (in tens) and guards itself with ``NOT(Step(order=N))`` so it fires exactly
  once. The planner sorts the resulting Step facts by ``order``, so the guide is
  always in the correct sequence even though experta may fire the rules in any
  order.
"""

from experta import KnowledgeEngine, Rule, NOT

from .facts import Flag, Step
from .scaling import fmt, qty


def _ing_lines(ing):
    """Turn the scaled-ingredient dict into readable bullet lines."""
    lines = []
    for name, (amt, unit) in ing.items():
        label = name.replace("_", " ")
        lines.append("  - %s %s" % (qty(amt, unit), label))
    return lines


class JollofRiceEngine(KnowledgeEngine):
    """Generates a Jollof Rice guide from ``self.calc``."""

    # ---- Step 1: overview + measured ingredients -------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=10)))
    def overview(self):
        c = self.calc
        lines = [
            "Prepare %d serving(s) of Jollof Rice." % c["servings"],
            "Scaling factor: %s (reference recipe serves %d)."
            % (fmt(c["factor"]), c["ref"]),
            "Ingredients (scaled to your batch):",
        ]
        lines += _ing_lines(c["ing"])
        lines.append("  - %d scotch bonnet pepper(s)  [spice level: %s]"
                     % (c["scotch_bonnet"], c["spice"]))
        if c["protein"] == "none":
            lines.append("  - protein: none (vegetarian)")
        else:
            lines.append("  - %s g %s" % (fmt(c["protein_g"]), c["protein"]))
        lines.append("  - cooking liquid target: about %s cups of stock/water"
                     % fmt(c["liquid_cups"]))
        lines.append("  - salt: to taste (start small, adjust near the end)")
        self.declare(Step(order=10, phase="Overview", text="\n".join(lines)))

    # ---- Step 2: prepare -------------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=20)))
    def prepare(self):
        self.declare(Step(
            order=20, phase="Prepare",
            text=("Wash the rice in cold water until it runs clear, then drain. "
                  "Wash and roughly chop the tomatoes, bell peppers and one onion "
                  "for blending. Slice the remaining onion for frying. Measure out "
                  "all the other ingredients.")))

    # ---- Step 3: blend the pepper mix -----------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=30)))
    def blend(self):
        c = self.calc
        self.declare(Step(
            order=30, phase="Blend",
            text=("Blend the tomatoes, bell peppers, %d scotch bonnet pepper(s) and "
                  "the chopped onion into a smooth puree. If it is too thick, add a "
                  "little water to help it blend - remember any water added here "
                  "counts toward the %s cups of cooking liquid."
                  % (c["scotch_bonnet"], fmt(c["liquid_cups"])))))

    # ---- Step 4: protein + stock (only when a protein is chosen) ---------
    @Rule(Flag(name="protein_present"), NOT(Step(order=40)))
    def cook_protein(self):
        c = self.calc
        self.declare(Step(
            order=40, phase="Protein",
            text=("Season the %s g of %s with a little onion, salt, curry and thyme. "
                  "Steam it on low heat, then add water and simmer until tender. Fry "
                  "or grill the pieces and set aside. RESERVE the cooking liquid - it "
                  "becomes the stock for the rice."
                  % (fmt(c["protein_g"]), c["protein"]))))

    # ---- Step 5: fry onions + tomato paste ------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=50)))
    def fry_base(self):
        c = self.calc
        oil_amt, oil_unit = c["ing"]["vegetable_oil"]
        paste_amt, paste_unit = c["ing"]["tomato_paste"]
        self.declare(Step(
            order=50, phase="Fry base",
            text=("Heat %s of vegetable oil in a large pot over medium heat. Fry "
                  "the sliced onions until soft and golden, then add the %s of "
                  "tomato paste and fry 3-5 minutes, stirring, until it darkens and "
                  "the raw smell is gone."
                  % (qty(oil_amt, oil_unit), qty(paste_amt, paste_unit)))))

    # ---- Step 6: cook the blended pepper mix ----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=60)))
    def reduce_sauce(self):
        self.declare(Step(
            order=60, phase="Cook sauce",
            text=("Add the blended pepper mix to the pot. Stir well and cook "
                  "uncovered over medium heat for about 15-20 minutes, until it "
                  "thickens and the raw tomato taste is gone. Lower the heat and "
                  "stir if it starts to stick.")))

    # ---- Step 7: season + add the cooking liquid ------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=70)))
    def season_and_liquid(self):
        c = self.calc
        ing = c["ing"]
        if c["protein"] == "none":
            liquid_source = "water or vegetable stock"
        else:
            liquid_source = "the reserved meat stock (top up with water if needed)"
        self.declare(Step(
            order=70, phase="Season",
            text=("Stir in %s curry powder, %s thyme, %d seasoning cube(s), "
                  "%d bay leaf/leaves and salt to taste. Add %s until the total "
                  "liquid in the pot is about %s cups - subtract any water you added "
                  "while blending. Taste and adjust the seasoning now, before the "
                  "rice goes in."
                  % (qty(ing["curry_powder"][0], ing["curry_powder"][1]),
                     qty(ing["thyme"][0], ing["thyme"][1]),
                     ing["seasoning_cubes"][0], ing["bay_leaves"][0],
                     liquid_source, fmt(c["liquid_cups"])))))

    # ---- Step 8: add rice + cook (with a batch note if the pot is small) -
    @Rule(Flag(name="ready"), NOT(Step(order=80)))
    def add_rice(self):
        c = self.calc
        text = ("Add the washed rice and stir until every grain is coated. The liquid "
                "should sit just at or slightly above the rice. Cover tightly (a sheet "
                "of foil under the lid helps trap steam), reduce the heat to low, and "
                "cook for about 20 minutes.")
        if c["pot_batches"] > 1:
            text += ("\n  NOTE: %d servings is more than one pot holds (%d "
                     "servings/pot). Cook in %d batches so the rice steams evenly - "
                     "do not overfill a single pot."
                     % (c["servings"], c["pot_capacity"], c["pot_batches"]))
        self.declare(Step(order=80, phase="Cook rice", text=text))

    # ---- Step 9: inspect + adjust (runtime decisions) -------------------
    @Rule(Flag(name="ready"), NOT(Step(order=90)))
    def inspect(self):
        self.declare(Step(
            order=90, phase="Inspect",
            text=("After 20 minutes, check the rice. If it is still hard and the "
                  "liquid is gone, sprinkle in a little hot water or stock, cover, and "
                  "continue on low. If it is still hard but liquid remains, keep "
                  "cooking. If it is tender and the liquid is gone, move on. Repeat "
                  "until the grains are tender.")))

    # ---- Step 10: finish - branches on style ----------------------------
    @Rule(Flag(name="style_party"), NOT(Step(order=100)))
    def finish_party(self):
        self.declare(Step(
            order=100, phase="Finish",
            text=("PARTY-STYLE FINISH: Give the pot a gentle stir, cover again and "
                  "raise the heat briefly (about 5 minutes) to develop a lightly "
                  "smoky, caramelised bottom. Watch it closely so it does not burn, "
                  "then turn off the heat and rest, covered, for 5-10 minutes.")))

    @Rule(Flag(name="style_regular"), NOT(Step(order=100)))
    def finish_regular(self):
        self.declare(Step(
            order=100, phase="Finish",
            text=("FINISH: Turn off the heat and leave the pot covered to rest for "
                  "5-10 minutes so the grains firm up. Do not leave it over high "
                  "heat, which would burn the base.")))

    # ---- Step 11: serve --------------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=110)))
    def serve(self):
        c = self.calc
        self.declare(Step(
            order=110, phase="Serve",
            text=("Remove the bay leaves, fluff the rice gently, and serve hot. "
                  "Enjoy your %d-serving Jollof Rice!" % c["servings"])))


class FriedRiceEngine(KnowledgeEngine):
    """Generates a Nigerian Fried Rice guide from ``self.calc``."""

    # ---- Step 1: initialise + planning figures --------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=10)))
    def overview(self):
        c = self.calc
        lines = [
            "Prepare %d serving(s) of Nigerian Fried Rice." % c["servings"],
            "Scaling factor: %s (reference recipe serves %d)."
            % (fmt(c["factor"]), c["ref"]),
            "Ingredients (scaled to your batch):",
        ]
        lines += _ing_lines(c["ing"])
        if c["protein"] == "none":
            lines.append("  - protein: none (vegetarian)")
        else:
            lines.append("  - %s g %s" % (fmt(c["protein_g"]), c["protein"]))
        lines.append("  - vegetable oil: %s tbsp (base + batch model, not a straight "
                     "multiple)" % fmt(c["oil_tbsp"]))
        lines.append("  - salt: to taste (account for salt already in the stock)")
        lines.append("Planning figures:")
        lines.append("  - expected cooked rice: about %s cups (raw x %s expansion)"
                     % (fmt(c["cooked_cups"]), fmt(c["rice_expansion"])))
        lines.append("  - frying capacity: %s cups/batch  ->  %d frying batch(es)"
                     % (fmt(c["frying_capacity"]), c["frying_batches"]))
        self.declare(Step(order=10, phase="Overview", text="\n".join(lines)))

    # ---- Step 2: prepare + cook the protein (only when chosen) ----------
    @Rule(Flag(name="protein_present"), NOT(Step(order=20)))
    def cook_protein(self):
        c = self.calc
        self.declare(Step(
            order=20, phase="Protein",
            text=("Clean and cut the %s g of %s into bite-size pieces. Season with a "
                  "little onion, salt, curry and thyme, add just enough water to cook, "
                  "and simmer until done (cooked through but not dry). Save any stock, "
                  "then set the protein aside - you need it cooked before frying the "
                  "rice." % (fmt(c["protein_g"]), c["protein"]))))

    # ---- Step 3: wash + prepare the rice --------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=30)))
    def wash_rice(self):
        c = self.calc
        rice_amt, rice_unit = c["ing"]["rice"]
        self.declare(Step(
            order=30, phase="Wash rice",
            text=("Measure %s %s of %s rice. Wash it in cold water until the water "
                  "runs fairly clear to remove surface starch, then drain well."
                  % (fmt(rice_amt), rice_unit, c["variety"]))))

    # ---- Step 4: cook the rice ------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=40)))
    def cook_rice(self):
        c = self.calc
        self.declare(Step(
            order=40, phase="Cook rice",
            text=("Cook the rice with about %s cups of water or stock "
                  "(liquid-to-rice ratio %s for %s) and a little salt. Cook until the "
                  "grains are just tender and separate - NOT mushy. If it is "
                  "undercooked but dry, add a splash more hot liquid; if it is cooked "
                  "but wet, drive off the extra moisture on low heat. Stop as soon as "
                  "the grains are done."
                  % (fmt(c["liquid_cups"]), fmt(c["liquid_ratio"]), c["variety"]))))

    # ---- Step 5: cool + condition ---------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=50)))
    def condition_rice(self):
        self.declare(Step(
            order=50, phase="Cool rice",
            text=("Spread the cooked rice out on a wide tray to release steam and dry "
                  "the surface. Do not pack it into a dense mass. It should be cool "
                  "enough to handle and dry enough to fry as separate grains.")))

    # ---- Step 6: prepare the vegetables ---------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=60)))
    def prep_veg(self):
        c = self.calc
        ing = c["ing"]
        self.declare(Step(
            order=60, phase="Prep veg",
            text=("Dice the vegetables to a similar small size so they cook evenly: "
                  "carrot %s, green beans %s, bell pepper %s, plus green peas %s and "
                  "sweet corn %s. Slice the spring onion (%s). Aim for cooked-but-firm, "
                  "not soft."
                  % (qty(*ing["carrot"]), qty(*ing["green_beans"]),
                     qty(*ing["bell_pepper"]), qty(*ing["green_peas"]),
                     qty(*ing["sweet_corn"]), qty(*ing["spring_onion"])))))

    # ---- Step 7: build the frying mixture -------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=70)))
    def frying_mixture(self):
        c = self.calc
        ing = c["ing"]
        protein_sentence = ("" if c["protein"] == "none"
                            else " Stir in the cooked protein.")
        self.declare(Step(
            order=70, phase="Fry mixture",
            text=("Heat %s tbsp of oil in a wide pan or wok over medium-high heat. Fry "
                  "the %s chopped onion until soft, then add the firmer vegetables "
                  "first (carrot, green beans) followed by the rest.%s Season with %s "
                  "curry, %s thyme, pepper and seasoning, and keep the vegetables "
                  "bright and just-firm."
                  % (fmt(c["oil_tbsp"]), qty(*ing["onion"]), protein_sentence,
                     qty(*ing["curry_powder"]), qty(*ing["thyme"])))))

    # ---- Step 8: add the rice (respecting frying-batch capacity) --------
    @Rule(Flag(name="ready"), NOT(Step(order=80)))
    def add_rice(self):
        c = self.calc
        text = ("Add the cooled rice to the pan a little at a time and toss so the "
                "seasoning and vegetables spread through it while the grains stay "
                "whole.")
        if c["frying_batches"] > 1:
            text += ("\n  NOTE: about %s cups of rice is more than one %s-cup frying "
                     "batch. Fry in %d separate batches - do NOT overload the pan or "
                     "simply cook it longer."
                     % (fmt(c["cooked_cups"]), fmt(c["frying_capacity"]),
                        c["frying_batches"]))
        self.declare(Step(order=80, phase="Combine", text=text))

    # ---- Step 9: fry the combined rice ----------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=90)))
    def fry_rice(self):
        self.declare(Step(
            order=90, phase="Fry",
            text=("Fry over medium-high heat, tossing regularly, until the rice is "
                  "heated through, evenly coloured, and reasonably dry with separate "
                  "grains. If it is too wet, keep frying; if it sticks, check the heat "
                  "and oil; if it starts to burn, lower the heat and move it to a clean "
                  "pan.")))

    # ---- Step 10: final seasoning + quality check -----------------------
    @Rule(Flag(name="ready"), NOT(Step(order=100)))
    def validate(self):
        self.declare(Step(
            order=100, phase="Validate",
            text=("Taste and check: texture (cooked, separate), moisture (not wet), "
                  "seasoning (add a little at a time if flat), vegetables (firm, not "
                  "mushy), protein (evenly spread) and colour. Adjust in small steps. "
                  "Stop when it meets the target.")))

    # ---- Step 11: serve --------------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=110)))
    def serve(self):
        c = self.calc
        self.declare(Step(
            order=110, phase="Serve",
            text=("Serve the fried rice hot. Enjoy your %d-serving Nigerian Fried "
                  "Rice!" % c["servings"])))


ENGINES = {"jollof": JollofRiceEngine, "fried_rice": FriedRiceEngine}
