"""Plain-assert checks for the ExpertCook engine (no pytest needed).

Run with:  venv/Scripts/python.exe selftest.py
"""

from expertcook import scaling
from expertcook import proportions as props
from expertcook.planner import build_plan
from expertcook.recipes import DISHES, PARAM_SPECS


def _steps_text(plan):
    return "\n".join(s["text"] for s in plan["steps"])


def _phases(plan):
    return [s["phase"] for s in plan["steps"]]


def _ingredient(plan, key):
    return next(i for i in plan["ingredients"] if i["key"] == key)


def _expect_value_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---------------------------------------------------------------------------
# Rounding rules (spec: no decimal quantities are ever shown)
# ---------------------------------------------------------------------------

def test_rounding_rules():
    assert scaling.round_count(3.2) == 3
    assert scaling.round_count(0.4) == 1          # minimum 1
    assert scaling.round_half(2.25) == 2.0
    assert scaling.round_half(2.6) == 2.5
    assert scaling.round_half(0.1) == 0.5         # minimum 1/2
    assert scaling.round_quarter(0.62) == 0.5
    assert scaling.round_quarter(0.68) == 0.75
    assert scaling.round_grams(430) == 450
    assert scaling.round_grams(20) == 50          # minimum 50
    assert scaling.round_grams(321.7) == 300


def test_round_range_rule():
    # spec: 2.65 tbsp -> "2-3 tbsp", 2.25 tbsp -> "2 tbsp", 2.75 -> "3 tbsp"
    assert scaling.round_range(2.65) == (2, 3)
    assert scaling.round_range(2.25) == 2
    assert scaling.round_range(2.75) == 3
    assert scaling.round_range(0.05) == 1         # ~whole -> min 1
    assert scaling.round_range(1.5) == (1, 2)
    assert scaling.qty((2, 3), "tbsp") == "2-3 tbsp"
    assert scaling.qty(2, "tbsp") == "2 tbsp"


def test_qty_formatting():
    assert scaling.qty(7.5, "cups") == "7 1/2 cups"
    assert scaling.qty(1, "cups") == "1 cup"      # singular
    assert scaling.qty(0.25, "cups") == "1/4 cup" # fractions are singular too
    assert scaling.qty(1.5, "cups") == "1 1/2 cups"
    assert scaling.qty(1, "tbsp") == "1 tbsp"
    assert scaling.qty(1, "medium") == "1 medium"
    assert scaling.fmt(3.0) == "3"
    assert scaling.fmt(2.5) == "2.5"
    assert scaling.fmt(0.25) == "0.25"


# ---------------------------------------------------------------------------
# Proportionality file (proportions.json)
# ---------------------------------------------------------------------------

def test_proportions_file_loads_and_validates():
    dishes = props.list_dishes()
    assert set(dishes) >= {"jollof", "fried_rice"}, dishes
    for dish in dishes:
        assert props.validate(dish) is True
        ing = props.dish_ingredients(dish)
        assert len(ing) > 0
        for key, rule in ing:
            assert rule.get("special") or "per_rice" in rule, key
        rt = props.rice_types(dish)
        assert "parboiled" in rt and "basmati" in rt and "other" in rt
        for variety in rt:
            assert rt[variety]["liquid_ratio"] > 0


def test_recipes_do_not_share_parameters():
    # individual recipes: jollof and fried rice ask for different params
    jollof_names = [s["name"] for s in PARAM_SPECS["jollof"]]
    fried_names = [s["name"] for s in PARAM_SPECS["fried_rice"]]
    assert "style" in jollof_names and "style" not in fried_names
    assert "pot_capacity" in jollof_names and "pot_capacity" not in fried_names
    assert "frying_capacity" in fried_names and "frying_capacity" not in jollof_names
    # and independent ingredient sets
    jollof_ing = dict(props.dish_ingredients("jollof"))
    fried_ing = dict(props.dish_ingredients("fried_rice"))
    assert "tomatoes" in jollof_ing and "tomatoes" not in fried_ing
    assert "carrots" in fried_ing and "carrots" not in jollof_ing


# ---------------------------------------------------------------------------
# Rice-relative computation (rice is the base)
# ---------------------------------------------------------------------------

