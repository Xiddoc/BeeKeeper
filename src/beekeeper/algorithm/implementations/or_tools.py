"""OR-Tools CP-SAT-backed assignment algorithm.

Optional. Requires the ``ortools`` extra::

    pip install 'beekeeper[ortools]'
    uv add 'beekeeper[ortools]'

Importing this module without OR-Tools installed succeeds; instantiating
the algorithm class raises ``ImportError`` with the install hint. This
keeps ``beekeeper.algorithm.implementations`` importable in environments
that don't need OR-Tools while still providing a clear error when the
algorithm is actually used.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from beekeeper.algorithm.algorithm_state import State
from beekeeper.algorithm.base_algorithm import BaseAlgorithm
from beekeeper.allocations.allocation_request import AllocationRequest
from beekeeper.allocations.planned_allocation import PlannedAllocation
from beekeeper.entities.entity import Entity
from beekeeper.flow.candidate import Candidate
from beekeeper.rules.stateful_rule import StatefulRule

try:
    from ortools.sat.python import cp_model
except ImportError:
    cp_model = None  # type: ignore[assignment]

# CP-SAT works in integers; we scale float scores to ints with this factor.
# 1000 keeps three decimal digits of resolution, which is well above the
# noise floor of typical preliminary-rule scores.
SCORE_SCALE = 1000

# Default wall-clock cap for the CP-SAT solver. The model build is fast; the
# variability is in the solver's branch-and-bound search, which can spike from
# ~50 ms on easy problems to multiple seconds on hard ones with many tied
# optima. Capping the solver lets the algorithm return a feasible (not
# necessarily optimal) result quickly. Domains that need full optimality can
# pass a larger limit via the constructor.
DEFAULT_SOLVER_TIME_LIMIT_SECONDS = 0.5


class OrToolsAssignmentAlgorithm[
    TEntity: Entity[Any],
    TAllocationRequest: AllocationRequest[Any, Any],
](
    BaseAlgorithm[TEntity, TAllocationRequest],
):
    """Constraint-programming solver via Google OR-Tools' CP-SAT backend.

    Formulates the assignment as an integer program:

    * **Variables.** ``x[i, j]`` is a boolean: 1 if entity ``j`` is assigned
      to allocation ``i``, 0 otherwise. Variables are only created for
      (allocation, entity) pairs that appear in the candidate map — pairs
      pruned by stage-1 inavailability filtering or stage-2 preliminary
      rules don't enter the formulation at all.
    * **Constraints.** For each allocation, the sum of its ``x[i, j]``
      values is either 0 (unfulfilled) or exactly ``required_count`` —
      no partial fills.
    * **Objective.** Maximize the total weighted score of assignments,
      where each ``x[i, j]`` is weighted by the candidate's score from
      stage 2. The solver naturally prefers full coverage; ties are broken
      by score.

    Stateful rules are *not* modeled in the CP-SAT formulation. Encoding
    arbitrary Python predicates as CP-SAT constraints is the wrong tool —
    rules are imperative code, not declarative constraints. Domains that
    need stateful guarantees should compose this algorithm with a
    post-processing step (or use ``BacktrackingAssignmentAlgorithm``,
    which evaluates stateful rules during the search).

    Pros over greedy/backtracking:

    * Globally optimal under the modeled constraints.
    * Scales well to thousands of variables; CP-SAT is industrial-grade.

    Cons:

    * Heavy dependency (``ortools`` is ~50 MB).
    * No stateful-rule support.
    * Solver overhead: small problems (the McDonald's fixtures) often
      finish slower than greedy due to model-build and solver-init
      costs. Pays off above ~500 entity-allocation pairs.
    """

    def __init__(self, solver_time_limit_seconds: float = DEFAULT_SOLVER_TIME_LIMIT_SECONDS) -> None:
        if cp_model is None:
            msg = (
                "OR-Tools is required for OrToolsAssignmentAlgorithm but is not installed. "
                "Install with: pip install 'beekeeper[ortools]' (or 'uv add beekeeper[ortools]')."
            )
            raise ImportError(msg)
        self._solver_time_limit_seconds = solver_time_limit_seconds

    def run(
        self,
        allocations: Iterable[TAllocationRequest],
        entities: Iterable[TEntity],
        candidates: Mapping[int, list[Candidate[TEntity]]],
        rules: Iterable[StatefulRule[TEntity, TAllocationRequest]],
    ) -> State[TEntity, TAllocationRequest]:
        del rules  # CP-SAT formulation doesn't model stateful rules — see class docstring
        allocations_list = list(allocations)
        entities_list = list(entities)
        entity_index_by_id = {id(e): idx for idx, e in enumerate(entities_list)}

        model = cp_model.CpModel()

        # x[(i, j)] — entity j assigned to allocation i. Only candidate pairs.
        # score_for[(i, j)] — the candidate's score, used in the objective.
        x: dict[tuple[int, int], Any] = {}
        score_for: dict[tuple[int, int], int] = {}
        for i, alloc in enumerate(allocations_list):
            for cand in candidates.get(id(alloc), []):
                j = entity_index_by_id.get(id(cand.entity))
                if j is None:
                    continue
                x[(i, j)] = model.new_bool_var(f"x_{i}_{j}")
                score_for[(i, j)] = int(cand.score * SCORE_SCALE)

        # Each allocation: sum of assignments is 0 or required_count.
        for i, alloc in enumerate(allocations_list):
            slot_vars = [x[(i, j)] for j in range(len(entities_list)) if (i, j) in x]
            if not slot_vars:
                continue  # no candidates; allocation will be unfulfilled
            is_filled = model.new_bool_var(f"filled_{i}")
            model.add(sum(slot_vars) == alloc.required_count).only_enforce_if(is_filled)
            model.add(sum(slot_vars) == 0).only_enforce_if(is_filled.Not())

        # Objective: maximize total weighted assignments.
        objective_terms = [score_for[k] * x[k] for k in x]
        if objective_terms:
            model.maximize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self._solver_time_limit_seconds
        status = solver.solve(model)

        state: State[TEntity, TAllocationRequest] = State()
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return state

        for i, alloc in enumerate(allocations_list):
            assigned: tuple[TEntity, ...] = tuple(
                entities_list[j] for j in range(len(entities_list)) if (i, j) in x and solver.value(x[(i, j)]) == 1
            )
            if len(assigned) == alloc.required_count:
                state.add_allocation(PlannedAllocation(request=alloc, assigned_entities=assigned))

        return state
