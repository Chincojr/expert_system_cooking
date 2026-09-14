# ExpertCook — a Cooking Expert System (experta)

An [experta](https://github.com/nilp0inter/experta) rule-based expert system that a
user can **query** to cook one of two Nigerian rice dishes and get a
**rice-relative, step-by-step cooking guide** in return.

* **Jollof Rice**
* **Fried Rice**

The recipes are **individual**: they do not share parameters or ingredients.
**Rice is the base ingredient** — you state how many cups of rice you are cooking
and every other quantity is derived from it via its own independent
proportionality rule.

It ships with three interfaces:

* a **command-line interface** — [cli.py](cli.py)
* a **Tkinter GUI** — [ui.py](ui.py)
* a **web frontend** served by [server.py](server.py) (Flask)

The recipe knowledge is derived from the specs in
[reciepies/jollof_rice.md](reciepies/jollof_rice.md) and
[reciepies/fried_rice.md](reciepies/fried_rice.md).

---

## Requirements

Everything needed is already installed in the bundled `venv`:

* Python 3.8+
* `experta` 1.9.4 (+ `frozendict` 2.4.7 — 1.2 breaks on Python 3.10+)
* `flask` 3.x
* `tkinter` (bundled with Python — used by the desktop GUI)

All commands below use the venv's interpreter.

---

## Run it

### 1) Web frontend

```bash
venv/Scripts/python.exe server.py
```

Open <http://127.0.0.1:5000>. The page has two tabs:

* **Cook** — pick a dish, set the rice-driven parameters, get the guide.
* **Proportionality rules** — edit `proportions.json` live in the browser and save
  it (validated; a bad edit is rejected and leaves the file intact).

The server binds to `0.0.0.0` (LAN-visible). For real hosting point any WSGI
server at `server:app`, e.g. `waitress-serve --port=8000 server:app`.

### 2) Command-line interface

```bash
venv/Scripts/python.exe cli.py
```

You'll be asked which dish to cook and a few parameters (press Enter to accept the
default shown in brackets), then the guide is printed.

### 3) Graphical interface (Tkinter)

```bash
venv/Scripts/python.exe ui.py
```

Pick a dish from the dropdown, set the parameters, and click **Generate Guide**.
The parameter fields change automatically depending on the dish.

### 4) Self-tests

```bash
venv/Scripts/python.exe selftest.py          # core checks (no server needed)
venv/Scripts/python.exe smoke_web.py         # web endpoints (server must be running)
```

Plain-assert checks (no pytest needed) covering the rounding rules,
proportions.json, rice-relative maths, step ordering and the branching rules.

---

## Parameters

**Jollof Rice**

| Parameter | Meaning |
|-----------|---------|
| rice_cups | Cups of rice — the base everything is derived from |
| rice_type | `parboiled` / `basmati` / `other` (sets the liquid ratio) |
| style | `party` (smoky finish) or `regular` |
| spice | `mild` / `medium` / `hot` (sets the scotch bonnet amount) |
| protein | `chicken` / `beef` / `goat` / `none` |
| pot_capacity | Cups of raw rice your largest pot cooks well at once (triggers batching) |

**Fried Rice**

| Parameter | Meaning |
|-----------|---------|
| rice_cups | Cups of rice — the base everything is derived from |
| rice_type | `parboiled` / `basmati` / `other` (sets the liquid ratio) |
| spice | `mild` / `medium` / `hot` (sets the scotch bonnet amount) |
| protein | `chicken` / `liver` / `chicken+liver` / `none` |
| frying_capacity | Cups of cooked rice your pan fries well per batch (triggers batching) |

---

## Proportionality rules (proportions.json)

[proportions.json](proportions.json) is a plain, dict-like JSON file — the single
editable source of truth for quantities. Insert / modify / delete entries the same
way you would edit any JSON object; the system picks up changes on the next
request (no restart needed).

```json
"tomatoes": {"label": "Tomatoes", "per_rice": 1.33,
             "unit": "medium", "rounding": "count"}
```

Per entry:

| Field | Meaning |
|-------|---------|
| `per_rice` | Amount per 1 cup of rice (simple linear rule) |
| `per_rice_by_spice` | Spice-driven rules (`"special": "spice"`) |
| `special` | `liquid` / `protein` / `seasoning` / `to_taste` |
| `unit` | Display unit |
| `rounding` | `count` / `half` / `quarter` / `range` / `grams` |
| `note` | Free-text caveat shown in the UI |

Rounding rules (decimal quantities are never shown — per the recipe specs):

* `count` — whole items, minimum 1
* `half` — nearest ½, minimum ½
* `quarter` — nearest ¼, minimum ¼
* `range` — fractional values become ranges: 2.65 tbsp → "2-3 tbsp",
  2.25 tbsp → "2 tbsp", 2.75 tbsp → "3 tbsp"
* `grams` — nearest 50 g, minimum 50

Each dish also defines its own `rice_types` (`liquid_ratio`, `expansion`) and
`liquid_reserve_per_rice`. **The current values are mocks** — tune them to taste.

---

## How it works

```
proportions.json        rice-relative proportionality rules (editable)
expertcook/
  proportions.py        loads/validates proportions.json (re-read every call)
  recipes.py            recipe metadata + PARAM_SPECS (one source of truth)
  scaling.py            pure maths: rounding rules, rice-relative quantities, batches
  facts.py              experta Facts: Param, Flag, Step
  engines.py            the expert system: JollofRiceEngine & FriedRiceEngine
  planner.py            build_plan(dish, params) -> ordered, rice-relative guide
cli.py                  text interface
ui.py                   Tkinter interface
server.py               Flask server + JSON API
static/index.html       web frontend
smoke_web.py            web endpoint checks
selftest.py             core assertion checks
```

`build_plan(dish, params)` is the single entry point used by every interface:

1. **Validate** the parameters against `PARAM_SPECS` (defaults, ranges, choices)
   and the proportionality rules in `proportions.json`.
2. **Derive** every ingredient from the rice: `rice_cups × per_rice`, each with
   its own rounding rule. Special rules handle spice levels, the cooking liquid
   (rice × the rice type's liquid ratio), protein grams and to-taste items.
3. **Run the experta engine** — the rules decide *which* steps apply, *branch* on the
   query (protein present/absent, party vs regular finish, whether the batch must be
   split), and emit a `Step` fact for each instruction.
4. **Sort** the `Step` facts by their `order` field, so the guide is always in the
   correct sequence regardless of the order experta happened to fire the rules in.

### API (server.py)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | the web frontend |
| GET | `/api/dishes` | dish metadata + parameter specs (drives the form) |
| POST | `/api/plan` | `{"dish": ..., "params": {...}}` → cooking guide |
| GET | `/api/proportions` | the current proportionality rules |
| PUT | `/api/proportions` | replace the rules (validated, then written to disk) |

### Design notes / known experta gotchas handled here

* **Step ordering.** experta's agenda does not fire rules in recipe order, so each
  step carries an explicit `order` and the guide is sorted before display.
* **frozendict version.** experta pins `frozendict==1.2`, which uses
  `collections.Mapping` (removed in Python 3.10); 2.4.7 is required instead.
* **Windows console encoding.** `cli.py` reconfigures stdout to UTF-8 and the guide
  text is ASCII-only, so it never hits the `UnicodeEncodeError` the original
  [run.py](run.py) prototype produced on a cp1252 console.

> [run.py](run.py) is the original single-dish prototype and is left unchanged for
> reference.