def test_jollof_rice_relative_amounts():
    # rice x per_rice, each with its own rounding rule
    plan = build_plan("jollof", {"rice_cups": 3})
    c = plan["calc"]
    assert c["rice_cups"] == 3
    # tomatoes: 3 x 1.33 = 3.99 -> round_count -> 4
    assert c["ing"]["tomatoes"]["amount"] == 4
    # bell peppers: 3 x 0.67 = 2.01 -> 2
    assert c["ing"]["bell_peppers"]["amount"] == 2
    # onion: 3 x 0.67 -> 2
    assert c["ing"]["onions"]["amount"] == 2
    # tomato paste: 3 x 0.67 = 2.01, range rule -> whole 2
    assert c["ing"]["tomato_paste"]["amount"] == 2
    # oil: 3 x 0.17 = 0.51 -> quarter -> 0.5
    assert c["ing"]["vegetable_oil"]["amount"] == 0.5
    # parboiled liquid: 3 x 1.5 = 4.5
    assert c["ing"]["stock"]["amount"] == 4.5
    # seasoning cubes: 3 x 0.67 = 2.01 -> half -> 2
    assert c["ing"]["seasoning_cubes"]["amount"] == 2
    # protein default chicken: 3 x 167 = 501 -> grams -> 500
    assert c["ing"]["protein"]["amount"] == 500
    # rice itself is first in the ingredient list
    assert plan["ingredients"][0]["key"] == "rice"
    # pre-formatted amount strings, no decimals
    tom = _ingredient(plan, "tomatoes")
    assert tom["amount"] == "4" and tom["unit"] == "medium"


def test_fried_rice_rice_relative_amounts():
    plan = build_plan("fried_rice", {"rice_cups": 2})
    c = plan["calc"]
    # Current knowledge base: 2 x 0.10 = 0.20 stick -> nearest quarter, 0.25.
    assert c["ing"]["carrots"]["raw_amount"] == 0.2
    assert c["ing"]["carrots"]["amount"] == 0.25
    assert c["ing"]["carrots"]["unit"] == "stick"
    # oil (tbsp, range): 2 x 0.75 = 1.5 -> (1, 2) displayed "1-2 tbsp"
    assert c["ing"]["vegetable_oil"]["amount"] == (1, 2)
    oil = _ingredient(plan, "vegetable_oil")
    assert oil["amount"] == "1-2" and oil["unit"] == "tbsp"
    # stock: 2 x 1.5 = 3
    assert c["ing"]["stock"]["amount"] == 3
    # cooked rice: 2 x 3.0 expansion, half rule -> 6
    assert c["cooked_cups"] == 6
    # default frying capacity 6 -> exactly 1 batch
    assert c["frying_batches"] == 1
    # protein (chicken): 2 x 150 = 300 g
    assert c["ing"]["protein"]["amount"] == 300


def test_spice_level_changes_only_scotch_bonnet():
    mild = build_plan("jollof", {"rice_cups": 3, "spice": "mild"})
    hot = build_plan("jollof", {"rice_cups": 3, "spice": "hot"})
    assert mild["calc"]["ing"]["scotch_bonnet"]["amount"] == 1   # 3x0.33
    assert hot["calc"]["ing"]["scotch_bonnet"]["amount"] == 4    # 3x1.33
    # everything else identical
    assert mild["calc"]["ing"] and hot["calc"]["ing"]
    for key in ("tomatoes", "onions", "vegetable_oil", "stock"):
        assert (mild["calc"]["ing"][key]["amount"]
                == hot["calc"]["ing"][key]["amount"]), key


def test_rice_type_changes_liquid_ratio():
    p = build_plan("jollof", {"rice_cups": 4, "rice_type": "parboiled"})
    b = build_plan("jollof", {"rice_cups": 4, "rice_type": "basmati"})
    assert p["calc"]["liquid_ratio"] == 1.5
    assert b["calc"]["liquid_ratio"] == 1.25
    assert p["calc"]["ing"]["stock"]["amount"] == 6       # 4 x 1.5
    assert b["calc"]["ing"]["stock"]["amount"] == 5       # 4 x 1.25
    # non-rice solids unaffected by rice type
    assert (p["calc"]["ing"]["tomatoes"]["amount"]
            == b["calc"]["ing"]["tomatoes"]["amount"])


