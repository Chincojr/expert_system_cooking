"""Execution evidence for the literal Flag and NOT(Step) rules used here.

The wrapper runs only when Experta invokes the rule, before its effects occur.
It does not infer firing order from the sorted cooking instructions.
"""

from datetime import datetime, timezone
from functools import wraps
from hashlib import sha256
from pathlib import Path
from threading import RLock
from importlib.metadata import version
import platform

from experta import KnowledgeEngine, Rule, NOT
from .facts import Flag, Step

# Experta 1.9.4 Rule descriptors bind their engine instance on shared class
# objects. Serialize engine construction/execution within a process.
ENGINE_LOCK = RLock()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def implementation_hash():
    digest = sha256()
    for name in ("__init__.py", "audit.py", "engines.py", "facts.py", "planner.py", "proportions.py", "recipes.py", "scaling.py"):
        digest.update(name.encode())
        digest.update(Path(__file__).with_name(name).read_bytes())
    return digest.hexdigest()


def runtime_versions():
    return {"python": platform.python_version(),
            **{name: version(name) for name in ("experta", "frozendict", "schema")}}


def conditions_at(conditions, facts):
    evidence = []
    for condition in conditions:
        absent = isinstance(condition, NOT)
        pattern = condition[0] if absent else condition
        if not isinstance(pattern, (Flag, Step)):
            raise TypeError("Audit supports literal Flag and NOT(Step) conditions only")
        fields = {k: v for k, v in pattern.items() if not k.startswith("__")}
        matching = [f for f in facts if isinstance(f, type(pattern))
                    and all(f.get(k) == v for k, v in fields.items())]
        evidence.append({
            "kind": "absent" if absent else "present", "fact_type": type(pattern).__name__,
            "fields": fields, "satisfied": not matching if absent else bool(matching),
            "fact_ids": [f.__factid__ for f in matching],
        })
    return evidence


def AuditedRule(*conditions):
    def decorate(method):
        @wraps(method)
        def execute(self):
            before = set(self.facts)
            event = {
                "sequence": len(self.trace) + 1,
                "rule_id": type(self).__name__ + "." + method.__name__,
                "fired_at": utc_now(),
                "conditions": conditions_at(conditions, self.facts.values()),
                "decisions": [], "outputs": [],
            }
            self.trace.append(event)
            self._event = event
            try:
                method(self)
                event["outputs"] = [
                    {"fact_id": fid, "order": f["order"], "phase": f["phase"]}
                    for fid, f in self.facts.items() if fid not in before and isinstance(f, Step)]
            finally:
                self._event = None
        rule = Rule(*conditions)(execute)
        rule.audit_conditions = conditions
        return rule
    return decorate


class AuditedEngine(KnowledgeEngine):
    def __init__(self):
        self.trace = []
        self._event = None
        super().__init__()

    def decide(self, expression, result, **inputs):
        """Record the same boolean that controls a branch in a rule body."""
        self._event["decisions"].append({
            "expression": expression, "inputs": inputs, "result": bool(result)})
        return result

    def skipped_rules(self):
        fired = {e["rule_id"] for e in self.trace}
        skipped = []
        for name, rule in sorted(type(self).__dict__.items()):
            if not isinstance(rule, Rule):
                continue
            rule_id = type(self).__name__ + "." + name
            if rule_id not in fired:
                skipped.append({"rule_id": rule_id,
                                "evaluated_at": "end_of_run",
                                "conditions": conditions_at(rule.audit_conditions, self.facts.values())})
        return skipped
