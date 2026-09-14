"""Smoke-test the running web server (dev only; safe to delete).

Usage: venv/Scripts/python.exe smoke_web.py
Assumes the server is already running on http://127.0.0.1:5000.
"""
import json
import urllib.request

BASE = "http://127.0.0.1:5000"


def get(path):
    with urllib.request.urlopen(BASE + path) as r:
        return json.loads(r.read().decode())


def post(path, payload):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


dishes = get("/api/dishes")["dishes"]
print("dishes:", [d["key"] for d in dishes])

for dish in ("jollof", "fried_rice"):
    plan = post("/api/plan", {"dish": dish, "params": {"rice_cups": 3}})
    print("%s: %d steps, %d ingredients, first=%s %s"
          % (dish, len(plan["steps"]), len(plan["ingredients"]),
             plan["ingredients"][0]["label"],
             plan["ingredients"][0]["amount"]))

plan = post("/api/plan", {"dish": "fried_rice", "params": {"rice_cups": 2}})
oil = next(i for i in plan["ingredients"] if i["key"] == "vegetable_oil")
print("fried rice oil:", oil["amount"], oil["unit"])

props = get("/api/proportions")
print("proportionality dishes:", [k for k in props if not k.startswith("_")])

# PUT round-trip: saving the same content back must succeed and change nothing.
req = urllib.request.Request(
    BASE + "/api/proportions", data=json.dumps(props).encode(),
    headers={"Content-Type": "application/json"}, method="PUT")
with urllib.request.urlopen(req) as r:
    print("PUT same-content ->", r.status, r.read().decode())
assert get("/api/proportions") == props, "round-trip changed the file!"

# PUT with an invalid dish must be rejected (HTTP 400) and leave the file intact.
bad = dict(props)
bad["jollof"] = {"rice_types": {}, "ingredients": {}}
req = urllib.request.Request(
    BASE + "/api/proportions", data=json.dumps(bad).encode(),
    headers={"Content-Type": "application/json"}, method="PUT")
try:
    urllib.request.urlopen(req)
    raise SystemExit("ERROR: invalid proportions were accepted")
except urllib.error.HTTPError as e:
    print("PUT invalid -> HTTP", e.code, "(ok)")
assert get("/api/proportions") == props, "rejected save modified the file!"

try:
    post("/api/plan", {"dish": "egusi", "params": {}})
except urllib.error.HTTPError as e:
    print("bad dish -> HTTP %d (ok)" % e.code)

print("\nWeb smoke test passed.")
