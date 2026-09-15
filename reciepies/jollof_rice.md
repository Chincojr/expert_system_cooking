# Parameterized Jollof Rice Cooking Procedure

This procedure describes how to prepare Nigerian jollof rice using a parameterized expert system. The system receives the required parameters, calculates ingredient quantities, and generates the cooking instructions in the correct sequence.

The procedure uses long-grain parboiled rice as its reference recipe. Other rice types can be accommodated by changing the relevant parameters and cooking rules.

## 1. Define the input parameters

Before generating the cooking procedure, the system must receive the following parameters:

Recipe parameters: rice type, cooking method, cooking style, and desired spice level.

Equipment parameters: Cooking pot capacity, stove heat settings, blender capacity, and available cooking time.

Ingredient parameters: Reference quantities of rice, tomatoes, bell peppers, scotch bonnet peppers, onions, tomato paste, vegetable oil, stock, curry powder, thyme, seasoning cubes, and salt, bay leaf.

Cooking parameters: Liquid-to-rice ratio, sauce consistency target, rice tenderness target, initial cooking duration, additional cooking duration, resting duration, and liquid reserve.

These parameters provide the information required to generate the recipe and determine how the cooking procedure should behave.

Note the main ingredient is the rice everything else is relative to the rice

## 2. Calculate ingredient quantities

Rice is the main ingredient and everuthing else is relative to it. The proportionality in respect to other ingredient varies by ingredient

Within the system I need a place where I can define the relationship between each ingredient and rice. Note: they do not share proportionality

Note use ranges when the quantity of ingredient excluding (rice) is a decimal

Ingredients that require special treatment, such as salt, pepper, and cooking liquid, must be adjusted using their own rules rather than being scaled blindly.

## 3. Prepare the ingredients

The system generates an instruction to measure the calculated quantities of all ingredients.

The rice is washed and drained. The tomatoes, bell peppers, scotch bonnet peppers, and onions are washed and cut into pieces suitable for blending.

The system must identify the quantity of onion required for blending and the quantity reserved for frying.

The preparation stage is complete when all ingredients have been measured and prepared.

## 4. Blend the pepper mixture

The system generates an instruction to place the prepared tomatoes, bell peppers, scotch bonnet peppers, and the specified quantity of onion into a blender.

The ingredients are blended until smooth.

If the mixture is too thick to blend, the system may instruct the cook to add a small quantity of water and blend again.

The amount of water added during blending must be recorded because it contributes to the total liquid available for cooking the rice.

The blending stage is complete when the pepper mixture reaches the required consistency.

## 5. Fry the onions and tomato paste

The system generates an instruction to heat the cooking pot over medium heat and add the calculated quantity of vegetable oil.

The remaining sliced onions are added and fried until softened.

The calculated quantity of tomato paste is then added and fried for approximately 3–5 minutes while stirring regularly.

The system uses the condition of the onions and tomato paste to determine when to proceed to the next stage.

## 6. Cook the blended pepper mixture

The system generates an instruction to add the blended pepper mixture to the fried onion and tomato paste.

The mixture is stirred thoroughly and cooked uncovered over medium heat for approximately 15–20 minutes.

The system evaluates the sauce consistency and determines whether additional cooking is required.

If the sauce is still watery, the system instructs the cook to continue reducing it. If the sauce begins sticking excessively, the system instructs the cook to reduce the heat and stir.

The stage is complete when the sauce has thickened sufficiently and the raw tomato taste has reduced.

The quantity and consistency of the cooked sauce become inputs to the next stage.

## 7. Season the sauce and calculate the cooking liquid

The system generates an instruction to add the calculated quantities of curry powder, thyme, seasoning cubes, salt, and optional bay leaf.

The initial calculated quantity of stock is added, and the sauce is stirred thoroughly.

The system then calculates the initial liquid requirement using the selected rice type and the appropriate liquid-to-rice ratio.

The initial liquid requirement is calculated by multiplying the rice quantity by the calibrated liquid-to-rice ratio.

The system must also account for liquid already present in the sauce and any water added during blending.

