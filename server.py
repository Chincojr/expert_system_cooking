"""A small Flask web server for the ExpertCook expert system.

Run it with:

    venv/Scripts/python.exe server.py

Then open http://127.0.0.1:5000 in your browser.

Endpoints
---------
GET  /                     the web frontend (static/index.html)
GET  /api/dishes           dish metadata + parameter specs (drives the form)
POST /api/plan             {"dish": ..., "params": {...}} -> cooking guide
GET  /api/proportions      the current rice-relative proportionality rules
PUT  /api/proportions      replace the rules (validated, then written to disk)
                           so proportions.json can be edited from the web too

To host it on the web, point any WSGI server at ``app`` (e.g.
``waitress-serve --port=8000 server:app``) or simply run this file.
"""

import os
import hmac

from flask import Flask, jsonify, request, send_from_directory

from expertcook.recipes import DISHES, PARAM_SPECS, get_recipe
from expertcook.planner import build_plan
from expertcook import proportions

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
proportions.initialize_storage()

ROOT = os.path.dirname(os.path.abspath(__file__))


@app.route("/healthz")
def health():
    try:
        _, version = proportions.snapshot()
        return jsonify({"status": "ok", "config_hash": version})
    except proportions.ProportionsError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 503


@app.route("/")
def index():
    return send_from_directory(os.path.join(ROOT, "static"), "index.html")


@app.route("/api/dishes")
def api_dishes():
    """Everything the frontend needs to build its forms."""
    dishes = []
    for key in DISHES:
        recipe = get_recipe(key)
        dishes.append({
            "key": key,
            "name": recipe["name"],
            "description": recipe.get("description", ""),
            "params": PARAM_SPECS.get(key, []),
        })
    return jsonify({"dishes": dishes})


@app.route("/api/plan", methods=["POST"])
def api_plan():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400
    dish = payload.get("dish")
    params = payload.get("params", {})
    try:
        plan = build_plan(dish, params)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    # ``calc`` contains tuples/non-JSON values; strip it for the frontend.
    plan.pop("calc", None)
    return jsonify(plan)


@app.route("/api/proportions")
def api_get_proportions():
    try:
        data, _ = proportions.snapshot()
    except proportions.ProportionsError as exc:
        return jsonify({"error": "Could not read proportions.json: %s" % exc}), 500
    return jsonify(data)


@app.route("/api/proportions", methods=["PUT"])
def api_put_proportions():
    """Save edited proportionality rules (validated per dish before writing)."""
    token = os.environ.get("RULES_ADMIN_TOKEN")
    if token:
        supplied = request.headers.get("Authorization", "")
        if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
            return jsonify({"error": "An administrator token is required to edit rules"}), 401
    elif os.environ.get("ALLOW_RULE_EDITS") != "1":
        return jsonify({"error": "Rule editing is disabled. Configure an administrator token."}), 403
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400

    try:
        version = proportions.save(data)
    except (proportions.ProportionsError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    except OSError as exc:
        return jsonify({"error": "Could not save file: %s" % exc}), 500
    return jsonify({"ok": True, "config_hash": version})


if __name__ == "__main__":
    # Host on all interfaces so it is reachable when hosted on the web.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("DEBUG") == "1")
