
# 🐝 BeeKeeper: Smart Allocation Framework

<p align="center">
  <img src="https://via.placeholder.com/150?text=BeeKeeper+Logo" alt="BeeKeeper Logo Placeholder" width="150"/>
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/beekeeper?style=for-the-badge&logo=pypi&color=blue" alt="PyPI version">
  <img src="https://img.shields.io/pypi/pyversions/beekeeper?style=for-the-badge&logo=python&color=blue" alt="Python versions">
  <img src="https://img.shields.io/github/license/Xiddoc/beekeeper?style=for-the-badge&color=green" alt="GitHub license">
  <img src="https://img.shields.io/github/actions/workflow/status/Xiddoc/beekeeper/main.yml?branch=main&style=for-the-badge&logo=githubactions&label=tests" alt="Build Status">
  <img src="https://img.shields.io/readthedocs/beekeeper?style=for-the-badge&logo=readthedoc&color=blueviolet" alt="Documentation Status">
</p>

**BeeKeeper** is a powerful and flexible Python framework designed to simplify the complex process of allocating tasks, shifts, or assignments to available workers (we call them **Entities**! 🧑‍💼👩‍🍳). It takes the headache out of manual scheduling by allowing you to define your own rules, integrate various data sources, and use custom algorithms to find the perfect match for every task.

Inspired by the challenge of assigning work in a "Busy" (🐝) environment, BeeKeeper helps managers efficiently distribute tasks while considering numerous constraints like employee availability, skills, rank, and specific job requirements.

---

## ✨ Core Features

* **🧩 Modular Design:** BeeKeeper is built as a **framework**. Mix and match components to fit your exact needs!
* **🔄 Customizable Rules Engine:** Define your own **Preliminary Rules** (static checks) and **Stateful Rules** (dynamic checks based on current assignments) to ensure allocations meet all criteria.
* **🔌 Flexible Data Integration:**
    * **Input Adapters:** Easily pipe in data about your Entities (workers) and Allocation Requests (tasks) from any source (e.g., CSV files, databases, external APIs like "Busy").
    * **Output Adapters:** Dispatch the allocation results to any destination (e.g., update a webpage, save to a file, send notifications).
* **🧠 Algorithm Agnostic:** Plug in your own custom allocation algorithms or use pre-built ones (coming soon!).
* **🗓️ Inavailability & Exemptions:** Easily manage worker unavailability (vacations, appointments) and exemptions (tasks a worker cannot perform).
* **🥇 Rank System:** Assign ranks to workers and specify allowed ranks for tasks.
* **📍 Location Aware:** (Conceptual) Define locations for tasks and entities if needed.
* **⏱️ Date & Time Handling:** Clear `DateRange` objects for defining task durations and unavailability periods.

---

## ⚙️ How It Works: The BeeKeeper Flow

BeeKeeper processes allocations in a clear, staged pipeline:

1.  **📥 Data Ingestion:**
    * `InputAdapter` (e.g., `MixedInputAdapter`) fetches `Entity` data (workers, their ranks, unavailability) and `AllocationRequest` data (tasks, required dates, allowed ranks) from your sources.
    * Example: `McWorkerEntityInputAdapter` loads McDonald's worker data.

2.  **🚦 Preliminary Checks & Filtering:**
    * **(Conceptual Stage) `AssignPossibleEntitiesToAllocations`**: Filters entities that *could* potentially do an allocation.
    * `RunPreliminaryRules`: Applies basic, static rules to quickly eliminate incompatible entity-allocation pairs.
        * *e.g., Is the worker's rank appropriate for the task? Does the worker have an exemption preventing this task?*

3.  **🧠 Core Algorithm Execution:**
    * `RunAlgorithmAndDispatchResults`: The chosen `BaseAlgorithm` implementation takes the filtered allocations and entities.
    * It intelligently assigns entities to allocations, respecting all defined `StatefulRule`s.
        * *e.g., Has the worker already worked too many hours this week? Is this shift too close to their last one?*
    * The result is a `State` object containing all `PlannedAllocation`s.

4.  **📤 Results Dispatch:**
    * The final `State` (list of assignments) is passed to your configured `OutputAdapter`(s).
    * This could mean updating a database, writing to a UI, generating a report, etc.

The entire process is orchestrated by the `BeeKeeper` main class.

---

## 🚀 Getting Started

### Installation

TODO: We should upload to PyPI once we have a working release :)
```bash
pip install beekeeper
```

For now, you might install directly from GitHub:
```bash
git clone [https://github.com/Xiddoc/beekeeper.git](https://github.com/Xiddoc/beekeeper.git)
cd beekeeper
pip install uv # If you don't already have uv
uv sync
```

### Quick Usage Example

Here's a conceptual overview of how you might set up and run BeeKeeper:

