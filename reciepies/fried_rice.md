Below is a **parameterized procedural model** for Nigerian Fried Rice. I’ll treat the recipe as a cooking system rather than a fixed recipe, so that the same specification can generate a small home batch or a much larger batch.

The important distinction is that **ingredient quantities, cooking times, liquid requirements, vessel capacity, and heat behavior are not all governed by the same scaling rule**.

# 1. Recipe Parameters

The recipe is based on producing fried rice through these major phases:

1. Prepare and cook the rice.
2. Prepare the protein component.
3. Prepare the vegetables.
4. Prepare the frying mixture.
5. Combine rice with the frying mixture.
6. Fry and season until the desired final state is reached.
7. Validate the final product.

A reference recipe can be defined as **4 servings**.

The fundamental scaling parameter is:

**Scaling factor = desired servings / 4**

For example:

* 2 servings → scaling factor = 0.5
* 4 servings → scaling factor = 1
* 8 servings → scaling factor = 2
* 20 servings → scaling factor = 5

However, this scaling factor should **not automatically be applied to every parameter**.

---

# 2. Recipe-Level Parameters

### `reference_servings`

Represents the number of servings produced by the reference recipe.

* Unit: servings
* Reference value: 4
* Scaling: no
* Dependency: none

This establishes the basis for all proportional quantities.

---

### `desired_servings`

Represents how many servings the system should produce.

* Unit: servings
* Scaling: input
* Dependency: none

---

### `scaling_factor`

Represents the ratio between the desired batch and reference batch.

**Scaling factor = desired servings / reference servings**

* Unit: dimensionless
* Scaling: calculated
* Dependency: `desired_servings`, `reference_servings`

---

### `desired_final_consistency`

Represents the target texture of the finished rice.

Possible states include:

* separate grains
* dry/semi-dry fried rice
* slightly moist fried rice
* overly wet

The normal target is:

**separate, cooked, non-mushy grains with a relatively dry fried-rice consistency.**

* Unit: qualitative state
* Scaling: no
* Dependency: rice variety, water, cooking time, frying time

---

### `rice_variety`

Represents the type of rice being used.

Examples:

* long-grain parboiled rice
* basmati
* other long-grain rice

This is important because rice varieties differ in:

* water requirement

* absorption

* cooking time

* grain expansion

* tendency to become sticky

* Unit: categorical

* Scaling: no

* Special rule: yes

* Dependencies: water quantity, cooking time, cooling requirement

---

### `cooking_vessel_capacity`

Represents the usable capacity of the pot/pan.

* Unit: litres or approximate batch capacity
* Scaling: no
* Special rule: yes
* Dependencies: batch size, rice volume, frying space

The vessel must have enough space for the food to be stirred without excessive compression.

---

### `frying_batch_capacity`

Represents the maximum amount of cooked rice that can be effectively fried in one batch.

* Unit: kg of cooked rice or servings
* Scaling: no
* Special rule: yes
* Dependencies: pan/wok size, heat output, desired frying quality

This is particularly important for large batches.

A 10× recipe does **not necessarily mean one 10× frying operation**.

The system may need to divide the batch into multiple frying batches.

---

# 3. Ingredient Parameters

A reference 4-serving formulation can be represented approximately as follows.

## Rice

### `rice_quantity_raw`

Reference:

**2 cups raw rice**

* Unit: cups or grams
* Scaling: proportional
* Formula:

**required rice = reference rice × scaling factor**

* Dependencies: servings, rice variety

The system should preferably internally convert cups to grams because mass is more reliable for automated scaling.

---

### `rice_cooking_liquid`

Represents water or stock used to cook the rice.

This should **not blindly be treated as a fixed linear ingredient**.

The required liquid depends on:

* rice variety
* rice quantity
* whether rice is parboiled
* washing/soaking
* cooking vessel
* evaporation
* cooking method

A useful parameter is:

`liquid_to_rice_ratio`

rather than simply saying "add X cups of water."

For example:

**required cooking liquid = raw rice quantity × rice-specific liquid ratio**

But the ratio itself is a parameter determined by rice type.

---

### `salt_for_rice`

