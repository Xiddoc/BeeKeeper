"""Lock the public API surface.

These tests fail if the framework's exposed names change unintentionally.
Adding a public class? Add it to ``EXPECTED_EXPORTS``. Removing one? Same.
The point is that the diff is visible in the test file alongside the
diff that caused it.
"""

import inspect

import beekeeper

EXPECTED_EXPORTS = frozenset(
    {
        "AllocationInputAdapter",
        "AllocationRequest",
        "AllocationType",
        "Algorithm",
        "BeeKeeper",
        "DateRange",
        "Entity",
        "EntityInputAdapter",
        "HardPreliminaryRule",
        "HardStatefulRule",
        "Unavailability",
        "IncompleteSolutionError",
        "InputAdapter",
        "JsonAllocationInputAdapter",
        "JsonEntityInputAdapter",
        "CompositeInputAdapter",
        "OutputAdapter",
        "PlannedAllocation",
        "PreliminaryRule",
        "RuleVerdict",
        "SoftPreliminaryRule",
        "SoftStatefulRule",
        "AssignmentState",
        "StatefulRule",
    },
)


def test_all_matches_expected_exports() -> None:
    assert frozenset(beekeeper.__all__) == EXPECTED_EXPORTS


def test_all_exports_are_actually_importable() -> None:
    for name in beekeeper.__all__:
        assert hasattr(beekeeper, name), f"{name} declared in __all__ but not on the module"


def test_no_underscore_prefixed_exports() -> None:
    """The public API shouldn't include private names by accident."""
    for name in beekeeper.__all__:
        assert not name.startswith("_"), f"{name} is private but exported"


def test_all_is_sorted() -> None:
    """Lockdown that __all__ stays alphabetical so diffs stay readable."""
    assert list(beekeeper.__all__) == sorted(beekeeper.__all__)


def test_rule_classes_inherit_their_advertised_bases() -> None:
    """Hard/Soft rule conveniences must subclass their abstract base; LSP guarantee."""
    assert issubclass(beekeeper.HardPreliminaryRule, beekeeper.PreliminaryRule)
    assert issubclass(beekeeper.SoftPreliminaryRule, beekeeper.PreliminaryRule)
    assert issubclass(beekeeper.HardStatefulRule, beekeeper.StatefulRule)
    assert issubclass(beekeeper.SoftStatefulRule, beekeeper.StatefulRule)


def test_input_adapter_inherits_both_halves() -> None:
    assert issubclass(beekeeper.InputAdapter, beekeeper.EntityInputAdapter)
    assert issubclass(beekeeper.InputAdapter, beekeeper.AllocationInputAdapter)


def test_composite_input_adapter_implements_input_adapter() -> None:
    assert issubclass(beekeeper.CompositeInputAdapter, beekeeper.InputAdapter)


def test_unavailability_extends_daterange() -> None:
    assert issubclass(beekeeper.Unavailability, beekeeper.DateRange)


def test_beekeeper_init_signature_is_keyword_only() -> None:
    """All BeeKeeper.__init__ args except self are keyword-only — protects against
    positional-arg refactors that would silently break callers."""
    sig = inspect.signature(beekeeper.BeeKeeper.__init__)
    parameters = list(sig.parameters.values())
    # First param is `self`. Every subsequent param must be KEYWORD_ONLY.
    for param in parameters[1:]:
        assert param.kind == inspect.Parameter.KEYWORD_ONLY, (
            f"BeeKeeper.__init__ parameter {param.name!r} must be keyword-only but is {param.kind.name}"
        )


def test_beekeeper_required_kwargs() -> None:
    """input_adapter is the only kwarg without a default; everything else
    is optional. This is the contract the docs promise."""
    sig = inspect.signature(beekeeper.BeeKeeper.__init__)
    required = {
        name for name, param in sig.parameters.items() if name != "self" and param.default is inspect.Parameter.empty
    }
    assert required == {"input_adapter"}
