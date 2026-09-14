# ExpertCook — a Cooking Expert System (experta)

An [experta](https://github.com/nilp0inter/experta) rule-based expert system that a
user can **query** to cook one of two Nigerian rice dishes and get a scaled,
step-by-step **cooking guide** in return.

* **Jollof Rice**
* **Fried Rice**

You answer a few questions (servings, style, spice, protein, …); the rules calculate
the ingredient quantities, apply the recipes' special non-linear rules, and generate
an ordered guide.

It ships with two interfaces:

* a **command-line interface** — [cli.py](cli.py)
* a **simple Tkinter GUI** — [ui.py](ui.py)

The recipe knowledge is derived from the specs in
[reciepies/jollof_rice.md](reciepies/jollof_rice.md) and
[reciepies/fried_rice.md](reciepies/fried_rice.md).

---

## Requirements

Everything needed is already installed in the bundled `venv`:

* Python 3.8
* `experta` 1.9.4
* `tkinter` (bundled with Python — used by the GUI)

All commands below use the venv's interpreter.

---

## Run it

### 1) Command-line interface

```bash
venv/Scripts/python.exe cli.py
```

You'll be asked which dish to cook and a few parameters (press Enter to accept the
default shown in brackets), then the guide is printed.

### 2) Graphical interface (Tkinter)

```bash
venv/Scripts/python.exe ui.py
```

Pick a dish from the dropdown, set the parameters, and click **Generate Guide**.
The parameter fields change automatically depending on the dish.

### 3) Self-tests

```bash
venv/Scripts/python.exe selftest.py
```

Plain-assert checks (no pytest needed) covering the scaling maths, step ordering,
and the branching rules.

---

## Parameters

**Jollof Rice**

| Parameter | Meaning |
|-----------|---------|
| servings | How many people to cook for |
| style | `party` (smoky finish) or `regular` |
| spice | `mild` / `medium` / `hot` (sets the scotch bonnet amount) |
| protein | `chicken` / `beef` / `goat` / `none` |
| pot_capacity | Servings your largest pot cooks well at once (triggers batching) |

**Fried Rice**

| Parameter | Meaning |
|-----------|---------|
| servings | How many people to cook for |
| protein | `chicken` / `liver` / `chicken+liver` / `none` |
| variety | `parboiled` / `basmati` / `other` (sets the water ratio) |
| frying_capacity | Cooked rice (cups) your pan fries well per batch (triggers batching) |

---

## How it works

```
expertcook/
  recipes.py   reference quantities (4-serving base) + PARAM_SPECS (one source of truth)
  scaling.py   pure maths: scaling factor, special rules (spice, liquid, oil, batches)
  facts.py     experta Facts: Param, Flag, Step
  engines.py   the expert system: JollofRiceEngine & FriedRiceEngine (the rules)
  planner.py   build_plan(dish, params) -> ordered, scaled guide
cli.py         text interface
ui.py          Tkinter interface
selftest.py    assertion checks
```

`build_plan(dish, params)` is the single entry point used by both interfaces:

1. **Validate** the parameters against `PARAM_SPECS` (defaults, ranges, choices).
2. **Scale** ingredients from the 4-serving reference and apply special rules
   (e.g. Jollof cooking liquid = rice × ratio; Fried-rice oil = base + batch model;
   frying batches = `ceil(cooked rice / pan capacity)`).
3. **Run the experta engine** — the rules decide *which* steps apply, *branch* on the
   query (protein present/absent, party vs regular finish, whether the batch must be
   split), and emit a `Step` fact for each instruction.
4. **Sort** the `Step` facts by their `order` field, so the guide is always in the
   correct sequence regardless of the order experta happened to fire the rules in.

### Design notes / known experta gotchas handled here

* **Step ordering.** experta's agenda does not fire rules in recipe order, so each
  step carries an explicit `order` and the guide is sorted before display.
* **Windows console encoding.** `cli.py` reconfigures stdout to UTF-8 and the guide
  text is ASCII-only, so it never hits the `UnicodeEncodeError` the original
  [run.py](run.py) prototype produced on a cp1252 console.

> [run.py](run.py) is the original single-dish prototype and is left unchanged for
> reference.
