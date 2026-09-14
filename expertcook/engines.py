"""The expert system itself: one experta KnowledgeEngine per dish.

Each recipe is an INDIVIDUAL engine - recipes do not share parameters.
All quantities arrive pre-computed on ``engine.calc`` (a plain dict) from
:mod:`expertcook.planner`, which derives every ingredient from the rice via
the rules in ``proportions.json``.

The RULES here hold the *procedural* knowledge: which steps apply, how they
branch on the query (protein present/absent, party vs regular finish, whether
the batch must be split), and the order they belong in. Each rule declares a
:class:`~expertcook.facts.Step` tagged with an ``order`` (in tens) and guards
itself with ``NOT(Step(order=N))`` so it fires exactly once. The planner
sorts the Step facts by ``order``, so the guide is always in the correct
sequence even though experta may fire the rules in any order.
"""

from experta import KnowledgeEngine, Rule, NOT

from .facts import Flag, Step
from .scaling import fmt, qty


def _ing_line(label, entry, note=None):
    """One readable bullet line for a computed ingredient entry."""
    line = "  - %s: %s" % (label, qty(entry["amount"], entry["unit"]))
    if note or entry.get("note"):
        line += "  (%s)" % (note or entry["note"])
    return line


def _ingredient_bullets(ing):
    """Readable bullet lines for the ingredient dict, rice first."""
    lines = [_ing_line("RICE (base)", ing["rice"])]
    for key, entry in ing.items():
        if key == "rice":
            continue
        lines.append(_ing_line(entry["label"], entry))
    return lines


