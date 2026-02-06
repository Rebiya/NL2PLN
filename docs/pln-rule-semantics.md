# PLN Rule Semantics Spec (Draft)

## Status

Draft spec for the extended rule format discussed in `thoughts.txt`.

## Goals

1. Preserve deterministic, ordered premise evaluation with variable binding flow.
2. Keep operational predicates (`Compute`, `FoldAll`) out of truth-value logic.
3. Support efficient aggregation patterns without exploding proof search.

## Rule Syntax

```lisp
(Implication
  (Premises p1 p2 ...)
  (Conclusions c1 c2 ...))
```

- Premises are evaluated in listed order.
- All premises must succeed (`allOf` semantics).
- `anyOf` is out of scope for this version. Use multiple rules as a workaround.

## Variable Binding Model

Premise evaluation carries an environment of variable bindings:

1. Start with the incoming environment.
2. Evaluate each premise in order.
3. Successful premise matches may extend bindings.
4. Later premises see earlier bindings.
5. Any premise hard-failure fails the whole implication.

Already-bound variables are constraints, not rebindable targets.

## Truth Values

`Compute` and `FoldAll` do not contribute to or modify truth values directly.

- They are control/evaluation steps.
- Rule TV behavior remains defined by existing PLN TV machinery.

## `Compute`

Syntax:

```lisp
(Compute f args -> out)
```

Semantics:

1. Evaluate `f(args)` under current bindings.
2. Pattern-match returned value against `out`.
3. If match succeeds, continue with updated bindings (if any).
4. If match fails or evaluation fails, hard-fail this premise.

`out` can be a variable or a concrete value, enabling filter patterns:

```lisp
(Compute > ($x $y) -> True)
```

## `FoldAll`

Syntax:

```lisp
(FoldAll pattern value init fun -> out)
```

Semantics:

1. Enumerate all matches of `pattern` under current outer bindings.
2. For each match, evaluate `value` under that match binding.
3. Initialize accumulator `acc = init`.
4. For each projected value, apply `fun(acc, value)` to get the next `acc`.
5. If no matches are found, result is `init`.
6. Pattern-match final accumulator against `out`.
7. Match success: continue. Match failure: hard-fail this premise.

### Scope and Binding Rules

1. Variables already bound before `FoldAll` are constraints in `pattern`.
2. Variables newly introduced by `pattern` are local to fold iteration.
3. Local fold variables do not escape the `FoldAll` premise.
4. Only `out` (via pattern match) can affect outer bindings.
5. `fun` only transforms accumulator values; it cannot mutate outer bindings.

## Worked Examples

Ordered binding across premises:

```lisp
(Implication
  (Premises
    (Person $x)
    (Age $x $age)
    (Compute > ($age 17) -> True))
  (Conclusions
    (Adult $x)))
```

Aggregation with local match variable:

```lisp
(Implication
  (Premises
    (Count A $a)
    (Count B $b)
    (FoldAll (Count $name $n) $n 0 (|-> ($acc $x) (+ $acc $x)) -> $sum))
  (Conclusions
    (Count Total $sum)))
```

In the second example, `$a`/`$b` are outer bindings, `$name`/`$n` are fold-local, and only `$sum` escapes.

## Non-Goals (This Draft)

1. `anyOf` inside a single implication.
2. TV algebra changes.
3. Side-effectful operations in `Compute`/`FoldAll`.
