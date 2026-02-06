# PLN Premises/Conclusions Migration Tracker

## Scope

- Migrate to the new rule shape:
  - `(Implication (Premises ...) (Conclusions ...))`
  - `(Compute f args -> out)`
  - `(FoldAll pattern init fun -> out)`
- No backward compatibility with old syntax is required.

## Working Branches

- NL2PLN: `feature/pln-premises-conclusions`
- PeTTaChainer: `feature_pln_premises_conclusions`

## Process Rules

1. Keep this file updated as tasks move.
2. After each code change, add tests and run relevant test commands before moving on.
3. If a change is docs-only, note that tests were not run for that step.

## Tasks

- [x] T1: Compiler grammar update in PeTTaChainer
  - Accept `Implication` with explicit `Premises` and `Conclusions`.
  - Accept `Compute ... -> ...` and `FoldAll ... -> ...` forms.
- [x] T2: Compile pipeline refactor in PeTTaChainer
  - Replace binary implication handling in `compile_`, `compileQuery`, `pretty`.
  - Preserve ordered premise evaluation and binding propagation.
- [x] T3: `Compute` hard-fail control semantics
  - Remove legacy treatment requiring `Compute` as normal KB atom premise.
  - Keep TV unaffected by `Compute`.
- [x] T4: `FoldAll` implementation
  - Outer bindings constrain pattern.
  - New pattern vars are local.
  - Zero matches return `init`.
  - Only `out` may export binding updates.
  - TV unaffected.
- [x] T5: MeTTa examples and runtime cleanup
  - Update `pettachainer/metta/test.metta`.
  - Update sample atoms in `pettachainer/pettachainer.py`.
  - Fix obvious runtime issues found during migration (e.g. formula typos).
- [x] T6: NL2PLN syntax checker updates
  - Update `src/cleanPLN.py` validation patterns for new syntax.
  - Extend `tests/test_cleanPLN.py` for new valid/invalid forms.
- [x] T7: NL2PLN prompt/spec updates
  - Update signature instructions and `pln_spec` in `src/nl2pln.py`.
  - Include examples for ordered premises, compute filters, and fold aggregation.
- [x] T8: Dataset/example migration
  - Fix `data/counting.json` format.
  - Update `src/usage_example.py` and related examples to new syntax.
- [x] T9: End-to-end verification
  - Run PeTTaChainer tests/examples with new syntax.
  - Run NL2PLN tests and at least one pipeline smoke test.

## Progress Log

