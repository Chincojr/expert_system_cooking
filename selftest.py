"""Plain-assert checks for the ExpertCook engine (no pytest needed).

Run with:  venv/Scripts/python.exe selftest.py
"""

from expertcook import scaling
from expertcook.planner import build_plan


def _steps_text(plan):
    return "\n".join(s["text"] for s in plan["steps"])


def _phases(plan):
    return [s["phase"] for s in plan["steps"]]


def test_scaling_helpers():
    assert scaling.scaling_factor(10, 4) == 2.5
    assert scaling.frying_batches(12, 6) == 2
    assert scaling.frying_batches(6, 6) == 1
    assert scaling.frying_batches(13, 6) == 3
    assert scaling.pot_batches(20, 12) == 2
    assert scaling.oil_tbsp(4) == 4        # base 2 + 0.5*4
    assert scaling.oil_tbsp(8) == 6        # NOT a straight double of oil(4)
    assert scaling.fmt(3.0) == "3"
    assert scaling.fmt(7.5) == "7.5"
    assert scaling.fmt(0.25) == "0.25"


def test_jollof_matches_doc_example():
    # jollof_rice.md: 4 -> 10 servings gives factor 2.5, 7.5 cups rice,
    # 10 tomatoes, 5 bell peppers, 1.25 cups oil, 5 tbsp tomato paste.
    plan = build_plan("jollof", {"servings": 10, "style": "party",
                                 "spice": "medium", "protein": "chicken"})
    c = plan["calc"]
    assert c["factor"] == 2.5, c["factor"]
    assert c["ing"]["rice"][0] == 7.5, c["ing"]["rice"]
    assert c["ing"]["tomatoes"][0] == 10, c["ing"]["tomatoes"]
    assert c["ing"]["bell_peppers"][0] == 5, c["ing"]["bell_peppers"]
    assert c["ing"]["vegetable_oil"][0] == 1.25, c["ing"]["vegetable_oil"]
    assert c["ing"]["tomato_paste"][0] == 5, c["ing"]["tomato_paste"]


def test_steps_are_ordered_and_complete():
    plan = build_plan("jollof", {"servings": 4})
    orders = [s["order"] for s in plan["steps"]]
    assert orders == sorted(orders), orders
    assert len(orders) == len(set(orders)), "duplicate step orders"
    assert len(plan["steps"]) == 11, len(plan["steps"])

    plan2 = build_plan("fried_rice", {"servings": 4})
    orders2 = [s["order"] for s in plan2["steps"]]
    assert orders2 == sorted(orders2), orders2
    assert len(plan2["steps"]) == 11, len(plan2["steps"])


def test_protein_none_skips_protein_step():
    with_protein = build_plan("fried_rice", {"servings": 4, "protein": "chicken"})
    without = build_plan("fried_rice", {"servings": 4, "protein": "none"})
    assert "Protein" in _phases(with_protein)
    assert "Protein" not in _phases(without)
    assert "vegetarian" in _steps_text(without)


def test_jollof_style_branch():
    party = build_plan("jollof", {"servings": 4, "style": "party"})
    regular = build_plan("jollof", {"servings": 4, "style": "regular"})
    assert "PARTY-STYLE FINISH" in _steps_text(party)
    assert "PARTY-STYLE FINISH" not in _steps_text(regular)
    # both must still have exactly one finish step
    assert _phases(party).count("Finish") == 1
    assert _phases(regular).count("Finish") == 1


def test_fried_rice_batches():
    small = build_plan("fried_rice", {"servings": 4, "frying_capacity": 6})
    big = build_plan("fried_rice", {"servings": 8, "frying_capacity": 6})
    assert small["calc"]["frying_batches"] == 1
    assert big["calc"]["frying_batches"] == 2
    assert "separate batches" in _steps_text(big)
    assert "separate batches" not in _steps_text(small)


def test_validation_errors():
    for bad in [{"servings": 0}, {"servings": -3}, {"servings": "abc"}]:
        try:
            build_plan("jollof", bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for %r" % bad)
    try:
        build_plan("jollof", {"servings": 4, "spice": "nuclear"})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for bad choice")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("  ok  %s" % t.__name__)
    print("\nAll %d checks passed." % len(tests))


if __name__ == "__main__":
    main()