Represents salt added during rice cooking.

* Unit: grams/teaspoons
* Scaling: approximately proportional
* Special rule: final seasoning must account for salt already present in stock and other ingredients
* Dependencies: rice quantity, stock salinity

Therefore the system should calculate an initial quantity but permit runtime adjustment.

---

# 4. Protein Parameters

Nigerian fried rice commonly uses chicken, liver, or both.

The model should therefore treat protein as a **component**, rather than hard-code one particular protein.

### `protein_type`

Examples:

* chicken

* liver

* chicken + liver

* mixed protein

* Unit: categorical

* Scaling: no

* Special rule: yes

---

### `protein_quantity`

Reference example:

**300 g prepared protein**

* Unit: grams
* Scaling: proportional
* Formula:

**required protein = reference protein × scaling factor**

However, different protein types require different preparation procedures.

---

### `protein_preparation_state`

Possible states:

* raw
* cleaned
* cut
* seasoned
* boiled/cooked
* fried
* shredded/cubed

The frying stage should receive **already cooked protein**.

---

### `protein_cooking_liquid`

If the protein is boiled or simmered:

* Unit: ml
* Scaling: approximately proportional
* Special rule: minimum liquid requirement
* Dependencies: protein quantity, vessel, cooking method

The liquid should be sufficient to cook the protein, but its exact quantity is process-dependent.

---

### `protein_cooking_time`

* Unit: minutes
* Scaling: generally **not proportional**
* Special rule: yes
* Depends on:

  * protein type
  * piece size
  * starting temperature
  * cooking method

Doubling chicken quantity does not mean doubling cooking time.

---

# 5. Vegetable Parameters

A typical vegetable mixture may contain:

* carrots
* green peas
* green beans
* sweet corn
* bell pepper
* spring onion

The model should treat these independently.

### `vegetable_quantity[i]`

Each vegetable has:

* type
* quantity
* unit
* preparation state
* cut size
* cooking tolerance

Example reference quantities:

* carrot: ½ cup
* peas: ½ cup
* green beans: ½ cup
* sweet corn: ½ cup
* bell pepper: ½ cup
* spring onion: ¼ cup

Each can scale proportionally:

**required vegetable quantity = reference quantity × scaling factor**

But preparation and cooking time do not necessarily scale.

---

### `vegetable_cut_size`

Examples:

* diced

* small cubes

* sliced

* Unit: mm/cm or qualitative size

* Scaling: no

* Special rule: yes

Cut size affects cooking time.

---

### `vegetable_cooking_state`

The target state is generally:

**cooked but still firm, retaining recognizable pieces and some texture.**

The system should not define completion solely as "cook for 5 minutes."

It should define both:

**time range + observed state**

---

# 6. Aromatic and Seasoning Parameters

The model can include:

* onion
* garlic
* ginger
* curry powder
* thyme
* white/black pepper
* seasoning cube/powder
* salt
* vegetable oil

Each has a quantity parameter.

For example:

### `onion_quantity`

* Unit: grams
* Scaling: proportional
* Dependency: servings

### `curry_quantity`

* Unit: teaspoons/grams
* Scaling: approximately proportional
* Special rule: final intensity must be checked
* Dependency: rice quantity, desired flavor intensity

### `oil_quantity`

Oil requires a special scaling rule.

It is **not necessarily safe to multiply oil perfectly linearly with servings**, because the required quantity depends partly on:

* pan surface
* amount of food
* frying batch
* desired coating
* heat
* food moisture

A useful model is:

**oil = base oil requirement + batch-dependent oil requirement**

rather than blindly multiplying the reference quantity.

---

# 7. Derived Parameters

Before cooking begins, the system calculates several values.

## Raw ingredient quantities

For proportional ingredients:

**Q_required = Q_reference × scaling_factor**

This applies to things such as:

* rice
* protein
* most vegetables
* onions
* seasonings

subject to ingredient-specific rules.

---

## Expected cooked rice quantity

The system should estimate:

**expected cooked rice = raw rice × rice expansion factor**

The expansion factor depends on rice variety and cooking method.

This is useful because the frying stage should operate on **cooked rice quantity**, not raw rice quantity.

