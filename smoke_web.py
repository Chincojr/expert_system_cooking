"""Read-only HTTP checks for local or deployed ExpertCook services.

Usage: python smoke_web.py [https://your-service.up.railway.app]
Rule-save behavior is tested against isolated temporary files in test_regressions.py.
"""
import json
import sys
import urllib.error
import urllib.request


def main(base="http://127.0.0.1:5000"):
    def request(path, payload=None):
        body = None if payload is None else json.dumps(payload).encode()
        req = urllib.request.Request(base.rstrip("/") + path, data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    assert request("/healthz")["status"] == "ok"
    assert len(request("/api/dishes")["dishes"]) == 2
    for dish, steps in (("jollof", 11), ("fried_rice", 14)):
        plan = request("/api/plan", {"dish": dish, "params": {"rice_cups": 3}})
        assert len(plan["steps"]) == steps
        assert len(plan["audit"]["firings"]) == steps
        assert plan["ingredients"][0]["key"] == "rice"
        print("%s: %d steps, %d audited rule firings" % (dish, steps, steps))
    assert set(request("/api/proportions")) >= {"jollof", "fried_rice"}
    try:
        request("/api/plan", {"dish": "egusi"})
    except urllib.error.HTTPError as exc:
        assert exc.code == 400
    else:
        raise AssertionError("Unknown dish was accepted")
    print("HTTP smoke checks passed; no configuration was changed.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000")
