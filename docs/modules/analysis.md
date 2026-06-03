# analysis — Data Analysis

Physics-domain computations on diagnostic data containers. Operates on `GridData`, `ParticleData`,
etc. without knowledge of file formats.

## Architecture

```
Analyzer(sim, converter)
    ├── .emf       → EMFAnalyzer
    ├── .species   → SpeciesAnalyzer
    ├── .stats     → stats functions (module-level)
    └── .describe() / .mean() / .rms() ...   (delegated statics)
```

**Files:**

| File | Role |
|------|------|
| `_protocol.py` | `DiagnosticAnalyzer` ABC for all analyzer types |
| `_result_types.py` | Result dataclasses (`FieldEnergyResult`, `ParticleSpectrumResult`, `MomentumStatsResult`, etc.) |
| `stats.py` | Generic operations: `describe()`, `mean()`, `std()`, `minmax()`, `rms()`, `total_energy()`, `lineout()` |
| `emf.py` | `EMFAnalyzer`: field energy, total EM energy (E²+B²), FFT spectrum, Poynting vector |
| `density.py` | `DensityAnalyzer`: density profiles, total charge integrals |
| `species.py` | `SpeciesAnalyzer`: energy spectra, temperature tensor, momentum stats (v0.9.0) |
| `tracks.py` | `TracksAnalyzer`: track energy evolution, field-along-track extraction (v0.9.0) |
| `phasespace.py` | `PhasespaceAnalyzer`: list available phase-spaces |
| `kspace.py` | `KSpaceAnalyzer`: k-space FFT spectrum analysis |
| `scattering.py` | `ScatteringAnalyzer`: scattering fraction analysis |
| `__init__.py` | `PostAnalysisHub` unified entry with `.emf`, `.density`, `.species`, `.tracks`, `.phasespace`, `.kspace`, `.scattering` |

## Usage

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.postproc import PostProcessor

sim = Simulation("/path/to/output")
pp = PostProcessor(sim)

# EMF analysis
energies = pp.analyze.emf.field_energy("e1", iteration=50)
spectrum = pp.analyze.emf.fft_spectrum("e1", iteration=50)

# Species analysis
profile = pp.analyze.density.profile("electrons", "charge", iteration=50)
total_q = pp.analyze.density.total("electrons", "charge", iteration=50)
temp = pp.analyze.species.temperature("electrons", iteration=50)

# Momentum stats (v0.9.0)
mom = pp.analyze.species.momentum_stats("electrons", iteration=50)
# → MomentumStatsResult(p1_mean, p1_std, p2_mean, p2_std, anisotropy, nparts)

# Track analysis (v0.9.0)
ene = pp.analyze.tracks.energy_evolution("track_electrons")  # list[np.ndarray]
field = pp.analyze.tracks.field_along("track_electrons", "E1")

# Statistics
from osiris_toolkit.analysis import describe
grid = sim.get_field("e1", iteration=50)
print(describe(grid))
# {'shape': [512, 512], 'mean': 0.0123, 'std': 0.456, 'min': -1.23, 'max': 1.45, 'rms': 0.456}
```

## Extending

Add a new `*Analyzer` class extending `DiagnosticAnalyzer`, then add a `cached_property` to `PostAnalysisHub`:

```python
from ._protocol import DiagnosticAnalyzer

class MyAnalyzer(DiagnosticAnalyzer):
    diagnostic_kind = "MY_KIND"

    def list_available(self) -> list[str]:
        return self._sim.list_whatever()

# In __init__.py PostAnalysisHub:
@cached_property
def my_kind(self) -> MyAnalyzer:
    return MyAnalyzer(self._sim, self._converter)
```

## Backward Compatibility

`Analyzer` is deprecated since v0.6.0. Use `PostProcessor` from `osiris_toolkit.postproc`:

```python
# Deprecated
from osiris_toolkit.analysis import Analyzer
ana = Analyzer(sim)

# Recommended
from osiris_toolkit.postproc import PostProcessor
pp = PostProcessor(sim)
```