---

## Required frying batches

The system calculates:

**number of frying batches = ceiling(expected cooked rice / frying_batch_capacity)**

This is a major non-linear scaling rule.

For example, doubling the recipe may produce two frying batches rather than one twice-as-large frying operation.

---

## Required cooking vessel

The system evaluates:

**required vessel capacity ≥ expected food volume + required mixing space**

If this condition fails, the system must divide the operation into batches.

---

# 8. Complete Procedural Specification

## STEP 1 — Initialize the recipe

### Purpose

Convert the desired serving count into all initial ingredient quantities and operating requirements.

### Required parameters

* desired servings
* reference servings
* reference ingredient quantities
* scaling rules
* rice variety
* protein type
* vessel capacity
* frying capacity

### Actions

Calculate:

**scaling factor = desired servings / reference servings**

Then calculate all proportional ingredients.

Determine:

* expected raw rice quantity
* expected cooked rice quantity
* expected protein quantity
* expected vegetable quantities
* expected seasoning quantities
* expected number of frying batches

### Completion condition

All required ingredients and equipment requirements have been determined.

### Failure condition

If the selected vessel cannot safely accommodate a cooking stage:

**THEN divide that stage into smaller batches.**

### Next step

Step 2.

---

# STEP 2 — Prepare the protein

### Purpose

Produce cooked, usable protein for incorporation into the fried rice.

### Parameters

* protein type
* protein quantity
* piece size
* seasoning quantity
* protein cooking liquid
* heat level
* cooking method
* cooking time

### Ingredient state

Protein:

**raw → cleaned → cut → seasoned → cooked**

### Actions

1. Clean and prepare the protein.
2. Cut it into the desired size.
3. Apply the calculated seasoning.
4. Add appropriate cooking liquid where required.
5. Cook until the protein reaches its required cooked state.
6. Remove and allow it to cool enough for handling.
7. Cut, shred, or cube it according to the final recipe specification.

### Temperature/heat

Use medium heat initially, adjusting according to protein type and cooking method.

### Duration

Runtime dependent.

The system should use a time range as an estimate, not the sole completion criterion.

### Completion condition

The protein must satisfy its protein-specific doneness condition.

For example:

* chicken: fully cooked
* liver: cooked through but not excessively dry

### Runtime decision

IF the expected cooking time has elapsed but the protein has not reached the required doneness:

**THEN continue cooking and reassess periodically.**

### Output variables

`cooked_protein`

`prepared_protein_quantity`

### Next step

Step 3.

---

# STEP 3 — Wash and prepare the rice

### Purpose

Prepare rice for cooking while controlling excess starch and moisture.

### Parameters

* raw rice quantity
* rice variety
* washing method
* optional soaking
* cooking liquid ratio
* salt
* pot capacity

### Ingredient state

Rice:

**raw → washed → drained**

### Actions

1. Measure the calculated rice quantity.
2. Wash according to the rice-specific preparation rule.
3. Drain excess washing water.
4. Prepare the calculated cooking liquid.

### Completion condition

Rice is clean and ready for cooking.

### Important runtime variable

`drained_rice_state`

The amount of water remaining on the rice after washing can affect the final cooking-liquid requirement.

### Next step

Step 4.

---

# STEP 4 — Cook the rice

### Purpose

Produce cooked rice with separate grains and sufficiently low surface moisture for subsequent frying.

### Parameters

* prepared rice
* rice variety
* cooking liquid
* salt
* pot capacity
* heat
* cooking time
* target rice texture

### Ingredient state

Rice:

**washed → cooking → cooked**

### Actions

1. Add rice to the cooking vessel.
2. Add the calculated cooking liquid.
3. Add initial salt.
4. Bring to the required cooking condition.
5. Cook until the rice reaches the required texture.
6. Reduce heat where appropriate during the absorption phase.
7. Stop cooking when the grains are cooked but not mushy.

### Critical completion condition

The rice must be:

* fully cooked
* separate enough for frying
* not excessively wet
* not mushy

### Runtime decision

IF rice is undercooked:

**AND sufficient liquid remains**

