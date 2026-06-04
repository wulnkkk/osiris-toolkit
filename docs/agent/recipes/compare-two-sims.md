---
audience: [agent]
topic: agent
kind: recipe
updated: 2026-06-04
---

# Recipe: Compare Two Simulations

Load two simulations and generate side-by-side comparison plots.

## Step 1: Load both simulations

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.common import get_system

sim_a = Simulation("/data/run_A")
sim_b = Simulation("/data/run_B")

system_a = get_system(sim_a)
system_b = get_system(sim_b)

print(f"Run A: {sim_a.list_fields()}")
print(f"Run B: {sim_b.list_fields()}")
```

## Step 2: Verify compatibility

Check that both simulations have the diagnostics you want to compare:

```python
# Find common fields
common_fields = set(sim_a.list_fields()) & set(sim_b.list_fields())
print(f"Common fields: {common_fields}")

# Find the closest matching iteration if they differ
iter_a = 50
iter_b = 50  # May need to find nearest if not exact match

# Check grid shapes match (difference/overlay require same shape)
grid_a = sim_a.get_field("e1", iter_a)
grid_b = sim_b.get_field("e1", iter_b)
print(f"Shape A: {grid_a.data.shape}, Shape B: {grid_b.data.shape}")
```

## Step 3: Side-by-side field comparison

```python
import matplotlib.pyplot as plt
from osiris_toolkit.vis.field import plot_field

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Use plot_field on each axis (pass ax= parameter if supported)
# Or construct manually:
import matplotlib.pyplot as plt
import numpy as np

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

grid_a = sim_a.get_field("e1", 50)
grid_b = sim_b.get_field("e1", 50)

vmax = max(np.abs(grid_a.data).max(), np.abs(grid_b.data).max())
vmin = -vmax

im1 = ax1.imshow(grid_a.data.T, origin="lower", cmap="RdBu_r",
                 vmin=vmin, vmax=vmax, aspect="auto")
ax1.set_title("Run A: e1 @ iter 50")

im2 = ax2.imshow(grid_b.data.T, origin="lower", cmap="RdBu_r",
                 vmin=vmin, vmax=vmax, aspect="auto")
ax2.set_title("Run B: e1 @ iter 50")

fig.colorbar(im2, ax=[ax1, ax2], label="e1 [normalized]")
fig.savefig("comparison_e1_iter50.png", dpi=150, bbox_inches="tight")
```

## Step 4: Difference plot

```python
from osiris_toolkit.vis.comparison import plot_difference

# plot_difference expects two GridData objects
grid_a = sim_a.get_field("e1", 50)
grid_b = sim_b.get_field("e1", 50)

plot_difference(
    grid_a, grid_b,
    label_a="Run A",
    label_b="Run B",
    system=system_a,  # Use either system for axis labeling
    output="diff_e1_iter50.png",
)
```

## Step 5: Overlay plot

```python
from osiris_toolkit.vis.comparison import plot_overlay

grid_a = sim_a.get_field("e1", 50)
grid_b = sim_b.get_field("e1", 50)

plot_overlay(
    grid_a, grid_b,
    label_a="Run A",
    label_b="Run B",
    system=system_a,
    output="overlay_e1_iter50.png",
)
```

## Step 6: K-space comparison

```python
from osiris_toolkit.vis.kspace import plot_k_space

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Plot each sim's k-space (manually — plot_k_space creates its own figure)
# Alternative: use compute_k_space and plot manually
from osiris_toolkit.compute.fft import compute_k_space

grid_a = sim_a.get_field("e1", 50)
grid_b = sim_b.get_field("e1", 50)

spec_a, kx_a, ky_a = compute_k_space(grid_a)
spec_b, kx_b, ky_b = compute_k_space(grid_b)

spec_a_log = np.log10(np.abs(spec_a) + 1e-30)
spec_b_log = np.log10(np.abs(spec_b) + 1e-30)

vmax = max(spec_a_log.max(), spec_b_log.max())
vmin = vmax - 6

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
im1 = ax1.imshow(spec_a_log.T, origin="lower", cmap="inferno",
                 vmin=vmin, vmax=vmax, aspect="auto")
ax1.set_title("Run A: k-space |e1|")
im2 = ax2.imshow(spec_b_log.T, origin="lower", cmap="inferno",
                 vmin=vmin, vmax=vmax, aspect="auto")
ax2.set_title("Run B: k-space |e1|")
fig.colorbar(im2, ax=[ax1, ax2], label="log10(|FFT|)")
fig.savefig("comparison_kspace_e1_iter50.png", dpi=150, bbox_inches="tight")
```

## Step 7: Energy timeline comparison

```python
from osiris_toolkit.analysis.emf import EMFAnalyzer

analyzer_a = EMFAnalyzer(sim_a, system_a)
analyzer_b = EMFAnalyzer(sim_b, system_b)

# Collect energy over iterations
iterations = sim_a.list_iterations("e1")  # or find common iterations
energy_a = []
energy_b = []
times = []

for it in iterations:
    result_a = analyzer_a.field_energy("e1", iteration=it)
    result_b = analyzer_b.field_energy("e1", iteration=it)
    if result_a and result_b:
        energy_a.append(result_a.total_energy)
        energy_b.append(result_b.total_energy)
        times.append(it)  # or use actual simulation time

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(times, energy_a, "o-", label="Run A")
ax.plot(times, energy_b, "s-", label="Run B")
ax.set_xlabel("Iteration")
ax.set_ylabel("Total field energy [normalized]")
ax.legend()
ax.set_title("Energy Comparison: e1")
fig.savefig("comparison_energy_e1.png", dpi=150, bbox_inches="tight")
```

## Pre-conditions

- Both simulation directories exist and contain ZDF output
- Same diagnostic type and quantity available in both
- Comparable iteration numbers (or find nearest match)
- For difference/overlay: grids must have the same shape

## Verification

- Side-by-side comparison PNG shows both datasets with shared color scale
- Difference plot highlights regions where the two runs diverge
- Energy comparison line plot shows both traces on the same axes
- If grids have different shapes, regrid one to match the other before comparing