The remaining liquid to add is determined by subtracting the liquid already present from the target initial liquid quantity.

The sauce is tasted and adjusted for seasoning before the rice is introduced.

The stage is complete when the sauce is properly seasoned and the initial cooking liquid has been determined.

## 8. Add the rice and begin cooking

The system generates an instruction to add the washed and drained rice to the seasoned sauce.

The rice is stirred until evenly coated.

Before cooking begins, the system checks whether the cooking pot has sufficient capacity for the rice, sauce, and liquid.

If the batch exceeds the pot's capacity, the system instructs the cook to divide the recipe into smaller batches.

The pot is covered tightly, and the heat is reduced to medium.

The system generates an initial cooking duration appropriate to the selected rice type and cooking method.

For the reference stovetop procedure, the initial cooking period is approximately 20-30 minutes.Depending on rice type, the main goal is to check if the rice has softened.

The stage is complete when the initial cooking period has elapsed and the rice is ready for inspection.

## 9. Inspect and adjust the cooking liquid

The system generates an instruction to inspect the rice's tenderness and the amount of liquid remaining.

If the rice is still hard and the liquid has been absorbed, the system calculates a small additional quantity of hot water or stock.

The calculated quantity is added, the pot is covered, and cooking continues over low heat.

If the rice is still hard but sufficient liquid remains, the system instructs the cook to continue cooking without adding more liquid.

If the rice is tender and the liquid has been absorbed, the system proceeds to the finishing stage.

If the rice is tender but excess liquid remains, the system applies the appropriate finishing rule for the selected rice type and cooking method.

This stage is repeated until the rice reaches the required tenderness and cooking-liquid conditions.

## 10. Finish the rice

The system generates the finishing instructions according to the selected cooking style.

For regular jollof rice, the system instructs the cook to turn off the heat and leave the pot covered for approximately 5–10 minutes.

For party-style jollof rice, the system may generate an additional controlled low-heat stage to develop a lightly smoky flavour.

The system must ensure that the rice is not left over excessive heat, which could cause burning.

After resting, the bay leaf is removed and the rice is gently fluffed.

The procedure is complete when the rice is tender, the cooking liquid has been absorbed, and the rice is ready to serve.

## 11. Additional parameters required for reliable operation

The system should maintain several additional parameters to improve the reliability of the generated procedure.

The rice absorption rate represents how much liquid the selected rice requires. The evaporation rate estimates how much liquid is lost during cooking. The sauce water content represents the liquid already present in the cooked sauce.

The pot surface area helps estimate evaporation, while the pot capacity determines whether the entire batch can be cooked together.

The ingredient rounding rules determine how fractional quantities are converted into practical measurements. For example, a calculated quantity of 2.5 seasoning cubes may be represented as two and a half cubes or an equivalent measured quantity of seasoning powder. Do not use decimal amounts for ingredients. Use range. e.g Instead of 2.65 tbsp, you can use 2-3 tbsp. For 2.25, use 2.

The batch size limit determines when a recipe must be divided into multiple cooking batches.

These parameters allow the system to handle differences in ingredients, equipment, and batch size without relying entirely on fixed instructions.

## 12. Final procedure-generation logic

The expert system should begin by receiving the input parameters and retrieving the appropriate reference recipe.


The system checks the cooking equipment, calculates the initial liquid requirement, and generates the ordered cooking instructions.

Each generated instruction contains the required ingredients, their calculated quantities, the actions to perform, the applicable cooking duration, and the condition that determines when the next step should begin.

During cooking, the system uses the observed sauce consistency, rice tenderness, and remaining liquid to determine whether additional actions are necessary.

The procedure terminates when the rice satisfies the defined completion conditions.

The central design principle is that the recipe is a parameterized sequence of actions, not a fixed list of quantities and instructions. The parameters determine the required amounts, while the procedural rules determine which actions are performed and when the system advances to the next stage.

The proportional relationship of ingredients in respect to rice, is what defines their quantity. Note: the proportional relationship has not been defined, but the system should create space such that it can be inserted/created/modified as needed by the programmer.