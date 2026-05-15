# API Reference

Auto-generated from the source. Click any class to see its full signature, generic parameters, fields, and methods.

## Public surface (`beekeeper`)

::: beekeeper

## Adapters

### Input

::: beekeeper.adapters.inputs.entity_input_adapter
::: beekeeper.adapters.inputs.allocation_input_adapter
::: beekeeper.adapters.inputs.input_adapter
::: beekeeper.adapters.inputs.mixed_input_adapter
::: beekeeper.adapters.inputs.json_entity_input_adapter
::: beekeeper.adapters.inputs.json_allocation_input_adapter

### Output

::: beekeeper.adapters.outputs.output_adapter
::: beekeeper.adapters.outputs.console

## Entities and allocations

::: beekeeper.entities.entity
::: beekeeper.unavailabilities.unavailability
::: beekeeper.time_constructs.date_range
::: beekeeper.allocations.allocation_type
::: beekeeper.allocations.allocation_request
::: beekeeper.allocations.planned_allocation

## Rules

::: beekeeper.rules.rule_verdict
::: beekeeper.rules.preliminary_rule
::: beekeeper.rules.stateful_rule
::: beekeeper.rules.builtins

## Algorithm

::: beekeeper.algorithm.algorithm
::: beekeeper.algorithm.algorithm_state
::: beekeeper.algorithm.errors
::: beekeeper.algorithm.implementations.backtracking
::: beekeeper.algorithm.implementations.load_balancing
::: beekeeper.algorithm.implementations.or_tools

## Flow

::: beekeeper.flow.beekeeper
::: beekeeper.flow.beekeeper_flow_state
::: beekeeper.flow.candidate
::: beekeeper.flow.flow_stages.base_beekeeper_flow_stage
::: beekeeper.flow.flow_stages.assign_possible_entities_to_allocations
::: beekeeper.flow.flow_stages.run_preliminary_rules
::: beekeeper.flow.flow_stages.run_algorithm_and_dispatch_results

## Data structures

::: beekeeper.data_structures.abstract_enum
