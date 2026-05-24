# deck — Input Deck Parser & Validator

Parses OSIRIS PIC simulation input decks (Fortran-namelist-like curly-brace syntax) into
structured Python dictionaries, and validates them against a comprehensive schema of ~700
parameters across 36 section types with ~46 validation rules.

## Architecture

```
Text → Lexer (tokens) → Parser (AST) → Value Parser (typed dict)
                                            │
                              ┌─────────────┴─────────────┐
                              ▼                           ▼
                       Validator (21 rules)    CrossValidator (25 rules)
                              │                           │
                              └──────────┬────────────────┘
                                         ▼
                                    IssueReport
```

**Files:**

| File | Role |
|------|------|
| `lexer.py` | Custom tokenizer: `!` comments, Fortran `d`-exponents, `.true.`/`.false.`, `(1:3)` slices |
| `ast.py` | `Deck`, `Section`, `ParamAssignment`, `KeySpec`, `SliceSpec` dataclasses |
| `parser.py` | Recursive-descent parser: `section_name { key = value, ... }` |
| `value_parser.py` | Type coercion + array assembly from raw tokens |
| `schemas/parameters.py` | ~700 `ParamSpec` definitions (name, Fortran type, Python type, constraints, defaults, conditions) |
| `schemas/registry.py` | 36 `SectionSpec` entries: canonical order, required/optional/conditional, species-group repeat logic |
| `validator.py` | 21 single-section validation rules (V-REQUIRED, V-ORDER, V-GRID, V-TSTEP, V-SPECIES, etc.) |
| `cross_validator.py` | 25 cross-section rules: count matching, dimensional consistency, physics compatibility |
| `reporter.py` | `IssueReport` / `ValidationIssue` / `Severity(ERROR|WARNING|INFO)` |
| `main.py` | Public API entry point |

## Usage

```python
from osiris_toolkit.deck import parse_deck_file, lint_deck_file, parse_deck_text

# Parse a file
deck = parse_deck_file("simulation.in")
for sec in deck["sections"]:
    print(f"{sec['name']}: {list(sec['params'].keys())}")

# Parse from string
deck = parse_deck_text("simulation { omega_p0 = 3.55e15, }")

# Lint (validate)
report = lint_deck_file("simulation.in")
print(report.summary())
for issue in report.errors():
    print(f"[{issue.rule_id}] {issue.message}")
```

## Key Design Decisions

- **Schema-awareness during parsing**: parameter values are coerced to the correct Python type
  based on the Fortran type declared in `param_schemas`. A bare `-1` assigned to a `real` parameter
  becomes `-1.0`.
- **Slice metadata preserved**: `nx_p(1:2) = 32, 32` produces `{"value":[32,32], "slice":"(1:2)", "dims":[(1,2)]}`,
  not just a flat array.
- **Canonical section ordering**: validated against the Fortran `read_input_sim()` call sequence.
  Ensures the deck is structurally identical to what OSIRIS expects.

## Adding a New Parameter

1. Add a `ParamSpec` in `schemas/parameters.py` in the appropriate section block
2. Run existing tests — the new parameter is automatically recognized by the parser
3. Add validation rules if the parameter has constraints (e.g., `>= 0`)
