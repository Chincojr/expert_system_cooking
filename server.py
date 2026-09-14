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

import json
import os

from flask import Flask, jsonify, request, send_from_directory

from expertcook.recipes import DISHES, PARAM_SPECS, get_recipe
from expertcook.planner import build_plan
from expertcook import proportions

app = Flask(__name__, static_folder="static", static_url_path="/static")

ROOT = os.path.dirname(os.path.abspath(__file__))


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
    payload = request.get_json(silent=True) or {}
    dish = payload.get("dish")
    params = payload.get("params") or {}
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
        with open(proportions._PROPORTIONS_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (IOError, OSError, json.JSONDecodeError) as exc:
        return jsonify({"error": "Could not read proportions.json: %s" % exc}), 500
    return jsonify(data)


@app.route("/api/proportions", methods=["PUT"])
def api_put_proportions():
    """Save edited proportionality rules (validated per dish before writing)."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Body must be a JSON object"}), 400

    # Write to a temp string first, then validate each dish using the loader.
    tmp_path = proportions._PROPORTIONS_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except (IOError, OSError, TypeError) as exc:
        return jsonify({"error": "Could not write file: %s" % exc}), 500

    # Validate by temporarily swapping the file in.
    backup = proportions._PROPORTIONS_PATH + ".bak"
    try:
        os.replace(proportions._PROPORTIONS_PATH, backup)
        os.replace(tmp_path, proportions._PROPORTIONS_PATH)
        try:
            for dish in (k for k in data if not k.startswith("_")):
                proportions.validate(dish)
        except proportions.ProportionsError as exc:
            # Roll back on any invalid rule.
            os.replace(proportions._PROPORTIONS_PATH, tmp_path)
            os.replace(backup, proportions._PROPORTIONS_PATH)
            os.remove(tmp_path)
            return jsonify({"error": str(exc)}), 400
        os.remove(backup)
    except (IOError, OSError) as exc:
        return jsonify({"error": "Could not save file: %s" % exc}), 500

    proportions._cache["data"] = None      # force a reload
    return jsonify({"ok": True})


if __name__ == "__main__":
    # Host on all interfaces so it is reachable when hosted on the web.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=bool(os.environ.get("DEBUG")))
