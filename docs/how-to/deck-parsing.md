---
audience: [human, agent]
role: user
topic: deck
kind: how-to
tasks: ["parse deck", "lint deck", "extract parameters"]
api: ["parse_deck_file", "lint_deck_file", "SimulationParams"]
cli: ["deck parse", "deck lint", "deck validate", "deck estimate"]
updated: 2026-06-04
---

# Deck Parsing

Parse and validate OSIRIS input decks.

## Parse

`parse_deck_file()` reads an OSIRIS input deck and returns a dict with
`sections` -- each section has `name`, `line`, and `params`.

```python
from osiris_toolkit.deck import parse_deck_file

deck = parse_deck_file("input/simulation.in")
for sec in deck["sections"]:
    print(f"Section: {sec['name']} ({len(sec.get('params', {}))} params)")
```

`parse_deck_text()` parses from a string instead of a file path:

```python
from osiris_toolkit.deck import parse_deck_text

text = """
simulation {
    omega_p0 = 3.55e15
    n0 = 0.05
}
"""
deck = parse_deck_text(text)
```

## Extract simulation parameters

`SimulationParams` bridges the parsed deck to the unit system:

```python
from osiris_toolkit.units import SimulationParams

params = SimulationParams.from_deck(deck)
print(params.omega_p0)      # 3.55e15 rad/s
print(params.n0)            # 0.05 (or None)
print(params.omega0_norm)   # 10.0 (laser freq, if available)
```

`omega_p0` is extracted from the `simulation` section. `omega0_norm` is
extracted from antenna / zpulse / laser sections where present.

Alternative constructors:

```python
# Direct omega_p0
params = SimulationParams.from_omega_p0(3.55e15)

# Auto-discover from simulation directory (searches for .in files)
params = SimulationParams.from_sim_path("/data/Au")
```

## Validate (lint)

`lint_deck_file()` runs all validation rules and returns an `IssueReport`:

```python
from osiris_toolkit.deck import lint_deck_file

report = lint_deck_file("input/simulation.in")
print(report.summary())
for issue in report.issues:
    print(f"  [{issue.severity.name}] [{issue.rule_id}] {issue.message}")
    print(f"    section={issue.section}, line={issue.line}")
```

## CLI

```bash
# Parse to JSON (default)
osiris-toolkit deck parse input/simulation.in

# Parse to Python repr
osiris-toolkit deck parse input/simulation.in --output python

# Lint (print all issues)
osiris-toolkit deck lint input/simulation.in

# Validate with exit code (non-zero on errors)
osiris-toolkit deck validate input/simulation.in

# Estimate computational resources
osiris-toolkit deck estimate input/simulation.in
osiris-toolkit deck estimate -c 64 -e 0.20 input/simulation.in
```

## API Reference

| Function | Description |
|---|---|
| `parse_deck_file(path)` | Parse a deck file, return dict with `"sections"` |
| `parse_deck_text(text)` | Parse a deck from a string |
| `lint_deck_file(path)` | Run all validation rules, return `IssueReport` |
| `lint_deck_text(text)` | Lint from a string |
| `IssueReport.summary()` | Human-readable summary of all issues |
| `IssueReport.has_errors()` | True if any ERROR-severity issues exist |
| `IssueReport.errors()` | Iterate only ERROR-severity issues |
| `SimulationParams.from_deck(deck)` | Extract params from a parsed deck dict |
| `SimulationParams.from_omega_p0(val)` | Create from a known omega_p0 value |
| `SimulationParams.from_sim_path(path)` | Auto-discover .in file and extract params |
