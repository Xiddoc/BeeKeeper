"""Regenerate the large McDonald's fixtures (workers_large.json, allocations_large.json).

The generated files are checked in — this script is here for reproducibility, so
benchmarks and load tests have a stable, sizable dataset that's not produced anew
on every test run. Regenerate by running:

    cd examples/
    uv run python -m mcdonalds.scripts.generate_large_fixtures

Both files are deterministic for a given seed.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from faker import Faker

SEED = 42
WORKER_COUNT = 65
ALLOCATION_COUNT = 25

# Roster mix: roughly half cashiers, a third cooks, the rest managers.
RANK_MIX = ["CASHIER"] * 32 + ["COOK"] * 22 + ["MANAGER"] * 11

ALLOCATION_TYPES = ("CLEANING", "COOKING", "SERVING_FOOD", "ANSWERING_DRIVE_THRU")

# Each allocation type's eligible ranks; some allocations also accept managers as
# a fallback rank (managers are universally cross-trained in this fictional org).
TYPE_TO_RANKS: dict[str, list[str]] = {
    "CLEANING": ["CASHIER", "MANAGER"],
    "COOKING": ["COOK", "MANAGER"],
    "SERVING_FOOD": ["CASHIER", "MANAGER"],
    "ANSWERING_DRIVE_THRU": ["CASHIER"],
}

# A cooking shift typically wants two people on the line; everything else is
# usually a single-entity shift. Express as a per-type multi-entity probability.
TYPE_TO_REQUIRED_COUNT: dict[str, list[int]] = {
    "CLEANING": [1, 1, 1, 2],
    "COOKING": [1, 2, 2, 3],
    "SERVING_FOOD": [1, 1, 1, 2],
    "ANSWERING_DRIVE_THRU": [1, 1],
}

INAVAILABILITY_REASONS = (
    "vacation",
    "doctor's appointment",
    "family wedding",
    "school event",
    "moving day",
    "jury duty",
    "religious holiday",
)

PLANNING_WINDOW_START = datetime(2025, 6, 1)
PLANNING_WINDOW_END = datetime(2025, 7, 31)


def _random_date(rng: random.Random) -> datetime:
    span_days = (PLANNING_WINDOW_END - PLANNING_WINDOW_START).days
    return PLANNING_WINDOW_START + timedelta(days=rng.randint(0, span_days))


def _generate_inavailabilities(rng: random.Random) -> list[dict[str, str | bool]]:
    """0–3 inavailabilities per worker, biased toward 0–1."""
    count = rng.choices([0, 1, 2, 3], weights=[40, 35, 20, 5])[0]
    out: list[dict[str, str | bool]] = []
    for _ in range(count):
        start = _random_date(rng)
        length = rng.randint(1, 7)
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


def _generate_workers(fake: Faker, rng: random.Random) -> list[dict[str, object]]:
    rng.shuffle(RANK_MIX)
    return [
        {
            "name": fake.name(),
            "rank": RANK_MIX[i % len(RANK_MIX)],
            "inavailabilities": _generate_inavailabilities(rng),
        }
        for i in range(WORKER_COUNT)
    ]


def _generate_allocations(rng: random.Random) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for _ in range(ALLOCATION_COUNT):
        alloc_type = rng.choice(ALLOCATION_TYPES)
        start = _random_date(rng)
        # Most allocations are 1–3 days; a handful are week-long.
        length = rng.choices([1, 2, 3, 5, 7], weights=[40, 25, 15, 10, 10])[0]
        end = start + timedelta(days=length - 1)
        out.append(
            {
                "allocation_type": alloc_type,
                "date_range": {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                },
                "allowed_ranks": TYPE_TO_RANKS[alloc_type],
                "required_count": rng.choice(TYPE_TO_REQUIRED_COUNT[alloc_type]),
                "requested_entities": [],
            },
        )
    return out


def main() -> None:
    fake = Faker()
    Faker.seed(SEED)
    rng = random.Random(SEED)

    fixtures_dir = Path(__file__).resolve().parent.parent

    workers = _generate_workers(fake, rng)
    allocations = _generate_allocations(rng)

    (fixtures_dir / "workers_large.json").write_text(json.dumps(workers, indent=2) + "\n")
    (fixtures_dir / "allocations_large.json").write_text(json.dumps(allocations, indent=2) + "\n")

    print(f"Generated {len(workers)} workers and {len(allocations)} allocations.")


if __name__ == "__main__":
    main()
