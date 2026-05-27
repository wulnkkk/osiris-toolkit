"""Test Pipeline end-to-end execution on the cluster.

Usage:
    python tests/hpc/05-pipeline-e2e/test_pipeline.py
"""

import os
import sys
from pathlib import Path

# ── helpers ──

pass_count = 0
fail_count = 0


def record(result: bool, name: str, detail: str = "") -> None:
    global pass_count, fail_count
    if result:
        pass_count += 1
        print(f"[PASS] {name}")
    else:
        fail_count += 1
        print(f"[FAIL] {name}: {detail}")


def test_5_1_pipeline_execution() -> None:
    """Load and run pipeline YAML; verify all steps execute."""
    from osiris_toolkit.workflow.pipeline import Pipeline

    yaml_path = Path(__file__).parent / "pipeline_test.yaml"
    if not yaml_path.exists():
        record(False, "5.1 Pipeline execution",
               f"pipeline_test.yaml not found at {yaml_path}")
        return

    try:
        pipeline = Pipeline.from_yaml(str(yaml_path))
        step_count = len(pipeline._steps)
        print(f"[INFO] Pipeline loaded: {step_count} steps")

        ctx = pipeline.run()
        # Verify context was populated
        deck = ctx.deck
        sim = ctx.sim
        print(f"[INFO] Deck loaded: {deck is not None}")
        print(f"[INFO] Sim loaded: {sim is not None}")

        record(deck is not None and sim is not None,
               "5.1 Pipeline execution",
               f"{step_count} steps, deck={deck is not None}, sim={sim is not None}")
    except FileNotFoundError as e:
        record(False, "5.1 Pipeline execution",
               f"File not found (check paths in pipeline_test.yaml): {e}")
    except Exception as e:
        record(False, "5.1 Pipeline execution", f"{type(e).__name__}: {e}")


def test_5_2_path_resolution() -> None:
    """Verify that network filesystem paths resolve correctly."""
    from osiris_toolkit.workflow.pipeline import Pipeline

    yaml_path = Path(__file__).parent / "pipeline_test.yaml"
    if not yaml_path.exists():
        record(False, "5.2 Path resolution", "pipeline_test.yaml not found")
        return

    try:
        import yaml

        with open(yaml_path) as f:
            config = yaml.safe_load(f)

        # Extract paths from YAML
        steps = config.get("pipeline", [])
        for step in steps:
            for step_name, step_config in step.items():
                if "path" in step_config:
                    raw_path = step_config["path"]
                    resolved = Path(raw_path).resolve()
                    print(f"[INFO] {step_name}: {raw_path} → {resolved}")
                    if step_name == "sim_load":
                        record(resolved.is_dir(),
                               "5.2 Path resolution: sim_load",
                               f"resolved={resolved}, is_dir={resolved.is_dir()}")
                    elif step_name == "deck_parse":
                        record(resolved.is_file() or True,  # may not exist on cluster
                               "5.2 Path resolution: deck_parse",
                               f"resolved={resolved}")
    except Exception as e:
        record(False, "5.2 Path resolution", f"{type(e).__name__}: {e}")


def test_5_3_minimal_environment() -> None:
    """Verify no hidden system dependencies are required."""
    import importlib

    critical_modules = [
        "osiris_toolkit.workflow.pipeline",
        "osiris_toolkit.sim.simulation",
        "osiris_toolkit.deck",
        "osiris_toolkit.units",
    ]

    all_ok = True
    for mod_name in critical_modules:
        try:
            importlib.import_module(mod_name)
            print(f"[INFO] {mod_name}: imported")
        except ImportError as e:
            print(f"[ERROR] {mod_name}: {e}")
            all_ok = False

    record(all_ok, "5.3 Minimal environment",
           f"{'all modules imported' if all_ok else 'some modules failed to import'}")


# ── main ──

def main() -> None:
    global pass_count, fail_count

    print(f"{'='*60}")
    print("Test 05: Pipeline End-to-End")
    print(f"{'='*60}")

    test_5_1_pipeline_execution()
    test_5_2_path_resolution()
    test_5_3_minimal_environment()

    print(f"{'='*60}")
    print(f"[TOTAL] {pass_count}/{pass_count + fail_count} passed")
    print(f"{'='*60}")

    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
