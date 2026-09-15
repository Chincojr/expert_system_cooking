"""Reproduce functional results and export chapter evidence, without live edits.

Run: python verify.py --output docs/evidence
"""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import itertools
import json
from pathlib import Path
import platform
import subprocess
import time
import unittest

from expertcook import build_plan, proportions
from expertcook.audit import implementation_hash
from expertcook.recipes import PARAM_SPECS
import selftest
import test_regressions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/evidence")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    suite = unittest.TestSuite()
    for name, fn in sorted(vars(selftest).items()):
        if name.startswith("test_"):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_regressions))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    knowledge, config_hash = proportions.snapshot()
    cases = 0
    failures = []
    firings = 0
    for dish in ("jollof", "fried_rice"):
        specs = PARAM_SPECS[dish]
        dimensions = [(s["name"], s["choices"]) for s in specs if s["type"] == "choice"]
        capacity = "pot_capacity" if dish == "jollof" else "frying_capacity"
        dimensions += [("rice_cups", [0.5, 2.01, 12]), (capacity, [1, 6])]
        for combination in itertools.product(*(values for _, values in dimensions)):
            params = dict(zip((key for key, _ in dimensions), combination))
            cases += 1
            try:
                plan = build_plan(dish, params, knowledge=knowledge)
                expected = (11 if dish == "jollof" else 14) - (params["protein"] == "none")
                assert len(plan["steps"]) == expected
                assert len(plan["audit"]["firings"]) == expected
                assert len({s["order"] for s in plan["steps"]}) == expected
                assert all(c["satisfied"] for f in plan["audit"]["firings"] for c in f["conditions"])
                assert all(f["outputs"] for f in plan["audit"]["firings"])
                assert plan["audit"]["config_hash"] == config_hash
                firings += expected
            except Exception as exc:
                failures.append({"dish": dish, "params": params, "error": repr(exc)})
    samples = {
        "jollof_party": ("jollof", {"rice_cups": 3, "style": "party"}),
        "jollof_vegetarian": ("jollof", {"rice_cups": 12, "protein": "none", "style": "regular"}),
        "fried_rice_boundary": ("fried_rice", {"rice_cups": 2.01, "frying_capacity": 6}),
    }
    for name, (dish, params) in samples.items():
        plan = build_plan(dish, params, knowledge=knowledge)
        (output / (name + ".json")).write_text(json.dumps(plan, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "implementation_hash": implementation_hash(), "config_hash": config_hash,
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        **{name: version(name) for name in ("experta", "frozendict", "Flask", "gunicorn")}},
        "tests": {"run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                  "details": [(str(test), trace) for test, trace in result.failures + result.errors]},
        "matrix": {"cases": cases, "passed": cases - len(failures), "failures": failures,
                   "verified_firings": firings, "rice_cups": [0.5, 2.01, 12], "capacities": [1, 6]},
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "scope": "Local software verification, not sensory quality, usability, load testing or hosted uptime.",
    }
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not result.wasSuccessful() or failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
