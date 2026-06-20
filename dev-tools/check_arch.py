"""
check_arch.py — Verify osiris-toolkit module dependency hierarchy.

Ensures:
1. No reverse dependencies (compute → sim/vis/analysis/workflow)
2. No deprecated UnitConverter imports
3. Layer boundary compliance (low→base, mid→base|low, high→anything below)

Exit code 0 = all clean, 1 = violations found.
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src" / "osiris_toolkit"

# Layer definitions (ordered bottom to top)
LAYERS: list[tuple[str, set[str], set[str]]] = [
    # (name, directory_names, allowed_upward_targets)
    ("base",      {"exceptions", "_generated", "_models"},             set()),
    ("low",       {"deck", "io", "units", "compute"},                 {"base"}),
    ("mid",       {"sim", "sync", "parallel", "resource"},            {"base", "low"}),
    ("high",      {"analysis", "vis", "workflow"},                    {"base", "low", "mid"}),
]

# Build a module-prefix → layer-name mapping
MODULE_PREFIX: dict[str, str] = {}
for layer_name, dirs, _ in LAYERS:
    for d in dirs:
        MODULE_PREFIX[f"osiris_toolkit.{d}"] = layer_name

# All layer prefixes for reference
ALL_MODULES = set(MODULE_PREFIX.keys())


def module_to_layer(module_name: str) -> str | None:
    """Return the layer name for a given osiris_toolkit module, or None."""
    for prefix in sorted(ALL_MODULES, key=len, reverse=True):
        if module_name == prefix or module_name.startswith(prefix + "."):
            return MODULE_PREFIX[prefix]
    return None


def main() -> int:
    violations: list[str] = []
    py_files = sorted(SRC.rglob("*.py"))

    for py_file in py_files:
        rel = py_file.relative_to(SRC)
        # Determine which layer this file belongs to
        file_layer = None
        for layer_name, dirs, _ in LAYERS:
            if rel.parts[0] in dirs:
                file_layer = layer_name
                break
        if file_layer is None:
            continue  # e.g., cli.py, config.py at top level

        # Determine which layers this file is allowed to import
        allowed_up = None
        for _, dirs, allowed in LAYERS:
            if rel.parts[0] in dirs:
                allowed_up = allowed | {file_layer}  # same layer is always OK
                break
        if allowed_up is None:
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError as e:
            violations.append(f"  {py_file}: syntax error — {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import(alias.name, py_file, rel, file_layer, allowed_up, violations)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    _check_import(node.module, py_file, rel, file_layer, allowed_up, violations)

    if violations:
        print(f"[FAIL] {len(violations)} architecture violation(s) found:\n")
        for v in sorted(violations):
            print(v)
        return 1
    else:
        print("[PASS] Architecture checks passed.")
        return 0


def _check_import(
    module: str,
    py_file: Path,
    rel: Path,
    file_layer: str,
    allowed_up: set[str],
    violations: list[str],
) -> None:
    """Check a single import statement against architecture rules."""
    # Skip non-project imports
    if not module.startswith("osiris_toolkit"):
        return
    # Skip _generated imports (they're the interface layer)
    if "._generated" in module or module.endswith("_generated"):
        return

    target_layer = module_to_layer(module)
    if target_layer is None:
        return

    # 1. Reverse dependency check
    layer_order = ["base", "low", "mid", "high"]
    src_idx = layer_order.index(file_layer)
    tgt_idx = layer_order.index(target_layer)
    if tgt_idx > src_idx:
        violations.append(
            f"  {rel}:{py_file} imports {module} — "
            f"reverse dependency: {file_layer} ← {target_layer}"
        )
        return

    # 2. Layer boundary check
    if target_layer not in allowed_up:
        violations.append(
            f"  {rel}:{py_file} imports {module} — "
            f"not in allowed targets for {file_layer} layer: {sorted(allowed_up)}"
        )

    # 3. Deprecated UnitConverter check
    if "UnitConverter" in module:
        violations.append(
            f"  {rel}:{py_file} imports {module} — "
            f"UnitConverter is deprecated since v0.15.0, use UnitSystem instead."
        )


if __name__ == "__main__":
    sys.exit(main())
