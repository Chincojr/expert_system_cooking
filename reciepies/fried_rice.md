# Parameterized Nigerian Fried Rice Cooking Procedure

This procedure describes how to prepare Nigerian fried rice using a parameterized expert system. The system receives the required parameters, calculates ingredient quantities, and generates the cooking instructions in the correct sequence.

The procedure uses long-grain parboiled rice as its reference recipe. Other rice types can be accommodated by changing the relevant parameters and cooking rules.

The main ingredient is rice. All other ingredients are defined relative to the quantity of rice, but each ingredient has its own independent proportional relationship with rice. These relationships are not predefined in this specification; the programmer must provide a configurable place to define, create, or modify them.

The procedure focuses on Nigerian-style fried rice prepared with vegetables, stock, seasonings, and a controlled frying process.

## 1. Define the input parameters

Before generating the cooking procedure, the system must receive the following parameters.

Recipe parameters: Rice type, cooking method, cooking style, desired spice level, desired vegetable variety, and desired rice texture.

Equipment parameters: Cooking pot capacity, frying pan or wok capacity, stove heat settings, available cooking time, and available cooking utensils.

Ingredient parameters: Reference quantities of rice, carrots, green beans, green peas, sweet corn, green bell peppers, scotch bonnet pepper, onions, vegetable oil, stock, curry powder, thyme, seasoning cubes, salt, and optional ingredients such as liver, chicken, spring onions, and bay leaves.

Cooking parameters: Rice-to-liquid ratio, rice tenderness target, initial rice cooking duration, vegetable tenderness target, vegetable frying duration, rice cooling duration, final frying duration, resting duration, and liquid reserve.

Ingredient allocation parameters: The proportion of onions reserved for frying, the quantity of stock allocated to cooking the rice, the quantity of stock reserved for seasoning adjustments, and the quantities of vegetables allocated to different cooking stages.

These parameters provide the information required to generate the procedure and determine how the cooking process should behave.

## 2. Calculate ingredient quantities

Rice is the main ingredient, and every other ingredient is calculated relative to it.

The system must provide a configurable relationship for each ingredient, rather than applying one proportionality factor to all ingredients.

For example, the relationship for carrots must be independent of the relationship for green beans, and the relationship for vegetable oil must be independent of the relationship for seasoning cubes.

The programmer should provide a place where each relationship can be defined and modified. The system should retrieve the appropriate relationship when calculating the ingredient quantities.

The relationship may be expressed as a reference quantity per reference quantity of rice, a range, or another configurable rule.

The system should calculate the required quantities of:

* Carrots, green beans, green peas, sweet corn, and green bell peppers.

* Onions and optional spring onions.

* Vegetable oil.

* Stock.

* Curry powder, thyme, seasoning cubes, and salt.

* Optional protein ingredients and bay leaves.

The quantities of salt, seasoning cubes, stock, and spicy ingredients must be adjusted using their own rules rather than being scaled blindly.

The system must also account for practical measurement limitations. Decimal quantities should be converted into usable measurement ranges or rounded according to the ingredient's own rounding rule.

For example, a calculated quantity of 2.65 tablespoons may be represented as 2–3 tablespoons, while a quantity of 2.25 tablespoons may be represented as 2 tablespoons when the selected rounding rule permits it.

No ingredient proportionality is fixed in this specification. All ingredient relationships remain configurable.

## 3. Prepare the ingredients

The system generates an instruction to measure the calculated quantities of all ingredients.

The rice is washed and drained. The system should determine whether the selected rice type requires additional washing or soaking according to its preparation rules.

The carrots are washed, peeled if necessary, and diced into small, relatively uniform pieces.

The green beans are washed, trimmed, and cut into small pieces. The green bell peppers are washed, deseeded if required, and diced. The green peas and sweet corn are measured and drained if canned or previously frozen.

The onions are peeled and chopped or sliced according to the selected cooking style. The system identifies the quantity of onion required for frying and the quantity reserved for any optional finishing stage.

If liver or another protein ingredient is included, the system generates separate preparation instructions appropriate to that ingredient. Raw protein must be handled separately from ready-to-eat ingredients.

The system also determines whether the vegetables should be grouped according to their cooking requirements. For example, firmer vegetables may be assigned to an earlier frying stage than softer vegetables.

The preparation stage is complete when all ingredients have been measured, prepared, and allocated to their respective cooking stages.

## 4. Prepare the rice cooking liquid