class JollofRiceEngine(KnowledgeEngine):
    """Generates a Jollof Rice guide from ``self.calc`` (see jollof_rice.md)."""

    # ---- Step 1: overview + measured ingredients -------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=10)))
    def overview(self):
        c = self.calc
        lines = [
            "Jollof Rice for %s cup(s) of %s rice."
            % (fmt(c["rice_cups"]), c["rice_type"]),
            "Rice is the base: every other quantity below is derived from it "
            "using its own independent proportionality rule.",
            "",
            "Ingredients (all relative to the rice):",
        ]
        lines += _ingredient_bullets(c["ing"])
        lines.append("  - total cooking liquid target: %s (ratio %s for %s rice), "
                     "minus liquid already in the sauce"
                     % (qty(c["liquid_cups"], "cups"),
                        fmt(c["liquid_ratio"]), c["rice_type"]))
        lines.append("  - hot liquid reserve for adjustments: %s"
                     % qty(c["liquid_reserve"], "cups"))
        if c["protein"] == "none":
            lines.append("  - protein: none (vegetarian - use water/veg stock)")
        else:
            lines.append("  - protein: %s (%s), cooked separately and its stock "
                         "counted toward the liquid"
                         % (c["protein"], qty(c["protein_g"], "g")))
        self.declare(Step(order=10, phase="Overview", text="\n".join(lines)))

    # ---- Step 2: prepare -------------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=20)))
    def prepare(self):
        c = self.calc
        self.declare(Step(
            order=20, phase="Prepare",
            text=("Measure out every calculated quantity above. Wash the rice in "
                  "cold water until it runs clear, then drain. Wash and cut the "
                  "tomatoes (%s), bell peppers (%s), scotch bonnet (%s) and enough "
                  "onion (%s) for blending into pieces. Slice the rest of the onion "
                  "for frying - keep the two portions separate."
                  % (qty(c["ing"]["tomatoes"]["amount"], "medium"),
                     fmt(c["ing"]["bell_peppers"]["amount"]),
                     fmt(c["ing"]["scotch_bonnet"]["amount"]),
                     qty(c["ing"]["onions"]["amount"], "medium")))))

    # ---- Step 3: blend the pepper mix -----------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=30)))
    def blend(self):
        c = self.calc
        self.declare(Step(
            order=30, phase="Blend",
            text=("Blend the tomatoes, bell peppers, %s scotch bonnet and the "
                  "blending onion until smooth. If it is too thick to blend, add "
                  "a little water and blend again - WRITE DOWN any water added, "
                  "it counts toward the %s total liquid."
                  % (fmt(c["ing"]["scotch_bonnet"]["amount"]),
                     qty(c["liquid_cups"], "cups")))))

    # ---- Step 4: protein + stock (only when a protein is chosen) ---------
    @Rule(Flag(name="protein_present"), NOT(Step(order=40)))
    def cook_protein(self):
        c = self.calc
        self.declare(Step(
            order=40, phase="Protein",
            text=("Cook the %s of %s separately: season with onion, salt, curry "
                  "and thyme, steam on low, then simmer in water until tender. "
                  "Fry or grill the pieces if you like, and RESERVE the cooking "
                  "liquid - it is the stock that flavours the rice. Its volume "
                  "must be subtracted from the liquid target."
                  % (qty(c["protein_g"], "g"), c["protein"]))))

    # ---- Step 5: fry onions + tomato paste ------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=50)))
    def fry_base(self):
        c = self.calc
        self.declare(Step(
            order=50, phase="Fry base",
            text=("Heat %s of vegetable oil in the pot over medium heat. Fry the "
                  "sliced onions until softened and fragrant, then stir in the %s "
                  "of tomato paste and fry for about 3-5 minutes, stirring "
                  "regularly, until it darkens and the raw smell is gone."
                  % (qty(c["ing"]["vegetable_oil"]["amount"], "cups"),
                     qty(c["ing"]["tomato_paste"]["amount"], "tbsp")))))

    # ---- Step 6: cook the blended pepper mix ----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=60)))
    def reduce_sauce(self):
        self.declare(Step(
            order=60, phase="Cook sauce",
            text=("Add the blended pepper mix, stir thoroughly and cook uncovered "
                  "over medium heat for about 15-20 minutes, until the sauce "
                  "thickens and the raw tomato taste reduces. If it is still "
                  "watery, keep reducing; if it starts sticking, lower the heat "
                  "and stir. The sauce's volume and consistency feed the liquid "
                  "calculation in the next step.")))

    # ---- Step 7: season + calculate the cooking liquid ------------------
    @Rule(Flag(name="ready"), NOT(Step(order=70)))
    def season_and_liquid(self):
        c = self.calc
        ing = c["ing"]
        if c["protein"] == "none":
            liquid_source = "water or vegetable stock"
        else:
            liquid_source = "the reserved protein stock (top up with water)"
        self.declare(Step(
            order=70, phase="Season",
            text=("Stir in %s curry powder, %s thyme, %s seasoning cube(s) and %s "
                  "bay leaf/leaves. Add %s until the TOTAL liquid (sauce + blender "
                  "water + stock) is about %s - that is rice x %s for %s rice. "
                  "Taste now and adjust the seasoning BEFORE the rice goes in; "
                  "reduce the cubes/salt if the stock is already well seasoned."
                  % (qty(ing["curry_powder"]["amount"], "tbsp"),
                     qty(ing["thyme"]["amount"], "tsp"),
                     qty(ing["seasoning_cubes"]["amount"], "cubes"),
                     fmt(ing["bay_leaves"]["amount"]),
                     liquid_source,
                     qty(c["liquid_cups"], "cups"),
                     fmt(c["liquid_ratio"]), c["rice_type"]))))

    # ---- Step 8: add rice + cook (batch note if the pot is small) -------
    @Rule(Flag(name="ready"), NOT(Step(order=80)))
    def add_rice(self):
        c = self.calc
        text = ("Add the washed rice and stir until every grain is coated. The "
                "liquid should sit just at or slightly above the rice. Cover the "
                "pot tightly (foil under the lid helps trap steam), reduce the "
                "heat to medium-low, and cook for about 20-30 minutes - the goal "
                "at this point is simply that the rice softens.")
        if c["pot_batches"] > 1:
            text += ("\n  NOTE: %s cup(s) of rice is more than one pot of %s cup(s) "
                     "cooks well. Divide into %d batches so the rice steams "
                     "evenly - do not overfill a single pot."
                     % (fmt(c["rice_cups"]), fmt(c["pot_capacity"]),
                        c["pot_batches"]))
        self.declare(Step(order=80, phase="Cook rice", text=text))

    # ---- Step 9: inspect + adjust (runtime decisions) -------------------
    @Rule(Flag(name="ready"), NOT(Step(order=90)))
    def inspect(self):
        c = self.calc
        self.declare(Step(
            order=90, phase="Inspect",
            text=("Check the rice tenderness and the liquid left. If it is still "
                  "hard and the liquid is gone, add a little of the %s hot "
                  "reserve, cover, and continue on low heat. If it is still hard "
                  "but liquid remains, keep cooking without adding more. If it is "
                  "tender and the liquid is gone, move to the finish. If it is "
                  "tender but there is excess liquid, uncover on very low heat "
                  "until the liquid reduces. Repeat until tender."
                  % qty(c["liquid_reserve"], "cups"))))

    # ---- Step 10: finish - branches on style ----------------------------
    @Rule(Flag(name="style_party"), NOT(Step(order=100)))
    def finish_party(self):
        self.declare(Step(
            order=100, phase="Finish",
            text=("PARTY-STYLE FINISH: stir gently, cover again and raise the heat "
                  "briefly (about 5 minutes) to develop a lightly smoky, "
                  "caramelised bottom layer - watch it closely so it does not "
                  "burn. Then turn off the heat and leave covered to rest for "
                  "5-10 minutes.")))

    @Rule(Flag(name="style_regular"), NOT(Step(order=100)))
    def finish_regular(self):
        self.declare(Step(
            order=100, phase="Finish",
            text=("FINISH: turn off the heat and leave the pot covered to rest for "
                  "5-10 minutes so the grains firm up. Do not leave it over high "
                  "heat, which would burn the base.")))

    # ---- Step 11: serve --------------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=110)))
    def serve(self):
        self.declare(Step(
            order=110, phase="Serve",
            text=("Remove the bay leaves, fluff the rice gently and serve hot "
                  "with the fried protein on the side. Enjoy your jollof rice!")))


