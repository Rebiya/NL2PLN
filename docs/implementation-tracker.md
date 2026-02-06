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
- [ ] T3: `Compute` hard-fail control semantics
  - Remove legacy treatment requiring `Compute` as normal KB atom premise.
  - Keep TV unaffected by `Compute`.
- [ ] T4: `FoldAll` implementation
  - Outer bindings constrain pattern.
  - New pattern vars are local.
  - Zero matches return `init`.
  - Only `out` may export binding updates.
  - TV unaffected.
- [ ] T5: MeTTa examples and runtime cleanup
  - Update `pettachainer/metta/test.metta`.
  - Update sample atoms in `pettachainer/pettachainer.py`.
  - Fix obvious runtime issues found during migration (e.g. formula typos).
- [ ] T6: NL2PLN syntax checker updates
  - Update `src/cleanPLN.py` validation patterns for new syntax.
  - Extend `tests/test_cleanPLN.py` for new valid/invalid forms.
- [ ] T7: NL2PLN prompt/spec updates
  - Update signature instructions and `pln_spec` in `src/nl2pln.py`.
  - Include examples for ordered premises, compute filters, and fold aggregation.
- [ ] T8: Dataset/example migration
  - Fix `data/counting.json` format.
  - Update `src/usage_example.py` and related examples to new syntax.
- [ ] T9: End-to-end verification
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