The system generates an instruction to prepare the stock or cooking liquid required for the selected rice type.

If the stock is homemade or prepared separately, the system must ensure that it is ready before the rice cooking stage begins.

The system calculates the initial cooking liquid using the selected rice type and its calibrated rice-to-liquid ratio.

The initial liquid requirement is calculated by multiplying the quantity of rice by the selected liquid-to-rice ratio.

The system must account for liquid already present in the stock and any additional water introduced during rice preparation, where relevant.

If the stock is already seasoned, the system must account for its seasoning contribution when calculating the quantities of salt and seasoning cubes.

The system should reserve an appropriate quantity of hot stock or water for possible adjustments during cooking.

The stage is complete when the initial cooking liquid and the liquid reserve have been determined.

## 5. Cook the rice

The system generates an instruction to place the measured rice into the appropriate cooking pot and add the calculated quantity of stock or cooking liquid.

The system may add a portion of the calculated curry powder, thyme, onions, and other permitted seasonings at this stage, depending on the selected cooking style.

The ingredients are stirred gently to distribute the liquid and seasonings evenly.

The pot is covered and heated according to the selected cooking method.

For the reference stovetop procedure, the system brings the liquid to a boil and then reduces the heat to a level that maintains a gentle simmer.

The system generates an initial cooking duration appropriate to the selected rice type and cooking method.

During cooking, the system must monitor or request observations about the amount of remaining liquid and the tenderness of the rice.

The objective is to cook the rice until it is sufficiently tender for the subsequent frying stage, while avoiding excessive softness.

The stage is complete when the rice reaches the specified pre-frying tenderness target and the cooking liquid has been absorbed or reduced to the required level.

## 6. Inspect and adjust the cooked rice

The system generates an instruction to inspect the cooked rice.

If the rice is still hard and the liquid has been absorbed, the system calculates a small additional quantity of hot stock or water.

The calculated quantity is added, the pot is covered, and cooking continues over low heat.

If the rice is still hard but sufficient liquid remains, the system instructs the cook to continue cooking without adding more liquid.

If the rice is tender and the liquid has been absorbed, the system proceeds to the cooling stage.

If the rice is tender but excess liquid remains, the system applies the appropriate adjustment rule for the selected rice type.

The system must avoid allowing the rice to become excessively soft, because the subsequent frying process requires rice that can be stirred without breaking apart easily.

This stage is repeated until the rice reaches the required tenderness and moisture conditions.

## 7. Cool and separate the rice

The system generates an instruction to transfer the cooked rice into a suitable shallow container or tray, where appropriate.

The rice is spread out to allow excess steam to escape.

The system determines the required cooling duration based on the quantity of rice, the available cooling equipment, and the desired moisture condition.

If the selected procedure uses freshly cooked rice directly, the system applies the corresponding frying rule instead of requiring a separate cooling stage.

The system should identify whether the rice is:

* Too wet for the selected frying method.

* Sufficiently dry and separated for frying.

* Too dry and in need of a controlled moisture adjustment.

The rice should be handled gently to minimize breakage.

If the rice is prepared in advance, the system must apply the appropriate food-safety rules for cooling, storage, and reheating. Rice intended for later use should not be left at room temperature for an extended period.

The stage is complete when the rice reaches the required pre-frying condition.


## 8. Fry the onions and optional protein ingredients

The system generates an instruction to heat the frying pan or wok over medium heat and add the calculated quantity of vegetable oil.

The system must check whether the selected pan has sufficient capacity for the ingredients assigned to this stage.

The reserved quantity of onions is added to the heated oil and fried until softened and fragrant.

If liver or another suitable protein ingredient is included, the system generates the appropriate cooking instructions for that ingredient.

The system must determine whether the protein should be cooked separately before the vegetables are introduced or whether it can be safely cooked in the same pan.

For liver, the system must ensure that it is thoroughly cooked before proceeding. The cooking duration depends on the ingredient, its size, and the cooking method.

If the selected cooking style does not include protein, this stage is limited to frying the onions.

The stage is complete when the onions are softened and any included protein has reached its required cooking condition.

## 9. Fry the vegetables

The system generates an instruction to add the prepared vegetables to the fried onions and optional protein ingredients.

The vegetables are stirred to distribute the oil and allow them to cook evenly.

The system determines the order in which the vegetables are added according to their cooking requirements.

Firmer vegetables, such as carrots and green beans, may be introduced before softer vegetables, such as green peas, sweet corn, and green bell peppers.

