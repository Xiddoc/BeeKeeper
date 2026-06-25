import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleVerdict:
    """
    The outcome of evaluating a single rule against an (entity, allocation) pair.

    A rule's evaluation answers two related questions:

    * **compatible**: does the entity satisfy this rule's hard requirements? A
      ``False`` here drops the candidate from consideration entirely.
    * **score**: how *well* does the entity satisfy this rule, on an arbitrary
      non-negative finite scale? Higher is better. A ``score`` of ``1.0``
      means the rule is fully satisfied without preference; lower scores
      express soft preference. A ``score`` of ``0.0`` collapses the
      geometric-mean aggregate to zero, ranking the candidate last, but does
      *not* exclude it: a zero-scored candidate is still recorded and remains
      assignable when no better candidate exists. To exclude a candidate
      outright, return ``compatible=False`` rather than a zero score. The
      framework aggregates scores across rules using the geometric mean —
      see ``docs/explanations/soft-rules-aggregation.md``.

      ``NaN``, ``inf``, ``-inf``, and negative scores are rejected at
      construction. NaN in particular would poison the aggregator (it flows
      through ``math.log``), and inf / negative values produce nonsense
      orderings; failing loudly at the rule boundary keeps the pipeline's
      downstream invariants intact.

    Use the convenience subclasses ``HardPreliminaryRule`` / ``HardStatefulRule``
    to author binary rules, ``SoftPreliminaryRule`` / ``SoftStatefulRule`` to
    author scoring rules; both wrap their result in a ``RuleVerdict``
    automatically.
    """

    compatible: bool
    score: float = 1.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.score) or self.score < 0:
            msg = f"RuleVerdict.score must be a finite, non-negative float (got {self.score!r})"
            raise ValueError(msg)
