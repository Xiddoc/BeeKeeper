"""
Tests for ``AbstractEnum``'s ``@abstractmethod`` enforcement.

``ABCMeta``'s usual abstract-method check happens inside ``object.__new__``,
which ``EnumMeta`` bypasses when it builds members at class-creation time.
The custom ``_AbstractEnumMeta`` closes that gap by raising ``TypeError`` when
a subclass has members **and** still has unimplemented abstract methods. These
tests pin every branch of that behavior.
"""

from abc import abstractmethod

import pytest

from beekeeper.data_structures.abstract_enum import AbstractEnum


def test_empty_placeholder_subclass_is_allowed() -> None:
    """An empty subclass (the ``AllocationType`` placeholder shape) must work."""

    class Placeholder(AbstractEnum):
        pass

    assert Placeholder.__members__ == {}
    assert Placeholder.__abstractmethods__ == frozenset()


def test_subclass_with_members_and_no_abstracts_is_allowed() -> None:
    """The McDonald's-style ``McAllocType(AllocationType)`` shape must work."""

    class Colors(AbstractEnum):
        RED = "red"
        BLUE = "blue"

    assert Colors.RED.value == "red"
    assert Colors.BLUE.value == "blue"
    assert set(Colors.__members__) == {"RED", "BLUE"}


def test_subclass_with_members_and_unimplemented_abstract_raises() -> None:
    """A subclass that adds members without implementing its abstract method must fail."""
    with pytest.raises(TypeError, match=r"hex_code") as exc_info:

        class Broken(AbstractEnum):
            @abstractmethod
            def hex_code(self) -> str: ...

            RED = "red"

    message = str(exc_info.value)
    assert "Broken" in message
    assert "hex_code" in message


def test_subclass_with_multiple_unimplemented_abstracts_lists_all() -> None:
    """All missing abstract methods should appear in the error message, sorted."""
    with pytest.raises(TypeError) as exc_info:

        class StillBroken(AbstractEnum):
            @abstractmethod
            def second(self) -> int: ...

            @abstractmethod
            def first(self) -> str: ...

            ONLY = "only"

    message = str(exc_info.value)
    assert "first" in message
    assert "second" in message
    # Names are sorted for stable error messages.
    assert message.index("first") < message.index("second")


def test_subclass_that_implements_abstract_method_is_allowed() -> None:
    """If a subclass implements the abstract method in its body, members are fine."""

    class Base(AbstractEnum):
        @abstractmethod
        def hex_code(self) -> str: ...

    class Implemented(Base):
        RED = "red"
        BLUE = "blue"

        def hex_code(self) -> str:
            return {"red": "#ff0000", "blue": "#0000ff"}[self.value]

    assert Implemented.RED.hex_code() == "#ff0000"
    assert Implemented.BLUE.hex_code() == "#0000ff"


def test_abstract_base_without_members_is_allowed() -> None:
    """A subclass that declares abstracts but no members is a valid intermediate base."""

    class Base(AbstractEnum):
        @abstractmethod
        def label(self) -> str: ...

    assert Base.__members__ == {}
    assert "label" in Base.__abstractmethods__