The system generates a frying duration for each vegetable group according to the selected cooking style and desired vegetable tenderness.

The vegetables are fried over medium heat while being stirred regularly.

The system evaluates the condition of the vegetables and determines whether additional frying is required.

If the vegetables remain too firm, the system instructs the cook to continue frying.

If the vegetables begin to soften excessively or release too much liquid, the system instructs the cook to adjust the heat and proceed according to the applicable vegetable-handling rule.

The objective is to retain the desired vegetable texture without producing excessive liquid that could make the fried rice soggy.

The stage is complete when the vegetables reach the specified tenderness target and are ready to be combined with the rice.

The quantity and moisture condition of the fried vegetables become inputs to the next stage.

## 10. Season the vegetables

The system generates an instruction to add the calculated quantities of curry powder, thyme, seasoning cubes, salt, and any other selected seasonings to the fried vegetables.

The system must account for any seasonings already introduced during the rice cooking stage.

The seasonings are stirred into the vegetables and cooked briefly to distribute their flavour.

The system evaluates the seasoning level and determines whether an adjustment is required.

If the seasoning is insufficient, the system calculates an additional quantity using the relevant seasoning adjustment rule.

If the mixture is excessively salty or strongly seasoned, the system applies the appropriate correction rule.

The system must account for the seasoning contribution of the stock, protein ingredients, and any previously added seasoning cubes.

The stage is complete when the vegetable mixture is properly seasoned and ready for the addition of rice.

## 11. Combine the rice and vegetables

The system generates an instruction to add the cooked rice to the fried vegetable mixture.

If the quantity of rice exceeds the capacity of the frying pan, the system divides the recipe into smaller frying batches.

The rice is added in portions where necessary, and each portion is gently stirred into the vegetables.

The system must ensure that the rice is evenly distributed throughout the mixture without excessive stirring that could break the grains.

The system may instruct the cook to add the rice in multiple portions, depending on the batch size and available frying equipment.

If the rice is too dry to combine properly, the system may calculate a small quantity of hot stock or water for adjustment.

If the rice is too wet, the system applies the appropriate moisture-reduction rule before proceeding.

The stage is complete when the rice and vegetables are evenly combined and the mixture has reached the required distribution and moisture conditions.

## 12. Fry the combined rice

The system generates an instruction to fry the combined rice and vegetables over the selected heat setting.

The rice is stirred gently and regularly to distribute the heat and seasonings.

The system generates an initial frying duration according to the quantity of rice, frying pan capacity, cooking method, and desired final texture.

For the reference stovetop procedure, the frying stage uses medium heat, with adjustments according to the condition of the rice and vegetables.

The system must evaluate the following conditions:

* Whether the rice is evenly heated.

* Whether the vegetables are distributed throughout the rice.

* Whether the rice has reached the required moisture condition.

* Whether the rice is sticking excessively to the pan.

* Whether the rice is becoming too soft or breaking apart.

If the rice is insufficiently heated, the system instructs the cook to continue frying.

If the rice begins sticking excessively, the system instructs the cook to reduce the heat and stir gently.

If the mixture becomes too dry, the system may calculate a small quantity of hot stock or water, subject to the selected rice and moisture rules.

The system should avoid adding unnecessary liquid, as excessive moisture can reduce the desired fried-rice texture.

The stage is complete when the rice is evenly heated, properly seasoned, and has reached the specified final texture.

## 13. Adjust the final seasoning and texture

The system generates an instruction to inspect the finished fried rice and evaluate its seasoning, moisture, and texture.

If the seasoning is insufficient, the system calculates the required adjustment using the relevant ingredient-specific rule.

If the rice is too dry, the system determines whether a small quantity of hot stock or water is appropriate.

If the rice is too moist, the system determines whether additional uncovered frying is required.

If the rice is too soft, the system avoids unnecessary additional liquid and stirring.

The system must account for the fact that additional frying can increase moisture loss and alter the texture of the vegetables.

The stage is complete when the rice reaches the required seasoning, moisture, and texture targets.

## 14. Finish the fried rice

The system generates the finishing instructions according to the selected cooking style.

For regular Nigerian fried rice, the system instructs the cook to turn off the heat once the rice has reached the required condition.

The rice may be left briefly to settle before serving.

If spring onions or another optional finishing ingredient is included, the system generates an instruction to add it at the appropriate stage.

The system must ensure that any optional ingredient requiring cooking receives the appropriate treatment.

