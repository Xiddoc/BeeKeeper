from dataclasses import dataclass


@dataclass(frozen=True)
class RuleVerdict:
    """The outcome of evaluating a single rule against an (entity, allocation) pair.

    A rule's evaluation answers two related questions:

    * **compatible**: does the entity satisfy this rule's hard requirements? A
      ``False`` here drops the candidate from consideration entirely.
    * **score**: how *well* does the entity satisfy this rule, on an arbitrary
      positive scale? Higher is better. A ``score`` of ``1.0`` means the rule
      is fully satisfied without preference; lower scores express soft
      preference. The framework aggregates scores across rules using the
      geometric mean — see ``docs/explanations/soft-rules-aggregation.md``.

    Use the convenience subclasses ``HardPreliminaryRule`` / ``HardStatefulRule``
    to author binary rules, ``SoftPreliminaryRule`` / ``SoftStatefulRule`` to
    author scoring rules; both wrap their result in a ``RuleVerdict``
    automatically.
    """

    compatible: bool
    score: float = 1.0
