"""
Tests for the JSON-backed input adapters.

Both ``JsonEntityInputAdapter`` and ``JsonAllocationInputAdapter`` wrap
``pydantic.ValidationError`` in a ``ValueError`` that names the source
file, so a validation failure in a multi-file setup (e.g. via
``CompositeInputAdapter``) can be traced back to the offending file.
"""
import re
from enum import auto
from pathlib import Path

import pytest
from pydantic import ValidationError

from beekeeper import AllocationRequest, AllocationType, Entity, Unavailability
from beekeeper.adapters.inputs.json_allocation_input_adapter import (
    JsonAllocationInputAdapter,
)
from beekeeper.adapters.inputs.json_entity_input_adapter import JsonEntityInputAdapter


class _Task(AllocationType):
    SHIFT = auto()


class _Worker(Entity[Unavailability]):
    name: str


class _Request(AllocationRequest[_Task, _Worker]):
    pass


def _write(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.write_text(content)
    return file


def test_entity_adapter_malformed_json_names_file(tmp_path: Path) -> None:
    file = _write(tmp_path, "workers.json", "{not valid json")
    adapter = JsonEntityInputAdapter(file=file, entity_type=_Worker)

    with pytest.raises(ValueError, match=re.escape("workers.json")) as exc_info:
        list(adapter.get_entities())

    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_entity_adapter_extra_field_names_file(tmp_path: Path) -> None:
    file = _write(tmp_path, "workers.json", '[{"name": "Alice", "totally_unknown_field": 1}]')
    adapter = JsonEntityInputAdapter(file=file, entity_type=_Worker)

    with pytest.raises(ValueError, match=re.escape("workers.json")) as exc_info:
        list(adapter.get_entities())

    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_entity_adapter_valid_file_unchanged(tmp_path: Path) -> None:
    file = _write(tmp_path, "workers.json", '[{"name": "Alice", "unavailabilities": []}]')
    adapter = JsonEntityInputAdapter(file=file, entity_type=_Worker)

    entities = list(adapter.get_entities())

    assert len(entities) == 1
    assert entities[0].name == "Alice"


def test_allocation_adapter_malformed_json_names_file(tmp_path: Path) -> None:
    file = _write(tmp_path, "allocations.json", "{not valid json")
    adapter = JsonAllocationInputAdapter(file=file, allocation_type=_Request)

    with pytest.raises(ValueError, match=re.escape("allocations.json")) as exc_info:
        list(adapter.get_allocations())

    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_allocation_adapter_extra_field_names_file(tmp_path: Path) -> None:
    file = _write(
        tmp_path,
        "allocations.json",
        '[{"allocation_type": "SHIFT", "totally_unknown_field": 1}]',
    )
    adapter = JsonAllocationInputAdapter(file=file, allocation_type=_Request)

    with pytest.raises(ValueError, match=re.escape("allocations.json")) as exc_info:
        list(adapter.get_allocations())

    assert isinstance(exc_info.value.__cause__, ValidationError)
