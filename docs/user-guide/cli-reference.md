---
audience: [human, agent]
role: user
topic: cli
kind: reference
tasks: ["parse deck", "lint deck", "estimate resources", "browse sim", "plot data", "batch process", "run workflow", "sync definitions"]
api: ["main", "deck", "sim", "vis", "analyze", "run", "sync"]
cli: ["deck parse", "deck lint", "deck validate", "deck estimate", "sim info", "sim list", "vis plot", "vis batch", "analyze describe", "run", "sync extract"]
updated: 2026-06-04
---

# CLI Reference

Complete command-line interface reference for `osiris-toolkit`.

## Global options

| Option | Description |
|---|---|
| `--version` | Show version and exit |
| `--verbose`, `-v` | Enable DEBUG-level logging |
| `--quiet`, `-q` | Suppress non-error output (ERROR level) |

## Command groups

| Group | Description |
|---|---|
| `deck` | Parse and validate OSIRIS input decks |
| `sim` | Explore simulation output directories |
| `vis` | Visualize simulation data |
| `analyze` | Analyze simulation data |
| `run` | Run a workflow from YAML configuration |
| `sync` | Synchronize definitions from OSIRIS Fortran source |

---

## `deck parse`

Parse an OSIRIS input deck and print the result.

```
osiris-toolkit deck parse [OPTIONS] FILE
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `FILE` | PATH | *(required)* | Path to the input deck file |
| `--output`, `-o` | `json`\|`python` | `json` | Output format |

**Example:**

```bash
osiris-toolkit deck parse input/simulation.in
osiris-toolkit deck parse input/simulation.in --output python
```

---

## `deck lint`

Validate an input deck and print all issues.

```
osiris-toolkit deck lint [OPTIONS] FILE
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `FILE` | PATH | *(required)* | Path to the input deck file |

**Output:** Each issue printed with severity, rule ID, message, section, and line.
Summary printed at the end.

**Example:**

```bash
osiris-toolkit deck lint input/simulation.in
```

---

## `deck validate`

Validate an input deck; exit with non-zero status if errors are found.

```
osiris-toolkit deck validate [OPTIONS] FILE
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `FILE` | PATH | *(required)* | Path to the input deck file |

**Exit codes:** 0 = valid, 1 = errors found.

**Example:**

```bash
osiris-toolkit deck validate input/simulation.in && echo "Valid"
```

---

## `deck estimate`

Estimate computational resources for a simulation input deck.

```
osiris-toolkit deck estimate [OPTIONS] FILE
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `FILE` | PATH | *(required)* | Path to the input deck file |
| `--cores-per-node`, `-c` | INT | auto | CPU cores per compute node |
| `--efficiency`, `-e` | FLOAT | `0.15` | Sustained FLOP/s fraction of peak |

**Example:**

```bash
osiris-toolkit deck estimate input/simulation.in
osiris-toolkit deck estimate -c 64 -e 0.20 input/simulation.in
```

---

## `sim info`

Print summary information about a simulation output directory.

```
osiris-toolkit sim info [OPTIONS] DIRECTORY
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `DIRECTORY` | PATH | *(required)* | Path to the simulation output directory |
| `--output`, `-o` | `text`\|`json` | `text` | Output format |

**Output:** Fields with iteration ranges, species, phasespaces, tracks, history,
timings, and output format detection.

**Example:**

```bash
osiris-toolkit sim info /data/Au
osiris-toolkit sim info /data/Au --output json
```

---

## `sim list`

List available data for a specific diagnostic kind.

```
osiris-toolkit sim list [OPTIONS] DIRECTORY
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `DIRECTORY` | PATH | *(required)* | Path to the simulation output directory |
| `--kind`, `-k` | STR | `EMF` | Diagnostic kind: `EMF`, `DENSITY`, `PHASESPACE`, `TRACKS`, `HISTORY` |

**Example:**

```bash
osiris-toolkit sim list /data/Au --kind EMF
osiris-toolkit sim list /data/Au --kind PHASESPACE
```

---

## `vis plot`

Plot a single diagnostic frame.

