# ExpertCook changes to proportionality and rule auditability

This document describes the changes built on the `proportions` branch at base commit `a15fb1e`. The implementation preserves the current recipe ratios and adds evidence explaining both ingredient calculations and rule execution. Deployment preparation is included because editable knowledge must survive redeployment and public visitors must not be able to change it.

## Proportionality

Each ingredient retains its independent rice-relative ratio. Quantities now contain `raw_amount` as well as the existing rounded `amount`. Multiplication uses decimal input representations before conversion to a JSON number. Display rounding remains a separate operation, including the existing minimum measurement increments for positive quantities. Zero is preserved by every rounding mode; an unknown rounding mode is rejected.

For example, the current carrot rule is 0.10 stick per cup of rice. Two cups yield an unrounded 0.20 stick and a displayed quarter stick. The previous test expected half a cup from an older rule. The test now reflects the current configuration; the recipe ratio has not been changed.

Frying capacity uses the unrounded cooked-rice estimate. With 2.01 cups of raw rice and an expansion ratio of 3, the estimate is 6.03 cups. A pan capacity of 6 requires two batches. Rounding the estimate to 6 before the capacity comparison previously returned one. Pot and frying batch calculations use a decimal ceiling division to avoid introducing a batch through floating-point multiplication noise.

Ingredient units in cooking instructions now come from the same configuration entries as the ingredient table. Editing a unit changes the displayed label; it does not perform a unit conversion, so the corresponding ratio must be adjusted by the knowledge maintainer.

## Validation and consistent configuration

Every plan reads and validates one complete configuration snapshot. Calculations and exported evidence all use that snapshot. Validation checks the supported dishes, rice types, required procedural ingredients, finite non-negative ratios, positive liquid and expansion ratios, supported rounding modes, spice levels, and text fields. Liquid quantities use cups and protein quantities use grams because the procedural calculations depend on those units.

Required ingredients cannot be removed. Optional ingredients can be added or removed, but adding an ingredient only adds its quantity to the guide; new procedural behavior still requires a Python rule. A zero ratio remains a supported way to specify a zero quantity. Editing culinary relationships remains an expert task: syntactic validation does not certify taste, food safety or nutritional suitability.

Saves validate the candidate before writing a unique temporary file in the same directory. After the file is flushed, `os.replace` publishes it atomically. A failed validation or failed replacement leaves the preceding file intact. Readers see one complete version. Simultaneous valid edits use last-completed-write wins; there is no merge or optimistic concurrency check between editors.

## Execution evidence

`expertcook/audit.py` wraps each Experta rule body. An event is created only when Experta invokes that rule. It records the rule identifier, a per-run firing sequence, a UTC timestamp, the satisfied literal fact conditions and matching fact identifiers, and the Step facts created by that execution. Explicit decisions inside rule bodies record the expression, input values and boolean result used by the branch.

This separates two orders: the agenda determines execution order, while `Step.order` determines the sequence of cooking instructions. A finish rule can fire before the overview without requiring the cook to finish first. Each displayed step links back to its execution event.

Rules that did not fire have their conditions evaluated against the final fact state, explicitly labelled `end_of_run`. For instance, the party finish requires `style_party`; selecting regular style leaves that positive condition unmet. The alternative finish also shares an absent-Step guard that is false once the selected finish has emitted its step. These records are final-state explanations, not a history of every agenda activation or retraction.

The audit supports the rule language currently used here: literal `Flag` conditions and `NOT(Step(...))` guards. If new pattern types, variable bindings or more complex conditional elements are introduced, extend the evidence serializer and its tests alongside them.

Experta 1.9.4 binds rule descriptors to engine instances on shared class objects. Engine construction and execution are serialized with a process-local lock to prevent simultaneous requests from mixing their engines. The deployment uses one synchronous worker and one service replica.

## Export and reproduction

The API now returns an `audit` object containing a run ID, timestamps, configuration SHA-256, implementation SHA-256, Python and inference-library versions, initial facts and their parameter sources, the full knowledge snapshot, calculation outputs, fired-rule events and non-fired-rule explanations. Ingredients include a `derivation` object with the ratio source, formula, input rice amount, unrounded amount and display rounding mode. Steps add `rule_id` and `firing_sequence`.

The browser presents expandable quantity explanations and “Why this step?” details. Its JSON download contains the complete returned guide and audit. No administrator token is exported. Exports must be saved by the user: the server does not retain a history of every generated plan, and the files are not digitally signed or tamper-proof audit records.

The explanation views share five fields: Rule, Inputs, Explanation, Result and Execution. Cooking rules use descriptive names, fact conditions become readable requirements, and execution times use the browser's local date and time format with a time-zone label. Branch outcomes describe whether protein, batching or optional ingredients were included. Technical identifiers and raw JSON remain available inside a collapsed Technical details section. The guide-level summary and non-fired rules use the same layout. This presentation does not change the evidence or claim that ingredient arithmetic was an Experta firing.

To recompute an exported guide with its archived configuration:

```bash
python replay.py docs/evidence/fried_rice_boundary.json
```

The replay checks the configuration hash and implementation hash, then compares ingredients and ordered cooking instructions. New run IDs, timestamps and agenda sequence numbers are excluded from the comparison. Preserve the matching source code and dependency versions with the archive. A source hash detects a difference; it does not itself preserve the old code.

## Public deployment behavior

The rule editor is read-only unless `RULES_ADMIN_TOKEN` is configured. Saves send that token as a Bearer credential. For an isolated local experiment only, `ALLOW_RULE_EDITS=1` permits unauthenticated saves when no token is configured. The Docker Compose example and Railway instructions do not enable that override.

`PROPORTIONS_PATH` selects durable storage. An empty configured location is seeded from the bundled recipe configuration at startup; later restarts retain the edited file. `/healthz` verifies that the active knowledge base can be loaded and validated. Gunicorn serves the application, with debug disabled by default and a one-megabyte request limit.

The previous requirements pinned mutually incompatible Experta and frozendict versions. The installation now uses Experta's declared `frozendict==1.2` dependency with a small `collections.Mapping` compatibility alias before the engine import. No installed third-party files are edited. See the deployment guide for reproducible installation and dependency checks.

## Files and verification

| Area | Main files |
|---|---|
| Calculation and validation | `expertcook/scaling.py`, `expertcook/proportions.py`, `expertcook/planner.py` |
| Execution tracing | `expertcook/audit.py`, `expertcook/engines.py` |
| API and browser explanations | `server.py`, `static/index.html` |
| Deployment | `Dockerfile`, `compose.yaml`, `gunicorn.conf.py`, `railway.json`, `requirements.txt` |
| Reproduction and verification | `replay.py`, `verify.py`, `selftest.py`, `test_regressions.py`, `smoke_web.py` |

`verify.py` runs the core checks, regression tests and a 648-case parameter matrix, then writes the results and three representative guides to `docs/evidence`. The final implementation and results chapter discusses those recorded results. `smoke_web.py` checks a running server without saving or modifying its configuration.

## Scope and limitations

The system generates a guide from declared user parameters. It does not sense tenderness, temperature, moisture, elapsed cooking time or food condition. Instructions containing “if the rice is still hard” remain advice for the cook; the audit records generation of that advice, not observation of that condition.

Ratios are still the repository's mock culinary values. Positive minimum increments can dominate small portions, and displayed quantities are not strictly proportional after rounding. Total liquid is a target; existing sauce and stock volumes are not measured by the software. No claim of cooking quality, user satisfaction or food-safety validation follows from software test success.