THEN continue cooking.

IF rice is undercooked:

**AND liquid is insufficient**

THEN add a controlled additional quantity of cooking liquid and continue cooking.

IF rice is fully cooked:

**AND excessive liquid remains**

THEN continue under controlled heat to remove excess liquid, or drain according to the rice-specific procedure.

IF rice becomes mushy:

**THEN terminate the cooking stage and mark the rice as below-target quality rather than continuing to add water.**

### Output variables

`cooked_rice`

`cooked_rice_quantity`

`rice_texture`

`rice_surface_moisture`

### Next step

Step 5.

---

# STEP 5 — Cool and condition the rice

### Purpose

Reduce excess surface moisture and make the rice suitable for frying.

### Parameters

* cooked rice quantity
* ambient conditions
* spreading area
* cooling time
* desired surface dryness

### Actions

Spread the cooked rice sufficiently to release steam and reduce surface moisture.

Avoid compressing the rice into a dense mass.

### Duration

Runtime dependent.

### Completion condition

Rice should be:

* cooked
* warm/cool enough to handle
* reasonably dry on the surface
* sufficiently separate for frying

### Runtime decision

IF rice remains excessively wet:

**THEN extend conditioning/cooling before frying.**

IF rice begins becoming excessively dry:

**THEN proceed to frying rather than continuing the conditioning stage.**

### Output

`conditioned_rice`

### Next step

Step 6.

---

# STEP 6 — Prepare vegetables

### Purpose

Convert raw/frozen vegetables into uniformly sized pieces suitable for frying.

### Parameters

For every vegetable:

* vegetable type
* quantity
* cut size
* starting state
* cooking tolerance

### Ingredient states

For example:

carrot:

**whole → washed → peeled → diced**

green beans:

**raw → trimmed → chopped**

bell pepper:

**whole → cleaned → diced**

### Actions

1. Clean vegetables where required.
2. Remove unusable portions.
3. Cut into specified sizes.
4. Keep vegetables separated or grouped according to their cooking requirements.

### Completion condition

All vegetables have the correct preparation state.

### Next step

Step 7.

---

# STEP 7 — Prepare the frying mixture

### Purpose

Create the seasoned vegetable/protein mixture that will receive the cooked rice.

### Parameters

* oil quantity
* onion quantity
* vegetables
* cooked protein
* curry
* thyme
* pepper
* seasoning
* salt
* frying temperature
* frying batch size

### Ingredient states

Onion:

**raw → chopped**

Vegetables:

**prepared → partially cooked**

Protein:

**cooked → frying-ready**

Seasonings:

**measured → ready**

### Actions

1. Heat the frying vessel.
2. Add the required oil.
3. Add onion.
4. Fry until softened.
5. Add appropriate vegetables.
6. Add the prepared protein.
7. Add seasoning and spices.
8. Stir continuously or periodically as appropriate.

### Heat

Typically medium to medium-high heat.

The actual heat is a runtime control variable.

### Completion condition

The mixture should be:

* hot
* aromatic
* vegetables sufficiently cooked
* vegetables still retaining appropriate texture
* protein heated
* seasoning distributed

### Runtime adjustment

IF vegetables begin browning excessively:

**THEN reduce heat.**

IF vegetables remain too raw:

**THEN continue frying.**

IF the mixture becomes dry and begins sticking:

**THEN add a small controlled quantity of oil or appropriate liquid only if necessary.**

### Output

`seasoned_frying_mixture`

### Next step

Step 8.

---

# STEP 8 — Add cooked rice

### Purpose

Combine the conditioned rice with the seasoned frying mixture.

### Parameters

* conditioned rice quantity
* frying mixture quantity
* frying batch size
* pan capacity
* heat level
* mixing method

### Actions

Add rice progressively rather than necessarily dumping the entire quantity into the pan.

Mix so that:

* rice is coated with the seasoning
* vegetables are distributed
* protein is distributed
* rice grains remain intact

### Critical batch rule

IF:

**rice quantity > frying_batch_capacity**

THEN divide rice and frying mixture into multiple frying batches.

Do **not** compensate for an undersized pan merely by increasing cooking time.