class FriedRiceEngine(KnowledgeEngine):
    """Generates a Fried Rice guide from ``self.calc`` (see fried_rice.md)."""

    # ---- Step 1: overview + planning figures ----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=10)))
    def overview(self):
        c = self.calc
        lines = [
            "Nigerian Fried Rice for %s cup(s) of %s rice."
            % (fmt(c["rice_cups"]), c["rice_type"]),
            "Rice is the base: every other quantity below is derived from it "
            "using its own independent proportionality rule.",
            "",
            "Ingredients (all relative to the rice):",
        ]
        lines += _ingredient_bullets(c["ing"])
        lines.append("  - rice cooking liquid: %s (ratio %s for %s rice)"
                     % (qty(c["liquid_cups"], "cups"),
                        fmt(c["liquid_ratio"]), c["rice_type"]))
        lines.append("  - hot liquid reserve: %s"
                     % qty(c["liquid_reserve"], "cups"))
        if c["protein"] == "none":
            lines.append("  - protein: none (vegetarian)")
        else:
            lines.append("  - protein: %s (%s), cooked before frying"
                         % (c["protein"], qty(c["protein_g"], "g")))
        lines.append("Planning figures:")
        lines.append("  - expected cooked rice: about %s (raw x %s expansion)"
                     % (qty(c["cooked_cups"], "cups"), fmt(c["expansion"])))
        lines.append("  - frying capacity: %s/batch  ->  %d frying batch(es)"
                     % (qty(c["frying_capacity"], "cups"), c["frying_batches"]))
        self.declare(Step(order=10, phase="Overview", text="\n".join(lines)))

    # ---- Step 2: prepare the ingredients --------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=20)))
    def prepare(self):
        c = self.calc
        ing = c["ing"]
        self.declare(Step(
            order=20, phase="Prepare",
            text=("Measure every calculated quantity above. Wash and drain the "
                  "rice (%s rice may need no soaking; adjust for your type). Wash, "
                  "peel if needed and dice the carrots (%s), trim and cut the green "
                  "beans (%s), deseed and dice the bell peppers (%s), and drain the "
                  "peas (%s) and sweet corn (%s). Peel and chop the onions (%s), "
                  "keeping the frying portion separate from any reserved onion. "
                  "Group firmer vegetables (carrot, green beans) for the earlier "
                  "frying stage and softer ones (peas, corn, peppers) for later."
                  % (c["rice_type"],
                     qty(ing["carrots"]["amount"], "cups"),
                     qty(ing["green_beans"]["amount"], "cups"),
                     qty(ing["bell_peppers"]["amount"], "cups"),
                     qty(ing["green_peas"]["amount"], "cups"),
                     qty(ing["sweet_corn"]["amount"], "cups"),
                     qty(ing["onions"]["amount"], "medium")))))

    # ---- Step 3: cook the protein (only when chosen) --------------------
    @Rule(Flag(name="protein_present"), NOT(Step(order=30)))
    def cook_protein(self):
        c = self.calc
        self.declare(Step(
            order=30, phase="Protein",
            text=("Handle raw protein SEPARATELY from ready-to-eat ingredients. "
                  "Cut the %s of %s into bite-size pieces, season with onion, "
                  "salt, curry and thyme, and cook through (liver must be "
                  "thoroughly cooked; chicken until no longer pink). Set aside "
                  "with any stock it produces - the stock counts toward the "
                  "rice's liquid and seasoning."
                  % (qty(c["protein_g"], "g"), c["protein"]))))

    # ---- Step 4: prepare the rice cooking liquid ------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=40)))
    def rice_liquid(self):
        c = self.calc
        self.declare(Step(
            order=40, phase="Rice liquid",
            text=("Prepare the cooking liquid: about %s of stock or seasoned "
                  "water for the rice (rice x %s). If the stock is already "
                  "seasoned, reduce the salt and seasoning cubes accordingly. "
                  "Keep about %s of hot stock/water aside as a reserve for "
                  "adjustments during cooking."
                  % (qty(c["liquid_cups"], "cups"), fmt(c["liquid_ratio"]),
                     qty(c["liquid_reserve"], "cups")))))

    # ---- Step 5: cook the rice ------------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=50)))
    def cook_rice(self):
        c = self.calc
        self.declare(Step(
            order=50, phase="Cook rice",
            text=("Put the rice in the pot with the calculated liquid. You may "
                  "add a little of the curry, thyme and onion at this stage "
                  "depending on your style. Stir gently, cover, bring to a boil "
                  "then reduce to a gentle simmer. Cook until the grains are just "
                  "tender for frying - NOT soft and mushy, or they will break "
                  "apart when fried.")))

    # ---- Step 6: inspect and adjust the rice ----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=60)))
    def inspect_rice(self):
        c = self.calc
        self.declare(Step(
            order=60, phase="Inspect rice",
            text=("Inspect the rice: still hard with no liquid left -> add a "
                  "small amount of the %s hot reserve, cover and continue on "
                  "low. Still hard with liquid left -> keep cooking. Tender with "
                  "no liquid -> proceed to cooling. Tender with excess liquid -> "
                  "drive it off uncovered on low heat. Repeat until the rice is "
                  "tender with no standing liquid."
                  % qty(c["liquid_reserve"], "cups"))))

    # ---- Step 7: cool and separate the rice -----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=70)))
    def condition_rice(self):
        self.declare(Step(
            order=70, phase="Cool rice",
            text=("Spread the cooked rice in a shallow tray so excess steam "
                  "escapes and the grains dry and separate. Judge the condition: "
                  "too wet (needs more drying), just right (dry, separate "
                  "grains), or too dry (needs a light sprinkle of hot stock). "
                  "Handle gently to minimise breakage. If cooking in advance, "
                  "cool quickly, refrigerate and reheat properly - never leave "
                  "cooked rice at room temperature for long.")))

    # ---- Step 8: fry the onions + optional protein ----------------------
    @Rule(Flag(name="ready"), NOT(Step(order=80)))
    def fry_onions_protein(self):
        c = self.calc
        protein_sentence = ""
        if c["protein"] != "none":
            protein_sentence = (" Add the cooked %s and toss briefly to pick up "
                                "the oil and flavour." % c["protein"])
        self.declare(Step(
            order=80, phase="Fry base",
            text=("Check the pan can hold the ingredients for this stage, then "
                  "heat %s of vegetable oil in a wide pan or wok over medium "
                  "heat. Fry the reserved onions until softened and fragrant.%s"
                  % (qty(c["ing"]["vegetable_oil"]["amount"], "tbsp"),
                     protein_sentence))))

    # ---- Step 9: fry the vegetables -------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=90)))
    def fry_veg(self):
        c = self.calc
        ing = c["ing"]
        self.declare(Step(
            order=90, phase="Fry veg",
            text=("Add the firmer vegetables first (carrots %s, green beans %s) "
                  "and fry a few minutes, then the softer ones (green peas %s, "
                  "sweet corn %s, bell peppers %s) with the %s scotch bonnet. "
                  "Stir regularly over medium heat. Keep them bright and "
                  "just-tender: if they soften too much or release a lot of "
                  "liquid, raise the heat briefly and finish quickly - soggy "
                  "vegetables make soggy fried rice."
                  % (qty(ing["carrots"]["amount"], "cups"),
                     qty(ing["green_beans"]["amount"], "cups"),
                     qty(ing["green_peas"]["amount"], "cups"),
                     qty(ing["sweet_corn"]["amount"], "cups"),
                     qty(ing["bell_peppers"]["amount"], "cups"),
                     fmt(ing["scotch_bonnet"]["amount"])))))

    # ---- Step 10: season the vegetables ---------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=100)))
    def season_veg(self):
        c = self.calc
        ing = c["ing"]
        self.declare(Step(
            order=100, phase="Season",
            text=("Stir in %s curry powder, %s thyme, %s seasoning cube(s) and "
                  "salt to taste. Cook briefly to distribute the flavour. "
                  "Remember what already went into the rice and the stock - the "
                  "cubes have their own adjustment rule, not a blind scale. If "
                  "undersalted, add a little at a time; if oversalted, stop "
                  "adding salty stock."
                  % (qty(ing["curry_powder"]["amount"], "tbsp"),
                     qty(ing["thyme"]["amount"], "tsp"),
                     qty(ing["seasoning_cubes"]["amount"], "cubes")))))

    # ---- Step 11: combine rice + vegetables -----------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=110)))
    def combine(self):
        c = self.calc
        text = ("Add the cooled rice to the vegetable mixture. If the rice "
                "exceeds the pan's capacity, fry in batches - each batch gets "
                "its share of vegetables. Fold gently with a lifting motion so "
                "the grains stay whole and the vegetables spread evenly. If the "
                "rice is too dry to combine, sprinkle a little hot stock; if it "
                "is too wet, let the excess steam off before adding more.")
        if c["frying_batches"] > 1:
            text += ("\n  NOTE: about %s of cooked rice is more than one %s "
                     "frying batch. Divide into %d batches - do NOT overload "
                     "the pan or simply cook it longer."
                     % (qty(c["cooked_cups"], "cups"),
                        qty(c["frying_capacity"], "cups"),
                        c["frying_batches"]))
        self.declare(Step(order=110, phase="Combine", text=text))

    # ---- Step 12: fry the combined rice ---------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=120)))
    def fry_rice(self):
        self.declare(Step(
            order=120, phase="Fry",
            text=("Fry the combined rice over medium heat, stirring gently and "
                  "regularly. Watch for: uneven heating (keep going), vegetables "
                  "not distributed (fold more), rice sticking (lower the heat, "
                  "stir gently), rice too dry (a small splash of hot stock - but "
                  "avoid unnecessary liquid), or grains breaking (stir less). "
                  "Stop when the rice is evenly heated, well seasoned and dry "
                  "with separate grains.")))

    # ---- Step 13: final seasoning + texture check -----------------------
    @Rule(Flag(name="ready"), NOT(Step(order=130)))
    def validate(self):
        self.declare(Step(
            order=130, phase="Validate",
            text=("Inspect the finished rice: seasoning (adjust in small steps "
                  "using each ingredient's own rule), moisture (too dry -> tiny "
                  "splash of hot stock; too moist -> fry uncovered a little "
                  "longer), texture (too soft -> no more liquid or stirring), "
                  "and vegetable condition. Remember extra frying dries the rice "
                  "and softens the vegetables, so adjust in one direction at a "
                  "time and re-check.")))

    # ---- Step 14: finish + serve ----------------------------------------
    @Rule(Flag(name="ready"), NOT(Step(order=140)))
    def finish(self):
        c = self.calc
        optional = ""
        if "spring_onions" in c["ing"]:
            optional = (" Stir in the spring onions (%s) at the very end so they "
                        "stay fresh."
                        % qty(c["ing"]["spring_onions"]["amount"], "cups"))
        self.declare(Step(
            order=140, phase="Serve",
            text=("Turn off the heat once the rice reaches the required "
                  "condition and let it settle briefly.%s Fluff gently to "
                  "separate the grains and distribute the vegetables, then serve "
                  "hot. Enjoy your fried rice!" % optional)))


ENGINES = {"jollof": JollofRiceEngine, "fried_rice": FriedRiceEngine}
