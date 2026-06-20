---
audience: [agent]
role: user
topic: agent
kind: recipe
updated: 2026-06-20
---

# Recipe: Batch Process K-Space

Generate k-space plots for all fields and iterations in a simulation.

## Option A: CLI Batch (recommended for full-sim processing)

The `vis batch` command generates field, k-space, and density plots in one pass:

```bash
# Preview first
osiris-toolkit vis batch /data/Au Au --dry-run

# Execute with parallel workers
osiris-toolkit vis batch /data/Au Au -j 8 --progress
```

Output goes to `{sim_path}/figures/Au/` by default (or specify `-o /custom/output`). The `figures/Au/` directory will contain subdirectories for each diagnostic kind.

## Option B: CLI Single K-Space Plot

For one specific frame:

```bash
osiris-toolkit vis plot /data/Au \
  -k KSPACE \
  -q e1 \
  -i 50 \
  --k-unit k0 \
  --clim -4,2 \
  --log-scale \
  -o /output/e1_iter50_kspace.png
```

Available `--k-unit` options: `k0`, `rad/um`, `rad/nm`, `um^-1`, `norm`.

If the simulation input deck is not available, you can override the laser frequency (needed for k0 conversion):

```bash
osiris-toolkit vis plot /data/Au -k KSPACE -q e1 -i 50 \
  --k-unit k0 --omega0-norm 10.0
```

## Option C: Python API (full control)

For programmatic batch k-space processing with custom parameters:

```python
from pathlib import Path
from osiris_toolkit.sim import Simulation
from osiris_toolkit.units.converter import UnitSystem
from osiris_toolkit.vis.kspace import plot_k_space
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)  # None if no deck found

for quantity in sim.list_fields():
    for iteration in sim.list_iterations(quantity):
        output = Path(f"/output/kspace/{quantity}_iter{iteration:04d}.png")
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            plot_k_space(
                sim=sim,
                system=system,
                quantity=quantity,
                iteration=iteration,
                k_unit="k0",
                log_scale=True,
                clim=(-4, 2),
                output=str(output),
                show=False,
            )
            print(f"  OK: {output.name}")
        except Exception as e:
            print(f"  FAIL: {quantity} iter={iteration}: {e}")
```

## Option D: PostProcessor API (simplest Python)

```python
from osiris_toolkit.postproc import PostProcessor
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.common import get_system

sim = Simulation("/data/Au")
system = get_system(sim)
pp = PostProcessor(sim, system=system)

# Batch all diagnostics (fields + k-space + density + scattering)
pp.batch(sim_name="Au_batch", x_unit="um", time_unit="ps", max_workers=8)
```

## Tuning K-Space Plots

Common parameter adjustments via Python API:

```python
plot_k_space(
    sim=sim, system=system,
    quantity="e1", iteration=50,
    k_unit="k0",                # "k0", "rad/um", "rad/nm", "um^-1", "norm"
    log_scale=True,             # Log-scale the FFT magnitude
    clim=(-4, 2),               # Color range in log10 units
    white_low=0.05,             # Fraction of colormap low-end faded to white
    xlim=(-10, 10),             # K-space x-axis range (in k_unit)
    ylim=(-10, 10),             # K-space y-axis range (in k_unit)
    cmap="RdBu_r",              # Matplotlib colormap
    output="out.png",           # Save path
    show=False,                 # Set False for headless batch
)
```

## Pre-conditions

- Simulation output in ZDF format (not HDF5)
- Fields are 2-D (1-D data has no k-space)
- Input deck available (or use `--omega0-norm` CLI flag) for physical k-units

## Verification

- Check that all requested iterations produced non-zero PNG files
- Open a few samples to verify the color scale looks reasonable (not all white or saturated)
- For batch: count files `find /output/kspace -name "*.png" | wc -l` matches expected count (`n_fields * n_iterations`)
