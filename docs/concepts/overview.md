# Overview

BeeKeeper is built around six concepts. They form a small, orthogonal vocabulary that scales from a 5-worker McDonald's roster to a multi-line warehouse with capability-tracked equipment.

| Concept | One-line definition |
| --- | --- |
| **Entity** | Something you can assign to work — a worker, a vehicle, a machine. Carries its own *unavailabilities*. |
| **AllocationRequest** | A slot to fill. Has a `date_range`, an `allocation_type`, optionally a list of pre-requested entities. |
| **PlannedAllocation** | The outcome of a successful assignment: a request paired with its assigned entities. |
| **Rule** | A constraint. *Preliminary* rules run before the algorithm (static checks like rank eligibility); *stateful* rules run during assignment with access to the in-progress schedule. |
| **Algorithm** | Your assignment strategy. Receives candidates, entities, and stateful rules; returns the final State. |
| **InputAdapter / OutputAdapter** | How data gets in and out. JSON adapters ship in core; you can write your own for any source/sink. |

A `BeeKeeper` instance wires these together and runs them through a three-stage pipeline.

## What BeeKeeper is

BeeKeeper is **a framework**. It hands you abstract base classes, runs them through a fixed orchestration, and stays out of your domain. The framework knows nothing about cashiers, line positions, certifications, or shift swaps — it knows that you will define those, and it makes sure the types you define propagate cleanly through every layer.

## What BeeKeeper isn't

- **It isn't a solver.** The bundled `LoadBalancingAssignmentAlgorithm` is a reference impl that picks the highest-scored compatible candidate per allocation, with a load penalty (`score / (1 + load)`) so work disperses across the pool instead of concentrating on a few high-scorers. That's fine for examples and trivial scheduling. For nontrivial scheduling you supply your own algorithm — backtracking, constraint propagation, an OR-Tools bridge, whatever fits.
- **It isn't a calendar UI.** Output adapters can format planned allocations however you like (console, JSON, database), but BeeKeeper itself doesn't render anything.
- **It isn't a data store.** Input adapters load from your sources at execute time; the framework holds nothing across runs. If you need persistence between executions, build it into your adapters or above the framework.
- **It isn't opinionated about your domain.** Rules and algorithms know about your specific Entity and AllocationRequest subclasses, not the other way around.

## The mental model

Read [`concepts/pipeline.md`](pipeline.md) for the data flow through the three default stages, [`concepts/type-system.md`](type-system.md) for how generic parameters propagate, [`concepts/rules.md`](rules.md) for the rule taxonomy, and [`concepts/algorithm-contract.md`](algorithm-contract.md) for what your `BaseAlgorithm.run` is allowed to assume and required to return.