### Next step

Step 9.

---

# STEP 9 — Fry the combined rice

### Purpose

Produce the characteristic fried-rice flavor, color, dryness, and texture.

### Parameters

* combined rice
* oil
* heat
* pan capacity
* frying time
* desired color
* desired moisture
* desired grain separation

### Actions

1. Maintain appropriate heat.
2. Stir or toss the rice periodically.
3. Ensure seasoning is distributed.
4. Allow excess moisture to escape.
5. Monitor the rice continuously.

### Duration

Use a runtime range rather than a fixed value.

For example:

**initial frying period → inspect → continue/reduce heat as necessary**

### Completion conditions

The rice is complete when:

* grains are fully cooked
* grains remain reasonably separate
* vegetables have the required texture
* protein is evenly distributed
* seasoning is evenly distributed
* excess moisture has been reduced
* desired color has been achieved
* flavor is balanced

### Runtime decisions

IF rice is too wet:

**THEN continue frying while controlling heat and stirring.**

IF rice is dry but still under-seasoned:

**THEN adjust seasoning in small increments.**

IF rice begins sticking:

**THEN inspect heat and available oil.**

IF rice begins burning:

**THEN immediately reduce heat and, if necessary, transfer the unaffected food to another vessel.**

IF rice is cooked and target texture is achieved:

**THEN stop frying.**

### Output

`finished_fried_rice`

### Next step

Step 10.

---

# STEP 10 — Final seasoning and quality validation

### Purpose

Ensure the finished product satisfies the target specification.

### Parameters

* salt level
* spice level
* color
* texture
* moisture
* vegetable firmness
* protein distribution
* serving temperature

### Actions

Evaluate the finished rice.

The system should evaluate:

**Texture**

Is the rice cooked and reasonably separate?

**Moisture**

Is it excessively wet?

**Seasoning**

Is the flavor sufficiently seasoned?

**Vegetables**

Are they cooked but not excessively soft?

**Protein**

Is it evenly distributed?

**Color**

Does it match the desired fried-rice profile?

### Runtime corrections

IF seasoning is insufficient:

**THEN add a small controlled quantity of seasoning, mix thoroughly, and reassess.**

IF salt is excessive:

The system should not simply continue adding ingredients indefinitely. It should apply a correction strategy appropriate to the batch.

IF moisture is excessive:

**THEN continue controlled frying if the rice texture permits.**

IF texture is correct:

**THEN stop cooking.**

### Completion condition

The recipe is complete when all target quality conditions are satisfied.

---

# 9. Decision and Exception Rules

The expert system should contain rules like these rather than relying exclusively on predetermined times.

### Rice too dry during cooking

IF:

`rice_texture != cooked`

AND

`available_cooking_liquid < required_liquid`

THEN:

1. add a controlled amount of liquid;
2. continue cooking;
3. reassess texture.

---

### Rice too wet

IF:

`rice_texture = cooked`

AND

`surface_moisture > target_surface_moisture`

THEN:

1. continue controlled heating or conditioning;
2. reassess moisture;
3. proceed to frying when acceptable.

---

### Pan too small

IF:

`required_batch_quantity > vessel_capacity`

THEN:

1. calculate batch count;
2. divide ingredients;
3. execute frying procedure independently for each batch.

---

### Vegetables undercooked

IF:

`vegetable_texture < target_texture`

THEN:

continue frying and reassess periodically.

---

### Vegetables overcooking

IF:

`vegetable_texture > target_texture`

THEN:

reduce heat or terminate the vegetable-frying stage.

---

### Food sticking

IF:

`sticking_detected = true`

THEN evaluate:

* heat
* oil quantity
* vessel condition
* moisture

Then correct the relevant variable.

---

### Burning

IF:

`burning_detected = true`

THEN:

1. reduce heat;
2. stop aggressive stirring if it would mix burnt material into the food;
3. transfer unaffected food where necessary;
4. continue using a clean/appropriate vessel.

---

# 10. Parameters That Scale Directly

These generally use:

**Q = Q_reference × scaling_factor**

Examples:

* raw rice quantity
* protein quantity
* carrots
* peas
* green beans
* sweet corn
* bell pepper
* onion
* most seasonings

These are fundamentally **quantity variables**.

---

# 11. Parameters That Do NOT Scale Directly

Several important parameters require special rules.

### Cooking time

Doubling the ingredients does not normally double cooking time.

Instead:

**cooking time = function of ingredient type, piece size, heat, vessel, quantity and observed state**

---

### Cooking temperature

Does not double with quantity.

Temperature remains within an appropriate operating range.

---

### Heat level

Does not scale linearly.

A larger batch may require:

* greater burner output
* multiple batches
* different vessel geometry

rather than simply "more heat."

---

### Water

Water is based on:

**rice quantity × rice-specific liquid ratio**

but must also account for:

* rice variety
* residual moisture
* evaporation
* vessel geometry
* cooking method

---

### Oil

Oil depends on:

* food quantity
* pan surface
* batch size
* desired coating
* moisture

Therefore it should have a **base quantity + runtime adjustment** model.

---

### Vessel size

Does not scale proportionally with servings.

It is a physical constraint.

---

### Frying batch size

Must obey:

**batch quantity ≤ effective frying capacity**

This is one of the most important rules for large-scale generation.

---

# 12. Runtime vs Precomputed Variables

The system can divide its variables into three classes.

## Precomputed

Known before cooking:

* desired servings
* scaling factor
* ingredient quantities
* rice variety
* protein type
* cut sizes
* estimated cooking liquid
* estimated cooking times
* estimated batch count
* vessel requirements

---

## Runtime observations

Cannot reliably be known beforehand:

* actual rice moisture
* actual rice tenderness
* actual evaporation
* actual vegetable tenderness
* actual sticking
* actual browning
* actual seasoning balance
* actual final consistency

These must be evaluated during cooking.

---

## Runtime-adjusted parameters

Initially calculated but allowed to change:

* cooking liquid
* oil
* heat
* cooking duration
* frying duration
* seasoning
* batch size
* conditioning time

This is where the expert-system behavior becomes important.

---

# 13. Overall Procedural State Machine

The complete process can therefore be represented conceptually as:

**INITIALIZE**

→ calculate quantities
→ validate equipment

**PREPARE PROTEIN**

→ cook
→ validate doneness
→ produce `cooked_protein`

**PREPARE RICE**

→ wash
→ calculate liquid
→ cook
→ validate texture
→ produce `cooked_rice`

**CONDITION RICE**

→ reduce surface moisture
→ validate frying suitability

**PREPARE VEGETABLES**

→ clean
→ cut
→ group by cooking requirements

**FRY MIXTURE**

→ oil
→ aromatics
→ vegetables
→ protein
→ seasoning
→ produce `seasoned_frying_mixture`

**COMBINE**

→ add rice
→ respect batch capacity

**FRY**

→ heat
→ mix
→ evaporate excess moisture
→ adjust seasoning
→ validate texture

**FINALIZE**

→ validate all target conditions
→ serve

---

# 14. Example: Changing the Serving Size

Suppose the reference recipe produces **4 servings**.

For **8 servings**:

**scaling factor = 8 / 4 = 2**

Therefore the proportional ingredients become 2× their reference quantities.

If the reference contains 2 cups of rice:

**2 × 2 = 4 cups raw rice**

If the reference contains 300 g protein:

**300 × 2 = 600 g protein**

If the reference contains ½ cup peas:

**0.5 × 2 = 1 cup peas**

However, the system should **not** say:

> "Cook everything for twice as long."

Instead, it should determine whether the larger quantity exceeds the cooking/frying vessel capacity.

If the frying vessel can effectively fry only the equivalent of 4 servings at a time, the 8-serving batch becomes:

**Batch 1 → 4 servings**

**Batch 2 → 4 servings**

The ingredients scale approximately 2×, while the **frying operation scales by increasing the number of batches**, not by simply making one enormous frying operation.

That distinction is fundamental to a good cooking expert system: **the recipe quantity can scale mathematically, while the physical cooking process must obey constraints imposed by heat transfer, evaporation, vessel capacity, ingredient properties, and observed food state.**
