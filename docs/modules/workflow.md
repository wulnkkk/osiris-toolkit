---
audience: [human, agent]
role: developer
topic: modules
kind: reference
module: workflow
updated: 2026-06-04
---

# workflow — Pipeline Orchestration

Lightweight pipeline framework for automated "deck → simulate → analyze → visualize" workflows.
Configurable via YAML or programmatic construction.

## Architecture

```
Pipeline(steps)
    └── run(ctx) → ctx
            │
            ├── DeckParseStep       parse_deck_file() → ctx.deck
            ├── DeckValidateStep     lint_deck_file()  → raises on error
            ├── SimLoadStep          Simulation(path)  → ctx.sim
            ├── AnalyzeStep          PostAnalysisHub(sim, system) → ctx.extra["analysis_results"]
            └── VisualizeStep        PostVisHub(sim, system) → ctx.extra["figures_dir"]
```

**Files:**

| File | Role |
|------|------|
| `pipeline.py` | `Pipeline`, `PipelineContext`, `PipelineStep` (ABC), 5 predefined steps, YAML parser |
| `__init__.py` | Re-exports + `quick_pipeline()` convenience |

## Usage

### YAML

```yaml
# workflow.yaml
pipeline:
  - deck_parse:
      path: "./input/simulation.in"
  - deck_validate:
  - sim_load:
      path: "./output/"
  - analyze:
      quantities: ["e1", "charge"]
  - visualize:
      kinds: ["EMF", "DENSITY"]
      iteration: 100
      output_dir: "./figures/"
```

```bash
osiris-toolkit run workflow.yaml
```

### Python

```python
from osiris_toolkit.workflow import Pipeline, DeckParseStep, SimLoadStep

pipe = Pipeline([
    DeckParseStep("simulation.in"),
    SimLoadStep("/path/to/output"),
])
ctx = pipe.run()
print(ctx.params.omega_p0)
print(ctx.sim.list_fields())
```

## Key Design Decisions

- **Context as state bus**: `PipelineContext` is a dataclass passed between steps. Steps read from
  and write to it. No global state.
- **Fail-fast**: `DeckValidateStep` raises `PipelineError` on validation failure, halting the pipeline.
- **Current scope**: skeleton only. `AnalyzeStep` and `VisualizeStep` have minimal implementations.
  The framework is designed to grow with the project.

## Pipeline Snapshots (v0.13.0)

`PipelineContext` supports save/load for interrupt-resume workflows:

```python
from osiris_toolkit.workflow import PipelineContext

ctx = PipelineContext(deck_path=Path("input.in"), sim_path=Path("output/"))
ctx = pipe.run(ctx)

# Save a checkpoint
ctx.save_snapshot("checkpoint.json")

# ... interrupt, restart process ...

# Resume from checkpoint — rebuilds deck and sim from paths
ctx2 = PipelineContext.load_snapshot("checkpoint.json")
pipe.run(ctx2)  # continue from where you left off
```

Only non-runtime state is serialized (paths, dry_run, extra). Heavy objects
(`deck`, `sim`, `converter`) are rebuilt from paths on load.
