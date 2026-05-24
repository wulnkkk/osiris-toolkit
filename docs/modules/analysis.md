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
| `stats.py` | Generic operations: `describe()`, `mean()`, `std()`, `minmax()`, `rms()`, `total_energy()`, `lineout()` |
| `emf.py` | `EMFAnalyzer`: field energy, total EM energy (E²+B²), FFT spectrum, Poynting vector |
| `species.py` | `SpeciesAnalyzer`: density profiles, total charge, energy histograms, temperature tensor |
| `__init__.py` | `Analyzer` unified entry with `.emf`, `.species`, `.stats` accessors |

## Usage

```python
from osiris_toolkit.sim import Simulation
from osiris_toolkit.analysis import Analyzer

sim = Simulation("/path/to/output")
ana = Analyzer(sim)

# EMF analysis
energies = ana.emf.total_em_energy(iteration=50)
# {'e_energy': 1.23e6, 'b_energy': 4.56e5, 'em_energy': 1.69e6}

kx, ky, spectrum = ana.emf.spectrum("e1", iteration=50)

# Species analysis
x, profile = ana.species.density_profile("electrons", "charge", iteration=50)
total_q = ana.species.total_charge("electrons", iteration=50)
temp = ana.species.temperature("electrons", iteration=50)  # {'T11': ..., 'T22': ..., 'T33': ...}

# Statistics
from osiris_toolkit.analysis import describe
grid = sim.get_field("e1", iteration=50)
print(describe(grid))
# {'shape': [512, 512], 'mean': 0.0123, 'std': 0.456, 'min': -1.23, 'max': 1.45, 'rms': 0.456}
```

## Extending

Add a new `*Analyzer` class for a diagnostic type, then add a property to `Analyzer`:

```python
class Analyzer:
    @property
    def tracks(self) -> TrackAnalyzer:
        return TrackAnalyzer(self._sim, self._converter)
```
