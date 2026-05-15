"""Validation tests for ``RuleVerdict``.

The geometric-mean aggregator in ``RunPreliminaryRules`` takes
``math.log(score)``. NaN propagates through the log; inf and negative
values produce nonsense orderings. Failing loudly at construction keeps
the aggregator's invariants honest.
"""

import math

import pytest

from beekeeper import RuleVerdict


def test_default_score_accepted() -> None:
    verdict = RuleVerdict(compatible=True)
    assert verdict.score == 1.0


def test_zero_score_accepted_for_drop_semantics() -> None:
    """``0.0`` is the intentional "soft drop" signal; the aggregator handles it."""
    verdict = RuleVerdict(compatible=True, score=0.0)
    assert verdict.score == 0.0


def test_positive_finite_score_accepted() -> None:
    verdict = RuleVerdict(compatible=True, score=0.7)
    assert verdict.score == 0.7


def test_nan_score_rejected() -> None:
    with pytest.raises(ValueError, match="finite, non-negative"):
        RuleVerdict(compatible=True, score=float("nan"))


def test_positive_infinity_score_rejected() -> None:
    with pytest.raises(ValueError, match="finite, non-negative"):
        RuleVerdict(compatible=True, score=math.inf)


def test_negative_infinity_score_rejected() -> None:
    with pytest.raises(ValueError, match="finite, non-negative"):
        RuleVerdict(compatible=True, score=-math.inf)


def test_negative_score_rejected() -> None:
    with pytest.raises(ValueError, match="finite, non-negative"):
        RuleVerdict(compatible=True, score=-0.5)
