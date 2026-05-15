from abc import ABCMeta
from enum import Enum, EnumMeta


class _AbstractEnumMeta(EnumMeta, ABCMeta):
    """Metaclass mixing ``EnumMeta`` and ``ABCMeta`` with real abstract enforcement.

    ``ABCMeta`` normally blocks instantiation of classes that still carry
    ``__abstractmethods__`` by hooking into ``object.__new__``. ``EnumMeta``
    constructs members during *class* creation via its own ``__new__`` and
    bypasses that hook, so without this metaclass an abstract method on an
    enum subclass with members silently returns ``None`` when called.

    This metaclass closes the gap by failing class creation itself when a
    subclass has members **and** still has unimplemented abstract methods.
    Empty placeholder subclasses (no members) remain allowed so callers can
    use the ``AllocationType``-style pattern of subclassing once just to mark
    a domain vocabulary, then subclassing again to add the concrete members.
    """

    def __init__(cls, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        abstracts: frozenset[str] = getattr(cls, "__abstractmethods__", frozenset())
        members: dict[str, object] = getattr(cls, "__members__", {})
        if abstracts and members:
            missing = ", ".join(sorted(abstracts))
            raise TypeError(
                f"Cannot create enum {cls.__name__!r} with members "
                f"while abstract method(s) are unimplemented: {missing}"
            )


class AbstractEnum(Enum, metaclass=_AbstractEnumMeta):
    """``Enum`` base that honors ``@abstractmethod`` on its subclasses.

    Subclasses that declare abstract methods must implement them before
    adding members; otherwise class creation raises ``TypeError``. Empty
    subclasses (no members) are allowed so the codebase's two-step pattern
    — define a domain placeholder, then a concrete enum that fills it in —
    keeps working.
    """
