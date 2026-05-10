"""Regenerate the McDonald's stress-test fixtures.

Generated files (all checked in):

* ``workers_large.json``   /  ``allocations_large.json``    —  65 workers, 25 allocations
* ``workers_xlarge.json``  /  ``allocations_xlarge.json``   — 100 workers, 40 allocations
* ``workers_xxlarge.json`` /  ``allocations_xxlarge.json``  — 200 workers, 80 allocations

The two larger fixtures crank up the property variety on each worker:
inavailabilities are denser, more varied in length, and more clustered;
allocations exercise multi-entity required_count and explicit
requested_entities; the rank-vs-allowed-ranks intersection is wider.
This is what the benchmark suite throws at the algorithm to make sure
it scales.

Each size is deterministic for a given seed. Re-running with the same
seed reproduces the exact same JSON.

Run with::

    cd examples/
    uv run python -m mcdonalds.scripts.generate_large_fixtures
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

SEED = 42

ALLOCATION_TYPES = ("CLEANING", "COOKING", "SERVING_FOOD", "ANSWERING_DRIVE_THRU")

TYPE_TO_RANKS: dict[str, list[str]] = {
    "CLEANING": ["CASHIER", "MANAGER"],
    "COOKING": ["COOK", "MANAGER"],
    "SERVING_FOOD": ["CASHIER", "MANAGER"],
    "ANSWERING_DRIVE_THRU": ["CASHIER"],
}

TYPE_TO_REQUIRED_COUNT: dict[str, list[int]] = {
    "CLEANING": [1, 1, 1, 2],
    "COOKING": [1, 2, 2, 3],
    "SERVING_FOOD": [1, 1, 1, 2],
    "ANSWERING_DRIVE_THRU": [1, 1, 1, 2],
}

INAVAILABILITY_REASONS = (
    "vacation",
    "doctor's appointment",
    "family wedding",
    "school event",
    "moving day",
    "jury duty",
    "religious holiday",
    "personal day",
    "training course",
    "bereavement",
)

PLANNING_WINDOW_START = datetime(2025, 6, 1)
PLANNING_WINDOW_END = datetime(2025, 9, 30)


@dataclass(frozen=True)
class FixtureSpec:
    """One size of fixture: how many workers, how many allocations, output suffix."""

    suffix: str
    worker_count: int
    allocation_count: int
    inavailability_count_choices: tuple[int, ...]
    inavailability_count_weights: tuple[int, ...]
    inavailability_length_choices: tuple[int, ...]
    inavailability_length_weights: tuple[int, ...]
    allocation_length_choices: tuple[int, ...]
    allocation_length_weights: tuple[int, ...]
    requested_entities_probability: float


PRESETS = (
    # 65-worker fixture: the smallest of the three. Used by the basic benchmark.
    FixtureSpec(
        suffix="large",
        worker_count=65,
        allocation_count=25,
        inavailability_count_choices=(0, 1, 2, 3),
        inavailability_count_weights=(40, 35, 20, 5),
        inavailability_length_choices=(1, 2, 3, 4, 5, 6, 7),
        inavailability_length_weights=(1,) * 7,
        allocation_length_choices=(1, 2, 3, 5, 7),
        allocation_length_weights=(40, 25, 15, 10, 10),
        requested_entities_probability=0.0,
    ),
    # 100-worker fixture: denser inavailabilities, occasional pre-requested entities,
    # wider variety of inavailability lengths.
    FixtureSpec(
        suffix="xlarge",
        worker_count=100,
        allocation_count=40,
        inavailability_count_choices=(0, 1, 2, 3, 4, 5),
        inavailability_count_weights=(15, 25, 25, 20, 10, 5),
        inavailability_length_choices=(1, 2, 3, 4, 5, 7, 10, 14),
        inavailability_length_weights=(30, 25, 15, 10, 8, 5, 4, 3),
        allocation_length_choices=(1, 2, 3, 5, 7, 10, 14),
        allocation_length_weights=(40, 25, 15, 8, 6, 4, 2),
        requested_entities_probability=0.15,
    ),
    # 200-worker fixture: even denser inavailabilities, more pre-requested entities.
    # Every axis the algorithm has to deal with is dialled up here.
    FixtureSpec(
        suffix="xxlarge",
        worker_count=200,
        allocation_count=80,
        inavailability_count_choices=(1, 2, 3, 4, 5, 6, 7),
        inavailability_count_weights=(10, 15, 25, 25, 15, 7, 3),
        inavailability_length_choices=(1, 2, 3, 4, 5, 7, 10, 14),
        inavailability_length_weights=(30, 25, 15, 10, 8, 5, 4, 3),
        allocation_length_choices=(1, 2, 3, 5, 7, 10, 14),
        allocation_length_weights=(40, 25, 15, 8, 6, 4, 2),
        requested_entities_probability=0.20,
    ),
)


def _rank_mix(worker_count: int) -> list[str]:
    cashiers = round(worker_count * 0.50)
    cooks = round(worker_count * 0.34)
    managers = worker_count - cashiers - cooks
    return ["CASHIER"] * cashiers + ["COOK"] * cooks + ["MANAGER"] * managers


def _random_date(rng: random.Random) -> datetime:
    span_days = (PLANNING_WINDOW_END - PLANNING_WINDOW_START).days
    return PLANNING_WINDOW_START + timedelta(days=rng.randint(0, span_days))


def _generate_inavailabilities(spec: FixtureSpec, rng: random.Random) -> list[dict[str, str | bool]]:
    count = rng.choices(spec.inavailability_count_choices, weights=spec.inavailability_count_weights)[0]
    out: list[dict[str, str | bool]] = []
    for _ in range(count):
        start = _random_date(rng)
        length = rng.choices(spec.inavailability_length_choices, weights=spec.inavailability_length_weights)[0]
        end = start + timedelta(days=length)
        out.append(
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "reason": rng.choice(INAVAILABILITY_REASONS),
                "is_paid_leave": rng.random() < 0.4,
            },
        )
    return out


def _generate_workers(spec: FixtureSpec, fake: Faker, rng: random.Random) -> list[dict[str, object]]:
    rank_mix = _rank_mix(spec.worker_count)
    rng.shuffle(rank_mix)
    return [
        {
            "name": fake.name(),
            "rank": rank_mix[i],
            "inavailabilities": _generate_inavailabilities(spec, rng),
        }
        for i in range(spec.worker_count)
    ]


def _generate_allocations(
    spec: FixtureSpec,
    workers: list[dict[str, object]],
    rng: random.Random,
) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for _ in range(spec.allocation_count):
        alloc_type = rng.choice(ALLOCATION_TYPES)
        start = _random_date(rng)
        length = rng.choices(spec.allocation_length_choices, weights=spec.allocation_length_weights)[0]
        end = start + timedelta(days=length - 1)

        # Optionally pre-request 1–2 specific workers (must match an allowed rank).
        eligible_ranks = TYPE_TO_RANKS[alloc_type]
        requested_entities: list[dict[str, object]] = []
        if rng.random() < spec.requested_entities_probability:
            candidates = [w for w in workers if w["rank"] in eligible_ranks]
            if candidates:
                pick_count = rng.choice([1, 1, 2])
                picked = rng.sample(candidates, k=min(pick_count, len(candidates)))
                requested_entities = [
                    {"name": w["name"], "rank": w["rank"], "inavailabilities": w["inavailabilities"]} for w in picked
                ]

        out.append(
            {
                "allocation_type": alloc_type,
                "date_range": {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
                "allowed_ranks": eligible_ranks,
                "required_count": rng.choice(TYPE_TO_REQUIRED_COUNT[alloc_type]),
                "requested_entities": requested_entities,
            },
        )
    return out


def _generate_one(spec: FixtureSpec, fixtures_dir: Path) -> None:
    # Each preset uses a fresh seeded RNG so its output is independent of
    # iteration order and earlier presets' RNG consumption.
    fake = Faker()
    Faker.seed(SEED)
    rng = random.Random(SEED)

    workers = _generate_workers(spec, fake, rng)
    allocations = _generate_allocations(spec, workers, rng)

    (fixtures_dir / f"workers_{spec.suffix}.json").write_text(json.dumps(workers, indent=2) + "\n")
    (fixtures_dir / f"allocations_{spec.suffix}.json").write_text(json.dumps(allocations, indent=2) + "\n")

    print(f"  {spec.suffix:>8s}: {len(workers):3d} workers, {len(allocations):3d} allocations")


def main() -> None:
    fixtures_dir = Path(__file__).resolve().parent.parent

    print("Generating fixtures:")
    for spec in PRESETS:
        _generate_one(spec, fixtures_dir)


if __name__ == "__main__":
    main()
