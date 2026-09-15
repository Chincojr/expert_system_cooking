# ExpertCook

ExpertCook is an Experta rule-based system that generates cooking guides for Nigerian jollof rice and fried rice. Rice is the base quantity; each dish has independent ingredient ratios and procedural rules.

The guide now explains each ingredient calculation and records which rules fired, when they fired, the facts and branch conditions involved, and the cooking steps they produced. Downloadable JSON includes the configuration snapshot needed to reproduce a guide.

## Run the web application

With Docker running:

```bash
docker compose up --build -d
```

Open <http://localhost:8000>. Edited rules are retained in a named volume. Rule viewing and guide generation are public; saving rules requires `RULES_ADMIN_TOKEN`. Set that secret in a local `.env` file, restart with `docker compose up -d`, and enter it in the editor's administrator field. `.env` is ignored by Git.

For a native Python installation, Python 3.12 is the deployment target:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/gunicorn --config gunicorn.conf.py server:app
```

For development, `.venv/bin/python server.py` starts Flask on port 5000. The CLI is `.venv/bin/python cli.py`; the desktop interface is `.venv/bin/python ui.py` and requires Tk support. On Windows, use the equivalent interpreter under `.venv\Scripts` for those interfaces; use Docker for the Gunicorn deployment.

## Documentation

- [Change document](docs/CHANGES.md): behavior, implementation decisions, API additions and limitations.
- [Hosting and deployment](docs/DEPLOYMENT.md): Railway recommendation, Docker, persistent storage, secrets and verification.
- [Implementation and results chapter](docs/IMPLEMENTATION_AND_RESULTS.md): academic draft based on the recorded test evidence.
- [Verification report](docs/evidence/verification.json): machine-readable test counts, parameter matrix and version identifiers.

## Parameters

| Input | Jollof | Fried rice |
|---|---|---|
| `rice_cups` | Raw rice quantity, minimum 0.5 cup | Raw rice quantity, minimum 0.5 cup |
| `rice_type` | parboiled, basmati, other | parboiled, basmati, other |
| `spice` | mild, medium, hot | mild, medium, hot |
| `protein` | chicken, beef, goat, none | chicken, liver, chicken+liver, none |
| `style` | party, regular | Not used |
| `pot_capacity` | Raw rice cups per pot | Not used |
| `frying_capacity` | Not used | Cooked rice cups per pan batch |

Defaults and input specifications live in `expertcook/recipes.py` and are shared by the interfaces.

## Proportionality rules

`proportions.json` contains each dish's rice types, ingredient ratios and liquid reserve. For example:

```json
"tomatoes": {"label": "Tomatoes", "per_rice": 1.33,
             "unit": "medium", "rounding": "count"}
```

The unrounded quantity is rice cups multiplied by the selected ratio. Display rounding is independent:

| Mode | Positive quantity display |
|---|---|
| `count` | Whole items, minimum 1 |
| `half` | Nearest half, minimum one half |
| `quarter` | Nearest quarter, minimum one quarter |
| `range` | Whole value or adjacent whole-number range |
| `grams` | Nearest 50 grams, minimum 50 grams |

All modes preserve zero. Nearest-increment ties retain Python's ties-to-even behavior. Raw quantities are available in the audit; practical displayed quantities may not remain strictly proportional, especially for small portions.

Special modes support spice-dependent ratios, rice-type liquid ratios, selected protein, seasoning and to-taste ingredients. Salt remains to taste. Existing ratios are mock culinary values and have not been validated by a cooking trial.

The editor validates changes before publishing them atomically. Ingredients referenced by cooking rules cannot be deleted; optional ingredients can be changed. Use `PROPORTIONS_PATH` to select a file on persistent storage. New requests read one complete snapshot and retain it in their evidence.

## Inference and audit

`build_plan(dish, params)` validates inputs, calculates quantities, declares input-derived flags, runs the appropriate Experta engine and sorts emitted `Step` facts by cooking order. Rule bodies use `NOT(Step(order=...))` guards to prevent duplicate steps.

Each real rule invocation records its ID, UTC time, execution sequence, satisfied fact conditions and emitted steps. Branches within rule bodies record the boolean result actually used. Non-fired rules have end-of-run condition explanations. Cooking order is independent of firing order.

The web interface exposes “How much and why?” and “Why this step?” details and a JSON download. The same structured evidence is returned by the Python API; the CLI and Tkinter interfaces retain their text-guide presentation.

Cooking observations such as tenderness and moisture are not collected. Conditional instructions about those observations are advice for the user, not claims that the system observed a cooking event.

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Browser interface |
| GET | `/healthz` | Knowledge-base readiness and configuration hash |
| GET | `/api/dishes` | Dish metadata and input specifications |
| POST | `/api/plan` | `{"dish":"jollof","params":{"rice_cups":3}}` returns a guide and audit |
| GET | `/api/proportions` | Read the active knowledge base |
| PUT | `/api/proportions` | Replace validated knowledge using `Authorization: Bearer TOKEN` |

When no administrator token is set, saving rules is disabled. `ALLOW_RULE_EDITS=1` is an explicit local-only override; do not use it on a public deployment.

## Verification and replay

```bash
.venv/bin/python selftest.py
.venv/bin/python test_regressions.py
.venv/bin/python verify.py --output docs/evidence
.venv/bin/python replay.py docs/evidence/fried_rice_boundary.json
.venv/bin/python smoke_web.py http://localhost:8000
node --test test_audit_view.cjs
```

The verification runner combines 17 existing core checks with 19 regression/integration tests and a 648-case parameter matrix. It writes three representative plan exports and a result report. Configuration mutation tests use temporary files; the HTTP smoke test never saves rules. Re-running the verification command intentionally refreshes the evidence files, so preserve a copy for each academic evaluation run.

## Project layout

```text
expertcook/
  recipes.py       dish metadata and input specifications
  proportions.py   validated snapshots and atomic saves
  scaling.py       raw arithmetic, rounding and capacity calculations
  facts.py         Param, Flag and Step definitions
  engines.py       procedural rules for both dishes
  audit.py         execution evidence and implementation identity
  planner.py       shared guide generation entry point
server.py          Flask API
static/index.html  browser interface and audit download
docs/              changes, deployment, chapter and test evidence
```

Experta 1.9.4 requires frozendict 1.2. `expertcook/__init__.py` restores its legacy `collections.Mapping` alias before import, allowing the declared dependency versions to install consistently on modern Python. Engine runs are serialized within each process because Experta's rule descriptors retain their bound engine. Deployment uses one synchronous Gunicorn worker and one service replica. `run.py` remains the original prototype and is not the supported deployment entry point.
