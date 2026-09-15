"""Regression and integration tests; all configuration writes use temp files."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from expertcook import build_plan, proportions, scaling
from server import app


class ProportionalityTests(unittest.TestCase):
    def setUp(self):
        self.knowledge, _ = proportions.snapshot()

    def test_zero_is_preserved_by_every_rounder(self):
        for rounding in proportions.ROUNDINGS:
            with self.subTest(rounding=rounding):
                self.assertEqual(scaling.apply_rounding(0, rounding), 0)
                self.assertEqual(scaling._ROUNDERS[rounding](0), 0)
        self.knowledge["jollof"]["ingredients"]["tomatoes"]["per_rice"] = 0
        plan = build_plan("jollof", {}, knowledge=self.knowledge)
        self.assertEqual(plan["calc"]["ing"]["tomatoes"]["amount"], 0)

    def test_raw_quantities_scale_before_display_rounding(self):
        small = build_plan("jollof", {"rice_cups": 0.5})
        big = build_plan("jollof", {"rice_cups": 1})
        for key, item in small["calc"]["ing"].items():
            if item["raw_amount"] is not None:
                self.assertAlmostEqual(big["calc"]["ing"][key]["raw_amount"], 2 * item["raw_amount"])
        # Both display one tomato, while raw amounts remain distinct.
        self.assertEqual(small["calc"]["ing"]["tomatoes"]["amount"], 1)
        self.assertEqual(big["calc"]["ing"]["tomatoes"]["amount"], 1)

    def test_frying_capacity_uses_unrounded_volume(self):
        for rice, batches in ((2, 1), (2.01, 2), (1.99, 1)):
            with self.subTest(rice=rice):
                plan = build_plan("fried_rice", {"rice_cups": rice, "frying_capacity": 6})
                self.assertEqual(plan["calc"]["frying_batches"], batches)
        self.assertEqual(plan["calc"]["cooked_cups"], 6)

    def test_decimal_capacity_boundary(self):
        self.knowledge["fried_rice"]["rice_types"]["parboiled"]["expansion"] = 1.1
        plan = build_plan("fried_rice", {"rice_cups": 3, "frying_capacity": 3.3}, knowledge=self.knowledge)
        self.assertEqual(plan["calc"]["cooked_cups_raw"], 3.3)
        self.assertEqual(plan["calc"]["frying_batches"], 1)

    def test_units_match_in_table_and_steps(self):
        self.knowledge["fried_rice"]["ingredients"]["carrots"]["unit"] = "sticks"
        plan = build_plan("fried_rice", {}, knowledge=self.knowledge)
        prepare = next(s["text"] for s in plan["steps"] if s["phase"] == "Prepare")
        self.assertIn("carrots (1/4 stick)", prepare)
        self.assertNotIn("carrots (1/4 cup)", prepare)

    def test_bad_numeric_inputs(self):
        for value in (float("nan"), float("inf"), True, 10 ** 1000, -1):
            with self.subTest(value=str(value)[:20]), self.assertRaises(ValueError):
                build_plan("jollof", {"rice_cups": value})

    def test_configuration_validation(self):
        mutations = [
            lambda k: k.pop("fried_rice"),
            lambda k: k["jollof"]["ingredients"].pop("stock"),
            lambda k: k["jollof"]["ingredients"].update(rice={}),
            lambda k: k["jollof"]["ingredients"].update(tomatoes=[]),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(per_rice=-1),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(per_rice=True),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(per_rice=float("inf")),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(per_rice=10 ** 1000),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(rounding="unknown"),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(rounding=[]),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(special=[]),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(special="to_taste"),
            lambda k: k["jollof"]["ingredients"]["tomatoes"].update(unit=42),
            lambda k: k["jollof"]["ingredients"]["stock"].update(unit="litres"),
            lambda k: k["jollof"]["ingredients"]["stock"].update(rounding="range"),
            lambda k: k["jollof"]["ingredients"]["protein"].update(special="liquid"),
            lambda k: k["jollof"]["ingredients"]["scotch_bonnet"]["per_rice_by_spice"].pop("mild"),
            lambda k: k["jollof"]["rice_types"]["basmati"].update(expansion=0),
        ]
        for i, mutate in enumerate(mutations):
            candidate = deepcopy(self.knowledge)
            mutate(candidate)
            with self.subTest(case=i), self.assertRaises(ValueError):
                proportions.validate_data(candidate)


class AuditTests(unittest.TestCase):
    def test_firings_link_to_steps_and_satisfied_conditions(self):
        for dish in ("jollof", "fried_rice"):
            plan = build_plan(dish, {})
            events = plan["audit"]["firings"]
            self.assertEqual([e["sequence"] for e in events], list(range(1, len(events) + 1)))
            self.assertEqual(len(events), len(plan["steps"]))
            for step in plan["steps"]:
                event = events[step["firing_sequence"] - 1]
                self.assertEqual(step["rule_id"], event["rule_id"])
                self.assertIn(step["order"], [o["order"] for o in event["outputs"]])
                self.assertTrue(all(c["satisfied"] for c in event["conditions"]))
                self.assertTrue(event["fired_at"].endswith("+00:00"))
            self.assertNotEqual([e["outputs"][0]["order"] for e in events], sorted(s["order"] for s in plan["steps"]))

    def test_branch_evidence_and_alternatives(self):
        plan = build_plan("jollof", {"protein": "none", "style": "regular", "rice_cups": 12})
        skipped = {e["rule_id"].split(".")[-1]: e for e in plan["audit"]["not_fired"]}
        self.assertEqual(set(skipped), {"cook_protein", "finish_party"})
        for event in skipped.values():
            self.assertTrue(any(c["kind"] == "present" and not c["satisfied"] for c in event["conditions"]))
        add = next(e for e in plan["audit"]["firings"] if e["rule_id"].endswith(".add_rice"))
        self.assertEqual(add["decisions"][0]["inputs"]["pot_batches"], 2)
        self.assertTrue(add["decisions"][0]["result"])

    def test_optional_ingredient_decision(self):
        knowledge, _ = proportions.snapshot()
        knowledge["fried_rice"]["ingredients"].pop("spring_onions")
        plan = build_plan("fried_rice", {}, knowledge=knowledge)
        event = next(e for e in plan["audit"]["firings"] if e["rule_id"].endswith(".finish"))
        self.assertFalse(event["decisions"][0]["result"])

    def test_one_snapshot_and_archived_replay(self):
        knowledge, _ = proportions.snapshot()
        with patch.object(proportions, "_load_raw", return_value=knowledge) as read:
            original = build_plan("fried_rice", {"rice_cups": 2.01})
        self.assertEqual(read.call_count, 1)
        archive = json.loads(json.dumps(original))
        changed = deepcopy(knowledge)
        changed["fried_rice"]["ingredients"]["carrots"]["per_rice"] = 4
        with patch.object(proportions, "_load_raw", return_value=changed):
            replay = build_plan(archive["dish_key"], archive["params"], knowledge=archive["audit"]["knowledge_snapshot"])
        self.assertEqual(original["ingredients"], replay["ingredients"])
        self.assertEqual(original["steps"], replay["steps"])
        self.assertEqual(original["audit"]["config_hash"], replay["audit"]["config_hash"])
        self.assertNotEqual(original["audit"]["run_id"], replay["audit"]["run_id"])

    def test_concurrent_engines_do_not_mix_requests(self):
        params = [{"rice_cups": i + 1, "protein": "none" if i % 2 else "chicken"} for i in range(16)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            plans = list(pool.map(lambda p: build_plan("jollof", p), params))
        for p, plan in zip(params, plans):
            self.assertEqual(plan["params"]["rice_cups"], p["rice_cups"])
            self.assertEqual(len(plan["steps"]), 10 if p["protein"] == "none" else 11)
            self.assertEqual(len(plan["audit"]["firings"]), len(plan["steps"]))


class WebTests(unittest.TestCase):
    def setUp(self):
        self.knowledge, _ = proportions.snapshot()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "proportions.json"
        self.patch = patch.object(proportions, "_PROPORTIONS_PATH", str(self.path))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        proportions.save(self.knowledge)
        self.env = patch.dict(os.environ, {"RULES_ADMIN_TOKEN": "test-only-token", "ALLOW_RULE_EDITS": "0"})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.client = app.test_client()
        self.headers = {"Authorization": "Bearer test-only-token"}

    def test_health_and_plan_export(self):
        self.assertEqual(self.client.get("/healthz").status_code, 200)
        result = self.client.post("/api/plan", json={"dish": "jollof", "params": {}})
        self.assertEqual(result.status_code, 200)
        self.assertIn("knowledge_snapshot", result.json["audit"])
        self.assertNotIn("calc", result.json)

    def test_invalid_payloads_return_400(self):
        for payload in ([], None, {}, {"dish": []}, {"dish": "jollof", "params": []},
                        {"dish": "jollof", "params": {"rice_cups": "NaN"}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/plan", json=payload).status_code, 400)

    def test_save_authorization(self):
        before = self.path.read_bytes()
        self.assertEqual(self.client.put("/api/proportions", json=self.knowledge).status_code, 401)
        with patch.dict(os.environ, {"RULES_ADMIN_TOKEN": ""}):
            self.assertEqual(self.client.put("/api/proportions", json=self.knowledge).status_code, 403)
        self.assertEqual(before, self.path.read_bytes())

    def test_valid_save_and_invalid_candidate_preserves_file(self):
        changed = deepcopy(self.knowledge)
        changed["jollof"]["ingredients"]["tomatoes"]["per_rice"] = 2
        saved = self.client.put("/api/proportions", json=changed, headers=self.headers)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.json["config_hash"], proportions.fingerprint(changed))
        before = self.path.read_bytes()
        changed["jollof"]["ingredients"].pop("stock")
        self.assertEqual(self.client.put("/api/proportions", json=changed, headers=self.headers).status_code, 400)
        self.assertEqual(before, self.path.read_bytes())

    def test_atomic_replace_failure_preserves_previous_file(self):
        before = self.path.read_bytes()
        with patch.object(proportions.os, "replace", side_effect=OSError("simulated disk failure")):
            self.assertEqual(self.client.put("/api/proportions", json=self.knowledge, headers=self.headers).status_code, 500)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_storage_is_seeded_once(self):
        new_path = self.path.parent / "volume" / "proportions.json"
        with patch.object(proportions, "_PROPORTIONS_PATH", str(new_path)):
            proportions.initialize_storage()
            changed = deepcopy(self.knowledge)
            changed["jollof"]["ingredients"]["tomatoes"]["per_rice"] = 2
            proportions.save(changed)
            proportions.initialize_storage()
            self.assertEqual(proportions.snapshot()[0], changed)

    def test_simultaneous_reads_and_saves_remain_consistent(self):
        changed = deepcopy(self.knowledge)
        changed["jollof"]["ingredients"]["tomatoes"]["per_rice"] = 2
        expected = {proportions.fingerprint(k) for k in (self.knowledge, changed)}
        def operation(i):
            if i % 2:
                proportions.save(changed if i % 3 else self.knowledge)
            else:
                plan = build_plan("jollof", {})
                self.assertIn(plan["audit"]["config_hash"], expected)
                self.assertEqual(plan["audit"]["config_hash"], proportions.fingerprint(plan["audit"]["knowledge_snapshot"]))
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(operation, range(30)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