The fried rice is gently stirred or fluffed to distribute the vegetables and separate the grains.

If the selected cooking style includes a final frying stage intended to develop additional flavour, the system generates the corresponding controlled heat and duration parameters.

The system must ensure that the rice is not left over excessive heat, which could cause burning or excessive moisture loss.

The procedure is complete when the rice is properly seasoned, evenly heated, sufficiently dry, and ready to serve.


## 15. Additional parameters required for reliable operation

The system should maintain several additional parameters to improve the reliability of the generated procedure.

Rice absorption rate: Represents how much liquid the selected rice requires during cooking. It must be calibrated for the rice type and cooking method.

Rice moisture condition: Represents the amount of moisture remaining in the cooked rice before frying. This parameter helps determine whether the rice is ready for frying or requires further adjustment.

Vegetable moisture contribution: Estimates the amount of liquid released by the selected vegetables during frying. Different vegetables may contribute different amounts of moisture.

Vegetable cooking characteristics: Defines the cooking requirements of each vegetable, including its tenderness target, approximate cooking duration, and appropriate stage of introduction.

Ingredient proportionality rules: Defines the independent relationship between each ingredient and rice. These rules must be configurable, allowing the programmer to define or modify the quantities of carrots, green beans, vegetable oil, stock, seasonings, and other ingredients separately.

Ingredient allocation rules: Determines how each ingredient is distributed across the preparation, rice cooking, vegetable frying, and finishing stages.

Rice cooling parameters: Defines the required cooling condition, cooling method, and maximum permitted cooling time before the rice is used or stored.

Frying heat parameters: Defines the appropriate heat settings for frying onions, vegetables, and the combined rice mixture.

Pan capacity and surface area: Determines whether the ingredients can be fried together without overcrowding the pan. Pan surface area also affects heat distribution and moisture evaporation.

Evaporation rate: Estimates how much liquid is lost during rice cooking and frying. The rate depends on the equipment, heat setting, cooking duration, and whether the pan is covered.

Ingredient rounding rules: Determines how fractional quantities are converted into practical measurements.

For example, a calculated quantity of 2.65 tablespoons of curry powder may be represented as 2–3 tablespoons, while 2.25 tablespoons may be represented as 2 tablespoons if the selected rounding rule permits it.

The system must not use decimal quantities in the generated ingredient instructions. Where a calculated quantity is fractional, it should use an appropriate measurement range or the applicable rounding rule.

Batch size limit: Determines when the rice or vegetable mixture must be divided into smaller batches for cooking or frying.

Completion conditions: Defines the required final rice tenderness, vegetable tenderness, seasoning level, moisture condition, and temperature condition.

These parameters allow the system to accommodate different ingredients, equipment, batch sizes, and cooking preferences without relying entirely on fixed instructions.

## 16. Final procedure-generation logic

The expert system should begin by receiving the input parameters and retrieving the appropriate reference recipe.

The system identifies rice as the primary ingredient and retrieves the independently configured proportionality relationship for every other ingredient.

It calculates the required quantities, applies the ingredient-specific rounding and adjustment rules, and allocates ingredients to their appropriate cooking stages.

The system checks the available equipment and determines whether the recipe can be prepared in a single batch or requires multiple batches.

It then generates the ordered cooking instructions, beginning with ingredient preparation and proceeding through rice cooking, vegetable frying, combining, final frying, and finishing.

Each generated instruction contains:

* The required ingredients and their calculated quantities.

* The actions to perform.

* The applicable cooking method and heat setting.

* The expected cooking duration or observation interval.

* The condition that determines when the next step should begin.

* The adjustment rule to apply if the expected condition is not satisfied.

During cooking, the system uses observed rice tenderness, vegetable condition, remaining liquid, moisture level, and equipment capacity to determine whether additional actions are necessary.

The system must also maintain the state of the procedure so that an adjustment in one stage can affect the instructions generated in subsequent stages.

For example, if additional stock is introduced during rice cooking, the system must account for that liquid when determining whether further liquid is required. Similarly, if the vegetables release more moisture than expected, the system must consider that moisture when determining the final frying duration.

The procedure terminates when the rice satisfies the defined completion conditions.

The central design principle is that the recipe is a parameterized sequence of actions, not a fixed list of quantities and instructions.

The quantity of each ingredient is defined by its own configurable relationship with rice, while the procedural rules determine how, when, and under what conditions that ingredient is used.