```
osiris-toolkit vis plot [OPTIONS] DIRECTORY
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `DIRECTORY` | PATH | *(required)* | Path to the simulation output directory |
| `--kind`, `-k` | STR | `EMF` | Diagnostic kind: `EMF`, `KSPACE`, `DENSITY`, `PHASESPACE` |
| `--quantity`, `-q` | STR | `e1` | Quantity name |
| `--iteration`, `-i` | INT | `0` | Iteration number |
| `--output`, `-o` | PATH | auto | Output file path |
| `--overwrite` | FLAG | off | Overwrite existing output files |
| `--k-unit` | `k0`\|`rad/um`\|`rad/nm`\|`um^-1`\|`norm` | `k0` | Wavenumber unit (KSPACE only) |
| `--omega0-norm` | FLOAT | auto | Laser freq in normalized units |
| `--xlim` | STR | auto | k-space x-axis range: `"min,max"` |
| `--ylim` | STR | auto | k-space y-axis range: `"min,max"` |
| `--clim` | STR | auto | Color range: `"vmin,vmax"` |
| `--white-low` | FLOAT | `0.05` | Fraction of colormap low end faded to white |
| `--log-scale` / `--no-log-scale` | FLAG | on | Log-scale the FFT amplitude (KSPACE) |

**Example:**

```bash
# Field plot
osiris-toolkit vis plot /data/Au --kind EMF --quantity e1 -i 100 -o e1.png

# k-space with custom limits
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --k-unit rad/um --xlim -5,5 --ylim -5,5 --clim 0,10

# k-space with custom omega0
osiris-toolkit vis plot /data/Au --kind KSPACE --quantity e1 -i 100 \
    --omega0-norm 20.0
```

---

## `vis batch`

Batch-process one or more simulations.

```
osiris-toolkit vis batch [OPTIONS] SIMS...
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `SIMS` | STR... | *(required)* | Pairs of `SIM_PATH SIM_NAME` (e.g. `/data/Au Au`) |
| `--output-dir`, `-o` | PATH | sim's figures dir | Root directory for all output |
| `--max-workers`, `-j` | INT | auto | Number of parallel workers |
| `--dry-run` | FLAG | off | Preview what would be generated |
| `--progress` | FLAG | off | Show tqdm progress bar |

**Example:**

```bash
# Preview
osiris-toolkit vis batch --dry-run /data/Au Au

# Process with progress
osiris-toolkit vis batch --progress /data/Au Au

# Parallel
osiris-toolkit vis batch -j 8 --progress /data/Au Au

# Custom output dir, multiple simulations
osiris-toolkit vis batch -o /results/figures --progress /data/Au Au /data/Au0 Au0
```

---

## `analyze describe`

Print descriptive statistics for a diagnostic quantity.

```
osiris-toolkit analyze describe [OPTIONS] DIRECTORY
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `DIRECTORY` | PATH | *(required)* | Path to the simulation output directory |
| `--quantity`, `-q` | STR | `e1` | Quantity name |
| `--iteration`, `-i` | INT | `0` | Iteration number |

**Example:**

```bash
osiris-toolkit analyze describe /data/Au --quantity e2 --iteration 100
```

---

## `run`

Run a workflow from a YAML configuration file.

```
osiris-toolkit run [OPTIONS] WORKFLOW_FILE
```

| Argument/Option | Type | Default | Description |
|---|---|---|---|
| `WORKFLOW_FILE` | PATH | *(required)* | Path to the YAML workflow configuration |

**Example:**

```bash
osiris-toolkit run workflow.yaml
```

---

## `sync extract`

Extract parameter and quantity definitions from OSIRIS Fortran source code.

```
osiris-toolkit sync extract [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--osiris-path` | PATH | *(required)* | Path to OSIRIS Fortran source tree |
| `--docs-path` | PATH | `None` | Path to osiris/docs/reference/ for parameter descriptions |

**Output:** Writes to `src/osiris_toolkit/_generated/`:
- `parameters.py` -- Namelist parameter definitions
- `quantities.py` -- Diagnostic quantity definitions
- `sections.py` -- Input deck section definitions

**Example:**

```bash
osiris-toolkit sync extract --osiris-path /path/to/osiris-source --docs-path /path/to/osiris/docs/reference
```

---

## Environment variables

| Variable | Used by | Description |
|---|---|---|
| `SLURM_CPUS_PER_TASK` | parallel workers | Default worker count in SLURM |
| `OMP_NUM_THREADS` | parallel workers, BLAS | Fallback worker count; thread limit |
| `SLURM_ARRAY_TASK_ID` | job array | Current task index |
| `SLURM_ARRAY_TASK_COUNT` | job array | Total task count |
| `PBS_ARRAYID` | job array (PBS) | Current task index |
| `PBS_ARRAY_INDEX` | job array (PBS) | Total task count |
| `MKL_NUM_THREADS` | BLAS limiting | Intel MKL thread count |
| `OPENBLAS_NUM_THREADS` | BLAS limiting | OpenBLAS thread count |
| `NUMEXPR_NUM_THREADS` | BLAS limiting | NumExpr thread count |
