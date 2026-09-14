from experta import *

# ---------- FACT DEFINITIONS ----------

class Ingredient(Fact):
    """Represents an ingredient and whether it's ready/available."""
    name = Field(str, mandatory=True)
    ready = Field(bool, default=False)

class Stage(Fact):
    """Tracks progress through the cooking pipeline."""
    name = Field(str, mandatory=True)
    done = Field(bool, default=False)

class CookingState(Fact):
    """Runtime state values (timers, heat level, etc.)."""
    pass


# ---------- EXPERT SYSTEM ----------

class JollofRiceExpert(KnowledgeEngine):

    # ---------- STEP 1: Prep & Blend ----------
    @Rule(
        Ingredient(name='tomatoes', ready=True),
        Ingredient(name='bell_peppers', ready=True),
        Ingredient(name='scotch_bonnet', ready=True),
        Ingredient(name='onions', ready=True),
        NOT(Stage(name='blend', done=True))
    )
    def blend_vegetables(self):
        print("[Step 1] Blending tomatoes, bell peppers, scotch bonnet & onions into a smooth puree.")
        self.declare(Stage(name='blend', done=True))
        self.declare(Ingredient(name='pepper_mix', ready=True))

    # ---------- STEP 2: Protein & Stock ----------
    @Rule(
        Ingredient(name='meat', ready=True),
        Ingredient(name='curry', ready=True),
        Ingredient(name='thyme', ready=True),
        Ingredient(name='ginger', ready=True),
        Ingredient(name='garlic', ready=True),
        NOT(Stage(name='season_meat', done=True))
    )
    def season_meat(self):
        print("[Step 2a] Seasoning meat with onions, salt, curry, thyme, ginger, garlic.")
        self.declare(Stage(name='season_meat', done=True))

    @Rule(Stage(name='season_meat', done=True), NOT(Stage(name='steam_meat', done=True)))
    def steam_meat(self):
        print("[Step 2b] Steaming meat on low heat (no water) to absorb flavor.")
        self.declare(Stage(name='steam_meat', done=True))

    @Rule(Stage(name='steam_meat', done=True), NOT(Stage(name='cook_meat', done=True)))
    def cook_meat_and_make_stock(self):
        print("[Step 2c] Adding water, simmering until tender, then frying/grilling meat separately.")
        print("          Reserving meat stock for later.")
        self.declare(Stage(name='cook_meat', done=True))
        self.declare(Ingredient(name='meat_stock', ready=True))
        self.declare(Ingredient(name='cooked_meat', ready=True))

    # ---------- STEP 3: Fry Tomato Base ----------
    @Rule(Ingredient(name='oil', ready=True), NOT(Stage(name='fry_onions', done=True)))
    def fry_onions(self):
        print("[Step 3a] Heating oil, frying sliced onions until brown/caramelized.")
        self.declare(Stage(name='fry_onions', done=True))

    @Rule(
        Stage(name='fry_onions', done=True),
        Ingredient(name='tomato_paste', ready=True),
        NOT(Stage(name='fry_paste', done=True))
    )
    def fry_tomato_paste(self):
        print("[Step 3b] Frying tomato paste 10-15 min until sour taste is gone and oil separates.")
        self.declare(Stage(name='fry_paste', done=True))

    @Rule(
        Stage(name='fry_paste', done=True),
        Ingredient(name='pepper_mix', ready=True),
        NOT(Stage(name='reduce_pepper_mix', done=True))
    )
    def cook_pepper_mix(self):
        print("[Step 3c] Adding blended pepper mix, cooking ~10 min until reduced.")
        self.declare(Stage(name='reduce_pepper_mix', done=True))

    @Rule(
        Stage(name='reduce_pepper_mix', done=True),
        Ingredient(name='curry', ready=True),
        Ingredient(name='thyme', ready=True),
        Ingredient(name='bay_leaves', ready=True),
        Ingredient(name='seasoning_cubes', ready=True),
        NOT(Stage(name='stew_base', done=True))
    )
    def finish_stew_base(self):
        print("[Step 3d] Adding curry, thyme, bay leaves, seasoning cubes. Stew base ready.")
        self.declare(Stage(name='stew_base', done=True))
        self.declare(Ingredient(name='stew_base', ready=True))

    # ---------- STEP 4: Combine Rice and Cook ----------
    @Rule(Ingredient(name='rice', ready=True), NOT(Stage(name='wash_rice', done=True)))
    def wash_rice(self):
        print("[Step 4a] Washing rice until water runs clear.")
        self.declare(Stage(name='wash_rice', done=True))

    @Rule(
        Stage(name='wash_rice', done=True),
        Stage(name='stew_base', done=True),
        NOT(Stage(name='combine_rice', done=True))
    )
    def combine_rice_with_base(self):
        print("[Step 4b] Adding washed rice to stew base, stirring to coat every grain.")
        self.declare(Stage(name='combine_rice', done=True))

    @Rule(
        Stage(name='combine_rice', done=True),
        Ingredient(name='meat_stock', ready=True),
        NOT(Stage(name='add_stock', done=True))
    )
    def add_stock(self):
        print("[Step 4c] Pouring in reserved meat stock, level just at/above the rice.")
        self.declare(Stage(name='add_stock', done=True))

    @Rule(Stage(name='add_stock', done=True), NOT(Stage(name='layer_toppings', done=True)))
    def layer_toppings(self):
        print("[Step 4d] Layering sliced onions, fresh tomatoes, and butter on top.")
        self.declare(Stage(name='layer_toppings', done=True))

    @Rule(Stage(name='layer_toppings', done=True), NOT(Stage(name='steam_rice', done=True)))
    def steam_rice(self):
        print("[Step 4e] Covering tightly (foil under lid), cooking on low heat 30-45 min.")
        self.declare(Stage(name='steam_rice', done=True))
        self.declare(CookingState(rice_tender=True, liquid_absorbed=True))

    # ---------- STEP 5: Smoky Finish ----------
    @Rule(
        Stage(name='steam_rice', done=True),
        CookingState(rice_tender=True, liquid_absorbed=True),
        NOT(Stage(name='mix_rice', done=True))
    )
    def mix_rice(self):
        print("[Step 5a] Opening pot, mixing rice thoroughly.")
        self.declare(Stage(name='mix_rice', done=True))

    @Rule(Stage(name='mix_rice', done=True), NOT(Stage(name='smoky_finish', done=True)))
    def smoky_finish(self):
        print("[Step 5b] Covering again, high heat ~5 min for smoky caramelized bottom (party jollof).")
        self.declare(Stage(name='smoky_finish', done=True))

    @Rule(Stage(name='smoky_finish', done=True), NOT(Stage(name='rest', done=True)))
    def rest_and_serve(self):
        print("[Step 5c] Turning off heat, resting 10 min.")
        self.declare(Stage(name='rest', done=True))
        print("\n✅ Jollof rice is ready to serve!")


# ---------- RUN THE ENGINE ----------

if __name__ == "__main__":
    engine = JollofRiceExpert()
    engine.reset()

    # Declare all ingredients as "ready" (available/prepped)
    ingredients = [
        'rice', 'tomatoes', 'bell_peppers', 'scotch_bonnet', 'onions',
        'garlic', 'ginger', 'oil', 'meat_stock_base', 'tomato_paste',
        'curry', 'thyme', 'bay_leaves', 'salt', 'seasoning_cubes',
        'butter', 'meat', 'oil'
    ]
    for ing in ingredients:
        engine.declare(Ingredient(name=ing, ready=True))

    engine.run()