```python
from beekeeper import BeeKeeper, MixedInputAdapter
from your_project.your_entity_adapter import YourEntityAdapter
from your_project.your_allocation_adapter import YourAllocationAdapter
from your_project.your_custom_algorithm import YourCustomAlgorithm
from your_project.your_rules import YourCustomRuleSet
from your_project.your_output_adapter import YourOutputAdapter

# TODO: Improve this example once we have a more concrete API

def main() -> None:
    # 1. Setup Input Adapters
    entity_adapter = YourEntityAdapter()
    allocation_adapter = YourAllocationAdapter() # You'll need to create this
    input_adapter = MixedInputAdapter(
        entity_adapter=entity_adapter,
        allocation_adapter=allocation_adapter # Or provide None if no allocations initially
    )

    # 2. Choose/Create an Algorithm
    my_algorithm = YourCustomAlgorithm()

    # 3. Define Your Rules
    my_rules = YourCustomRuleSet() # This would be a list of rule instances

    # 4. Setup Output Adapter(s)
    my_output_adapters = [YourOutputAdapter()]

    # 5. Initialize BeeKeeper
    beekeeper_instance = BeeKeeper(
        algorithm=my_algorithm,
        rules=my_rules,
        input_adapter=input_adapter,
        output_adapters=my_output_adapters,
    )

    # 6. Buzz along and execute! 🐝
    beekeeper_instance.execute()

if __name__ == "__main__":
    main()
```

---

## 🍔 Included Example: McDonald's Workers

The project includes a simple example in `examples.mcdonalds`:

* **`McWorker`**: A custom `Entity` representing a McDonald's worker.
* **`McJobPositions`**: A `Rank` enum for positions like `CASHIER`, `COOK`, `MANAGER`.
* **`McWorkerEntityInputAdapter`**: An example `EntityInputAdapter` that provides a predefined list of `McWorker` entities with names, ranks, and some example `Inavailability` periods.

This example helps illustrate how to define your own entities and input sources.

---

## 🔧 Customization: Make BeeKeeper Your Own!

BeeKeeper's strength lies in its adaptability. You can customize:

* **Entities (`Entity`):**
    * Define your own worker types by subclassing `Entity`.
    * Add custom attributes relevant to your domain.
    * Specify `Rank`, `Location`, and `Exemption` enums tailored to your needs.
    * Example: `McWorker`, `McJobPositions`.

* **Allocations (`AllocationRequest`):**
    * Define types of tasks/shifts using `AllocationType`.
    * Specify requirements like `allowed_ranks`, `prohibited_exemptions`, `date_range`, and `location`.

* **Input/Output Adapters (`EntityInputAdapter`, `AllocationInputAdapter`, `OutputAdapter`):**
    * Implement `get_entities()` and `get_allocations()` in your input adapters to load data from anywhere.
    * Implement `handle_output()` in your output adapter to send results wherever they need to go.
    * Use `MixedInputAdapter` to combine separate entity and allocation sources easily.

* **Rules (`PreliminaryRule`, `StatefulRule`):**
    * Create `PreliminaryRule` subclasses to implement `is_compatible(entity, allocation)` for static checks.
    * Create `StatefulRule` subclasses to implement `is_compatible(entity, allocation, state)` for dynamic, context-aware checks.

* **Algorithms (`BaseAlgorithm`):**
    * Subclass `BaseAlgorithm` and implement the `run()` method with your unique allocation logic. This is where the core matching happens!

---

## 🏗️ Project Structure Highlights

* **`beekeeper/`**: Core library code.
    * `beekeeper.py`: Main `BeeKeeper` class orchestrating the flow.
    * `adapters/`: For input and output data handling.
        * `inputs/`: `EntityInputAdapter`, `AllocationInputAdapter`, `MixedInputAdapter`.
        * `outputs/`: `OutputAdapter`.
    * `allocations/`: `AllocationRequest`, `PlannedAllocation`, `AllocationType`.
    * `entities/`: `Entity`, `Rank`, `Location`, `Exemption`.
    * `algorithm/`: `BaseAlgorithm`, `State` (represents current assignments).
    * `rules/`: `BaseRule`, `PreliminaryRule`, `StatefulRule`.
    * `flow/`: Stages of the BeeKeeper execution process (`AssignPossibleEntitiesToAllocations`, `RunPreliminaryRules`, etc.).
    * `inavailabilities/`: `Inavailability` class.
    * `time_constructs/`: `DateRange`.
* **`examples/`**: Practical examples of how to use BeeKeeper.
    * `mcdonalds/`: A concrete example with `McWorker` entities.

---

## 🤝 Contributing

Contributions are welcome! Whether it's bug fixes, new features, or documentation improvements, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Write tests for your changes.
5.  Ensure all tests pass.
6.  Submit a pull request.

Please adhere to the project's coding standards and provide a clear description of your changes. 😊

---

## 📜 License

This project is licensed under the **[PRIVATE FOR NOW - TBD]** License - see the `LICENSE` file for details.

---

Happy Allocating! 🐝
