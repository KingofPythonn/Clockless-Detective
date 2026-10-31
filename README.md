# The Clockless Detective

**An Original Programming Assignment in Formal Languages and Automata Theory**

The Clockless Detective is a programming project focused on fault diagnosability in finite-state nondeterministic transition systems under partial observation.

The assignment asks whether a fault can be detected after a finite number of observable events, whether the maximum ambiguity period is finite, or whether faulty and fault-free executions can remain observationally indistinguishable for arbitrarily long sequences.

The project combines formal modeling, graph algorithms, cycle analysis, and certificate construction in Python.

## Problem Overview

A system produces observable events while its internal state and certain transitions remain hidden from an observer. In particular, a fault may occur without generating an observable event.

The task is to analyze a given transition system and determine which of the following cases applies:

- **Unreachable:** No faulty execution is reachable from the initial state.
- **Bounded:** The maximum number of observable events after the first fault, while a fault-free execution can produce the same observation, is finite. The program must compute the exact bound.
- **Unbounded:** Faulty and fault-free executions can remain observationally indistinguishable for arbitrarily long sequences.

The program must return not only the classification but also a certificate that can be checked against the input transition system.

## Formal Model

The input describes a finite-state nondeterministic transition system

\[
M=(Q,\Sigma,E,s)
\]

where:

- \(Q\) is the set of states, indexed from \(0\) to \(n-1\).
- \(\Sigma\) is the alphabet of observable events.
- \(E\) is the list of transitions.
- \(s\) is the initial state.

Each transition is represented by a triple:

`[source, label, destination]`

Transition labels have the following meanings:

| Label                  | Meaning             | Observable? |
| ---------------------- | ------------------- | ----------- |
| A symbol in `alphabet` | Observable event    | Yes         |
| `tau`                  | Internal transition | No          |
| `fault`                | Fault occurrence    | No          |

Only observable events contribute to the observer's event sequence. Internal transitions and fault occurrences are invisible.

The ambiguity bound counts observable events occurring after the first fault, while a fault-free execution can still produce the same observation.

## Repository Contents

| File                                           | Description                                           |
| ---------------------------------------------- | ----------------------------------------------------- |
| `Clockless_Detective_Assignment_Academic .pdf` | Formal assignment specification                       |
| `solution.py`                                  | Python reference implementation                       |
| `run_samples.py`                               | Script for executing the sample inputs                |
| `samples.json`                                 | Four sample transition systems                        |
| `README.md`                                    | Project overview and usage instructions               |
| `.gitignore`                                   | Git ignore rules for common local and generated files |

## Requirements

- Python 3.11 or later is recommended.
- Only the Python standard library is required.
- No third-party packages or external services are needed.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/KingofPythonn/Clockless-Detective.git
cd Clockless-Detective
```

### 2. Check your Python installation

```bash
python --version
```

On Windows, you can use `py --version` if the `python` command is unavailable.

### 3. Run the sample cases

```bash
python run_samples.py
```

The runner loads `samples.json`, analyzes each model using the reference implementation, and prints the computed JSON result.

To use a different JSON sample file, provide its path as an argument:

```bash
python run_samples.py path/to/samples.json
```

On Windows, replace the example path with the appropriate Windows path if necessary.

## Input Format

Each model is represented as a JSON object with the following fields:

```json
{
  "n": 3,
  "start": 0,
  "alphabet": ["a", "b"],
  "edges": [
    [0, "a", 0],
    [0, "fault", 1],
    [1, "tau", 1],
    [1, "b", 2]
  ]
}
```

- `n`: Number of states.
- `start`: Initial state identifier.
- `alphabet`: List of observable event symbols.
- `edges`: List of transitions, each represented by its source state, label, and destination state.

State identifiers and transition identifiers are zero-based. A transition identifier is its index in the `edges` array.

## Output Format

The function `analyze(model: dict) -> dict` returns a JSON-compatible result.

### Unreachable fault

```json
{
  "status": "unreachable"
}
```

### Finite ambiguity bound

```json
{
  "status": "bounded",
  "bound": 2,
  "witness": {
    "faulty": [0, 2, 3],
    "healthy": [0, 4]
  }
}
```

The `witness` contains transition identifiers for a faulty execution and a fault-free execution. A valid certificate must satisfy the assignment's path, observation, and bound requirements; the particular identifiers may differ between valid solutions.

### Unbounded ambiguity

```json
{
  "status": "unbounded",
  "prefix": {
    "faulty": [1],
    "healthy": []
  },
  "cycle": {
    "faulty": [2, 3],
    "healthy": [0]
  }
}
```

An unbounded certificate consists of a prefix and a pair of repeatable cycles satisfying the assignment's requirements. Repeating the cycles demonstrates arbitrarily long observational ambiguity.

The examples above illustrate the output structure; certificate paths must be valid for the particular input model.

## Implementation Overview

The reference implementation constructs a verifier-style product graph that tracks a potentially faulty execution alongside a fault-free execution with the same observable trace.

Observable transitions advance both executions synchronously, while invisible transitions can occur independently. The product graph also records whether the first fault has occurred.

The algorithm then analyzes reachable strongly connected components:

- A reachable positive-weight cycle establishes unbounded ambiguity.
- If no such cycle exists, a weighted longest-path computation on the component condensation graph determines the exact finite bound.
- The implementation reconstructs certificates using transition identifiers from the original model.

Under the assignment's stated out-degree constraints, the implementation is designed for \(O((|\Sigma|+1)n^2)\) time and space.

## Reference and Further Reading

T.-S. Yoo and S. Lafortune, “Polynomial-Time Verification of Diagnosability of Partially Observed Discrete-Event Systems,” _IEEE Transactions on Automatic Control_, vol. 47, no. 9, pp. 1491–1495, September 2002.

[https://doi.org/10.1109/TAC.2002.802763](https://doi.org/10.1109/TAC.2002.802763)

This paper provides related theoretical background on diagnosability in partially observed discrete-event systems.

## Notes

- The sample runner computes results from the supplied inputs; it does not compare them against stored expected outputs.
- The repository currently includes a reference implementation as well as the assignment materials.
- No explicit license is currently included. Reuse and redistribution permissions should be clarified before the project is distributed under a particular license.

## Author and Licensing

**Original Assignment Designer:** Sina Abbaszadeh Balanga

Copyright © 2026 Sina Abbaszadeh Balanga.

This repository contains materials distributed under two different licenses:

| Materials                                                     | License                                                    |
| ------------------------------------------------------------- | ---------------------------------------------------------- |
| Python source code (`solution.py`, `run_samples.py`)          | MIT License                                                |
| Original assignment, README, and educational sample materials | Creative Commons Attribution 4.0 International (CC BY 4.0) |

### License Files

- [MIT License — Source Code](LICENSES/MIT.txt)
- [CC BY 4.0 — Assignment and Documentation](LICENSES/CC-BY-4.0.txt)
- [Licensing and Attribution Details](LICENSES/README.md)

Commercial use, modification, and redistribution are permitted under the applicable license terms, subject to the required copyright notices and attribution.

**Original Author:** Sina Abbaszadeh Balanga

Project repository: https://github.com/KingofPythonn/Clockless-Detective
