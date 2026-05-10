# Soft-Rules Aggregation

When `RunPreliminaryRules` evaluates a candidate against multiple rules, each rule contributes a `RuleVerdict(compatible=..., score=...)`. The framework needs to combine the per-rule scores into a single number for the `Candidate.score` the algorithm consumes.

BeeKeeper uses the **geometric mean** across rule scores:

\[
\text{aggregate} = \left( \prod_{i=1}^{n} s_i \right)^{1/n}
\]

For two rules scoring `0.4` and `0.9`, the candidate's final score is `sqrt(0.4 * 0.9) ≈ 0.6`.

## Why not arithmetic mean?

The arithmetic mean treats rules as additive — a high score on one rule can compensate for a low score on another, even if the low score reflects a real concern. With `0.4` and `0.9` you'd get `0.65`, which feels too forgiving of the `0.4`. Soft preferences are usually better thought of as multiplicative factors: each rule's score is "this entity is `s_i` of the way to ideal *for this concern*." The geometric mean preserves that intuition.

## Why not pure product?

Pure product (`0.4 * 0.9 = 0.36`) collapses fast as rules accumulate — five neutral rules at `0.9` each would give `0.59`, which feels too pessimistic. Geometric mean *is* the per-rule normalized version of the product, and stays in the same range as its inputs.

## The neutral default of `1.0`

A score of `1.0` is neutral: it doesn't move the geometric mean. Hard rules that pass return `RuleVerdict(compatible=True, score=1.0)` by default, so combining hard rules and soft rules in the same pipeline doesn't penalize candidates for the hard checks alone.

## Edge cases

- **No rules**: aggregate is `1.0` (the empty product convention).
- **Any score `<= 0`**: aggregate is `0.0`. Negative scores aren't expected — the soft-rule API documents `score: float` as non-negative.

## When to override

If your domain wants different aggregation — arithmetic mean, weighted, min — write your own version of `RunPreliminaryRules` and pass it via `BeeKeeper(stages=...)`. See [Customize the pipeline](../how-to/customize-the-pipeline.md).
