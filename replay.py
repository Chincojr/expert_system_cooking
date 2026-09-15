"""Recompute an exported guide using its archived knowledge snapshot.

Usage: python replay.py docs/evidence/fried_rice_boundary.json
Execution timestamps, run IDs and agenda order are intentionally not compared.
"""
import argparse
import json
from pathlib import Path

from expertcook import build_plan, proportions
from expertcook.audit import implementation_hash


def replay(archive):
    audit = archive["audit"]
    if proportions.fingerprint(audit["knowledge_snapshot"]) != audit["config_hash"]:
        raise ValueError("The archived knowledge does not match its configuration hash")
    if implementation_hash() != audit["implementation_hash"]:
        raise ValueError("Implementation changed; use the source version associated with this archive")
    plan = build_plan(archive["dish_key"], archive["params"], knowledge=audit["knowledge_snapshot"])
    def cooking_steps(p):
        return [{k: v for k, v in step.items() if k != "firing_sequence"} for step in p["steps"]]
    if archive["ingredients"] != plan["ingredients"] or cooking_steps(archive) != cooking_steps(plan):
        raise ValueError("Replayed ingredients or cooking instructions differ from the archive")
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with args.archive.open(encoding="utf-8") as stream:
        plan = replay(json.load(stream))
    print("Replay matched: %d ingredients and %d cooking steps." % (len(plan["ingredients"]), len(plan["steps"])))