- 2026-02-06: Created tracker and defined migration tasks.
- 2026-02-06: Branches created in both repos.
- 2026-02-06: This was a docs-only change; no tests run for this step.
- 2026-02-06: Completed T1 compiler grammar acceptance changes in PeTTaChainer.
- 2026-02-06: Test run: `petta /tmp/t1_grammar_smoke.metta` (new implication + compute arrow syntax), exit code `0`.
- 2026-02-06: Test run: `petta /tmp/t1_checkstmt.metta` (`checkStmt` acceptance for new implication shape), exit code `0`.
- 2026-02-06: Updated `pettachainer/metta/test.metta` to assert existence of `Count C 3` using `!(test ...)` with new syntax.
- 2026-02-06: Test run: `petta ../PeTTaChainer/pettachainer/metta/test.metta`, assertion passed, exit code `0`.
- 2026-02-06: Completed T2 refactor for `compile_`, `compileQuery`, `checkStmt`, and `pretty` to new `Implication (Premises ...) (Conclusions ...)` shape.
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta test.metta`, assertion passed, exit code `0`.
- 2026-02-06: Completed T3 by compiling `Compute` premises to direct `CPU` goals (no KB `Compute` fact bridge required).
- 2026-02-06: Removed legacy runtime bridge rule from `pettachainer/metta/petta_chainer.metta`.
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta test.metta`, assertion passed, exit code `0`.
- 2026-02-06: Hard-fail check: `petta /tmp/t3_hard_fail_check.metta`, assertion passed (`Count C 4` query returned `()`), exit code `0`.
- 2026-02-06: Completed T4 by adding `FoldAll` compile mapping to `FoldAllEval` control goals and runtime evaluation in chainer.
- 2026-02-06: Added `FoldAll` tests for aggregation (`Count Total 6`) and zero-match behavior (`Count MissingTotal 42`) in `pettachainer/metta/test.metta`.
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta test.metta`, all assertions passed, exit code `0`.
- 2026-02-06: Completed T5 runtime/example cleanup.
- 2026-02-06: Fixed `InversionFormula` typo `Stv` -> `STV` in `pettachainer/metta/petta_chainer.metta`.
- 2026-02-06: Updated `pettachainer/pettachainer.py` example atoms/queries to the new implication and compute-arrow syntax.
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta test.metta`, all assertions passed, exit code `0`.
- 2026-02-06: Python syntax check: `python -m py_compile ../PeTTaChainer/pettachainer/pettachainer.py`, exit code `0`.
- 2026-02-06: Completed T6 by updating `checkImpl` to the new implication shape in `src/cleanPLN.py`.
- 2026-02-06: Extended `tests/test_cleanPLN.py` with new implication acceptance and legacy implication rejection cases.
- 2026-02-06: Test run: `pytest tests/test_cleanPLN.py -q`, `12 passed`, exit code `0`.
- 2026-02-06: Completed T7 by updating `NL2PLNSingature` instructions and `pln_spec` in `src/nl2pln.py` to new implication/compute/foldall syntax and examples.
- 2026-02-06: Syntax check: `python -m py_compile src/nl2pln.py`, exit code `0`.
- 2026-02-06: Regression check: `pytest tests/test_cleanPLN.py -q`, `12 passed`, exit code `0`.
- 2026-02-06: Completed T8 by fixing invalid trailing content in `data/counting.json`.
- 2026-02-06: Updated `src/usage_example.py` to a direct new-syntax chainer example using `Premises/Conclusions` and `Compute ... -> ...`.
- 2026-02-06: JSON validation: `python -m json.tool data/counting.json`, exit code `0`.
- 2026-02-06: Syntax check: `python -m py_compile src/usage_example.py`, exit code `0`.
- 2026-02-06: Completed T9 end-to-end verification.
- 2026-02-06: PeTTaChainer verification: `petta test.metta` (from `PeTTaChainer/pettachainer/metta`), all assertions passed, exit code `0`.
- 2026-02-06: NL2PLN unit checks: `pytest tests/test_cleanPLN.py -q`, `12 passed`, exit code `0`.
- 2026-02-06: Pipeline smoke test: `python src/usage_example.py`, query returned `Count Total 5` proofs under new syntax, exit code `0`.
- 2026-02-06: Additional note: direct `nl2pln` import triggers MLflow remote retries in this environment (network unavailable), so dataset-loader smoke via `build_examples_from_file` is not reliable without adjusting MLflow side effects.
- 2026-02-06: Post-T9 update: `FoldAll` now uses explicit projection argument in syntax `(FoldAll pattern value init fun -> out)`.
- 2026-02-06: Added reusable `AddCount` helper to `pettachainer/metta/petta_chainer.metta` to avoid undefined fold functions in generated programs.
- 2026-02-06: Updated prompt/spec docs to the new FoldAll signature in `src/nl2pln.py` and `docs/pln-rule-semantics.md`.
- 2026-02-06: Verification rerun: `petta test.metta` (pass), `python -m py_compile src/nl2pln.py` (pass), `pytest tests/test_cleanPLN.py -q` (`12 passed`).
- 2026-02-06: Fixed `seq2expr` ambiguity in `pettachainer/metta/compile.metta` by replacing overlapping clauses with a single `if (== $tail ()) ...` branch.
- 2026-02-06: Regression check: `petta testlambda.metta` (pass for existing output-only checks).
- 2026-02-06: Regression check: `petta test.metta` (currently failing in `FoldAll` proof assertion after singleton-`And` removal; bridge/compilation path for singleton executable premises under active rework).
- 2026-02-06: Fixed singleton executable-premise compilation after `seq2expr` determinism change by adding direct `compile-inputs` support for standalone `Compute` and `FoldAll`.
- 2026-02-06: Corrected singleton bridge rule shape so `mm2stmt/mm2compile` preserves generated `FoldAllEval`/`CPU` bridge rules.
- 2026-02-06: Updated `pettachainer/metta/test.metta` assertions to concrete expected proofs (no silent pass/fail behavior).
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta test.metta`, all assertions passed, exit code `0`.
- 2026-02-06: Test run (from `PeTTaChainer/pettachainer/metta`): `petta testlambda.metta`, exit code `0`.
