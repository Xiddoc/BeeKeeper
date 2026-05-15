from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from pydantic import TypeAdapter

from beekeeper.adapters.inputs.entity_input_adapter import EntityInputAdapter
from beekeeper.entities.entity import AnyEntity


@dataclass
class JsonEntityInputAdapter[TEntity: AnyEntity](EntityInputAdapter[TEntity]):
    """Strict JSON-backed adapter that loads entities from a file.

    The file must contain a JSON array of objects matching ``entity_type``'s
    schema. Validation is strict: any field not declared on the target
    entity (or any field declared on a nested model and unset on the JSON)
    will raise. This is enforced at the framework level — the framework's
    ``Entity`` base class sets ``model_config = ConfigDict(extra="forbid")``,
    which subclasses inherit unless they explicitly opt out.

    Want lenient parsing for legacy data, exploratory work, or
    third-party feeds? Implement your own ``EntityInputAdapter`` subclass
    — the core only ships strict, well-defined, Pydantic-backed adapters.
    """

    file: Path
    entity_type: type[TEntity]

    def get_entities(self) -> Iterable[TEntity]:
        adapter: TypeAdapter[list[TEntity]] = TypeAdapter(list[self.entity_type])  # type: ignore[name-defined]
        return adapter.validate_json(self.file.read_text())