def test_protein_none_zeroes_protein():
    with_protein = build_plan("fried_rice", {"rice_cups": 2, "protein": "chicken"})
    without = build_plan("fried_rice", {"rice_cups": 2, "protein": "none"})
    assert with_protein["calc"]["protein_g"] == 300
    assert without["calc"]["protein_g"] == 0


# ---------------------------------------------------------------------------
# Guide generation (experta engines)
# ---------------------------------------------------------------------------

def test_steps_are_ordered_and_complete():
    plan = build_plan("jollof", {"rice_cups": 3})
    orders = [s["order"] for s in plan["steps"]]
    assert orders == sorted(orders), orders
    assert len(orders) == len(set(orders)), "duplicate step orders"
    assert len(plan["steps"]) == 11, len(plan["steps"])

    plan2 = build_plan("fried_rice", {"rice_cups": 2})
    orders2 = [s["order"] for s in plan2["steps"]]
    assert orders2 == sorted(orders2)
    assert len(plan2["steps"]) == 14, len(plan2["steps"])


def test_protein_none_skips_protein_step():
    with_protein = build_plan("fried_rice", {"rice_cups": 2, "protein": "chicken"})
    without = build_plan("fried_rice", {"rice_cups": 2, "protein": "none"})
    assert "Protein" in _phases(with_protein)
    assert "Protein" not in _phases(without)
    assert "vegetarian" in _steps_text(without)
    assert "vegetarian" in _steps_text(
        build_plan("jollof", {"rice_cups": 3, "protein": "none"}))


def test_jollof_style_branch():
    party = build_plan("jollof", {"rice_cups": 3, "style": "party"})
    regular = build_plan("jollof", {"rice_cups": 3, "style": "regular"})
    assert "PARTY-STYLE FINISH" in _steps_text(party)
    assert "PARTY-STYLE FINISH" not in _steps_text(regular)
    # both must still have exactly one finish step
    assert _phases(party).count("Finish") == 1
    assert _phases(regular).count("Finish") == 1


def test_fried_rice_frying_batches():
    # 3 cups rice -> 9 cups cooked, capacity 4 -> 3 batches
    big = build_plan("fried_rice", {"rice_cups": 3, "frying_capacity": 4})
    assert big["calc"]["frying_batches"] == 3
    assert "batches" in _steps_text(big)
    # capacity 6 -> 2 batches
    mid = build_plan("fried_rice", {"rice_cups": 3, "frying_capacity": 6})
    assert mid["calc"]["frying_batches"] == 2


def test_jollof_pot_batches():
    # 12 cups rice, 10-cup pot -> 2 batches
    big = build_plan("jollof", {"rice_cups": 12, "pot_capacity": 10})
    assert big["calc"]["pot_batches"] == 2
    assert "batches" in _steps_text(big)
    small = build_plan("jollof", {"rice_cups": 3, "pot_capacity": 10})
    assert small["calc"]["pot_batches"] == 1
    assert "batches" not in _steps_text(small)


def test_summary_mentions_rice_as_base():
    plan = build_plan("jollof", {"rice_cups": 3})
    assert any("base" in line.lower() for line in plan["summary"])
    plan2 = build_plan("fried_rice", {"rice_cups": 2})
    assert any("base" in line.lower() for line in plan2["summary"])


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------

def test_validation_errors():
    _expect_value_error(lambda: build_plan("jollof", {"rice_cups": 0}))
    _expect_value_error(lambda: build_plan("jollof", {"rice_cups": -3}))
    _expect_value_error(lambda: build_plan("jollof", {"rice_cups": "abc"}))
    _expect_value_error(lambda: build_plan("egusi", {"rice_cups": 3}))
    _expect_value_error(lambda: build_plan(
        "jollof", {"rice_cups": 3, "spice": "nuclear"}))
    _expect_value_error(lambda: build_plan(
        "jollof", {"rice_cups": 3, "rice_type": "wild"}))


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("  ok  %s" % t.__name__)
    print("\nAll %d checks passed." % len(tests))


if __name__ == "__main__":
    main()
