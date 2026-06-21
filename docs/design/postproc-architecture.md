---
audience: [human]
role: developer
topic: design
kind: design
updated: 2026-06-04
language: en
---

# Post-Processing Module Architecture Redesign

> 2026-05-28 | Design

## Background

Evaluation identified the following issues in the `analysis/` and `vis/` post-processing modules:

1. **Boundary violations** â€?`vis/kspace.py::compute_k_space()` is a pure numerical FFT computation, and `vis/scattering.py::analyze_scattering()` is a complete analysis workflow; both are misplaced under vis/
2. **Duplicate implementations** â€?`analysis/emf.py::EMFAnalyzer.spectrum()` and `vis/kspace.py::compute_k_space()` both perform 2D FFT
3. **Broken chain** â€?Field energy, spectrum, and Poynting flux computed in the analysis layer have no corresponding plot functions in the vis layer
4. **Dual entry points unaware of each other** â€?`Analyzer` and `VisEngine` are independent, requiring users to understand two separate mental models
5. **Unstandardized extensibility** â€?8 diagnostic types with zero coverage on the backlog have no unified extension pattern

## Design Goals

- Establish a clear three-layer architecture: `compute/` â†?`analysis/` â†?`vis/`
- Single top-level entry point `PostProcessor`
- Analysis results passed via strongly-typed dataclasses, directly consumable by vis
- Define a `DiagnosticAnalyzer` protocol to unify the extension pattern for new diagnostic types
- Maintain backward compatibility; old APIs guide migration via deprecation warnings

## New Directory Structure

```
src/osiris_toolkit/
â”œâ”€â”€ compute/                    # NEW: pure numerical computation layer
â”?  â”œâ”€â”€ __init__.py
â”?  â”œâ”€â”€ fft.py                  # compute_k_space, spectral_power
â”?  â””â”€â”€ integrate.py            # mask_energy, trapz_2d, line_integrate
â”?â”œâ”€â”€ analysis/                   # REFACTORED: physical-semantic analysis layer
â”?  â”œâ”€â”€ __init__.py             # PostAnalysisHub
â”?  â”œâ”€â”€ _protocol.py            # NEW: DiagnosticAnalyzer abstract base class
â”?  â”œâ”€â”€ _result_types.py        # NEW: all analysis result dataclasses
â”?  â”œâ”€â”€ emf.py                  # EMFAnalyzer (simplified, FFTâ†’compute/)
â”?  â”œâ”€â”€ scattering.py           # NEW: analyze_scattering moved from vis/
â”?  â”œâ”€â”€ density.py              # NEW: DensityAnalyzer
â”?  â”œâ”€â”€ species.py              # SpeciesAnalyzer (particle analysis retained)
â”?  â”œâ”€â”€ phasespace.py           # NEW: PhasespaceAnalyzer
â”?  â”œâ”€â”€ kspace.py               # NEW: KSpaceAnalyzer
â”?  â”œâ”€â”€ stats.py                # Retained
â”?  â””â”€â”€ parallel.py             # Retained
â”?â”œâ”€â”€ vis/                        # STREAMLINED: pure plotting layer
â”?  â”œâ”€â”€ __init__.py             # PostVisHub
â”?  â”œâ”€â”€ common.py               # load_sim, get_converter, save_or_show
â”?  â”œâ”€â”€ field.py                # plot_field, plot_all_fields
â”?  â”œâ”€â”€ density.py              # plot_density
â”?  â”œâ”€â”€ phasespace.py           # plot_phasespace
â”?  â”œâ”€â”€ kspace.py               # plot_k_space (removed compute_k_space)
â”?  â”œâ”€â”€ scattering.py           # plot_scattering_fraction (removed analyze_*)
â”?  â”œâ”€â”€ composite.py            # plot_composite
â”?  â”œâ”€â”€ energy.py               # NEW: field energy/spectrum/Poynting plotting
â”?  â”œâ”€â”€ batch.py                # process_simulation
â”?  â””â”€â”€ parallel.py             # batch_process_parallel
â”?â””â”€â”€ postproc.py                 # NEW: top-level PostProcessor
```

## Three-Layer Architecture

### compute/ â€?Pure Numerical Computation Layer

- Input/output are `np.ndarray` or `float`
- **Does NOT import sim/, does NOT import units/, does NOT import matplotlib**
- Pure functions, stateless, callable by both analysis and vis
- Public API: `compute_k_space()`, `spectral_power()`, `mask_energy()`, `trapz_2d()`, `line_integrate()`

### analysis/ â€?Physical-Semantic Analysis Layer

- Depends on `compute/` + `sim/` + `units/`
- One Analyzer class per diagnostic type, implementing the `DiagnosticAnalyzer` protocol
- Analysis methods return strongly-typed dataclasses (defined in `_result_types.py`)
- **Does NOT import matplotlib**
- Submodules: emf, scattering, density, species, phasespace, kspace, stats

### vis/ â€?Plotting/Rendering Layer

- Depends on `analysis/` result types + `sim/` raw data + `compute/` (only for auxiliary purposes such as colormap ranges)
- One plot function or simple Vis facade per diagnostic type
- **Does NOT directly perform FFT, integration, or other numerical computations**
- Results saved to file or displayed

## Data Flow

```
sim/                         compute/               analysis/              vis/
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Simulation.get_field() â”€â”€â–? compute_k_space() â”€â”€â–? EMFAnalyzer â”€â”€â–?EMDynamicsResult
                             mask_energy()             .em_dynamics()   â”?                             trapz_2d()                .field_energy()  â”?                                                        .spectrum()     â–?                                                                  plot_energy_timeline()
                                                                  plot_spectrum()
                                                                  plot_poynting()
```

## Diagnostic Analysis Protocol

```python
class DiagnosticAnalyzer(ABC):
    """Abstract base class for all diagnostic type analyzers."""

    @property
    @abstractmethod
    def diagnostic_kind(self) -> str:
        """The OSIRIS diagnostic type name."""

    @abstractmethod
    def list_available(self) -> list[str]:
        """Return the list of analyzable quantities/species under this diagnostic."""
```

A unified `analyze()` signature is not enforced â€?parameters vary significantly across diagnostic types (field_energy needs quantity+iteration, density_profile needs species+axis). Therefore the protocol only constrains metadata and discovery interfaces.

## Result Types

All analysis methods return explicitly named dataclasses, defined in `analysis/_result_types.py`:

```python
@dataclass
class FieldEnergyResult:
    quantity: str
    iteration: int
    time: float
    total_energy: float
    grid: GridData | None

@dataclass
class EMDynamicsResult:
    iteration: int
    time: float
    e2_total: float
    b2_total: float
    total: float

@dataclass
class EMSpectrumResult:
    quantity: str
    iteration: int
    time: float
    kx_k0: np.ndarray
    ky_k0: np.ndarray
    spectrum: np.ndarray

@dataclass
class ScatteringResult:
    quantity: str
    iterations: list[int]
    times: list[float]
    scattered_fraction: list[float]
    side_scatter_fraction: list[float]
    back_scatter_fraction: list[float]
    mask_info: dict
```

## Top-Level API

```python
from osiris_toolkit import Simulation
from osiris_toolkit.postproc import PostProcessor

sim = Simulation("/path/to/output")
pp = PostProcessor(sim)

# â”€â”€ Analysis â”€â”€
pp.analyze.emf.field_energy("e1", iteration=50)      # â†?FieldEnergyResult
pp.analyze.emf.em_dynamics(iteration=50)              # â†?EMDynamicsResult
pp.analyze.emf.spectrum("e1", iteration=50)           # â†?EMSpectrumResult
pp.analyze.scattering.analyze("e3")                   # â†?ScatteringResult
pp.analyze.density.profile("electrons", iteration=50) # â†?DensityProfileResult
pp.analyze.species.energy_spectrum("electrons", 50)   # â†?ParticleSpectrumResult

# â”€â”€ Visualization â”€â”€
pp.vis.field.plot("e1", iteration=50, x_unit="um")   # reads sim data directly
pp.vis.energy.timeline(emd_result)                     # consumes analysis result
pp.vis.energy.spectrum(spec_result)                    # consumes analysis result
pp.vis.scattering.plot(result)                         # consumes analysis result

# â”€â”€ Batch Processing â”€â”€
pp.batch(sim_name="run_01", x_unit="um")
```

### Internal Structure

```python
class PostProcessor:
    def __init__(self, sim, converter=None):
        self._sim = sim
        self._converter = converter

    @cached_property
    def analyze(self) -> PostAnalysisHub: ...
    
    @cached_property
    def vis(self) -> PostVisHub: ...

class PostAnalysisHub:
    @cached_property
    def emf(self) -> EMFAnalyzer: ...
    @cached_property
    def scattering(self) -> ScatteringAnalyzer: ...
    # ... one cached_property per diagnostic type

class PostVisHub:
    @cached_property
    def field(self) -> FieldVis: ...
    @cached_property
    def energy(self) -> EnergyVis: ...
    # ...
```

All analyzers and vis facades are lazily loaded, initialized only on first access.

## New Diagnostic Type Extension Pattern

For each new diagnostic type added (RAW, TRACKS, HISTORY, UDIST, CELL_AVG, CURRENT, CHARGE_CONS, TIMINGS), follow three steps:

1. **`analysis/<name>.py`** â€?Implement `XxxAnalyzer(DiagnosticAnalyzer)` + result dataclass (add to `_result_types.py`)
2. **`vis/<name>.py`** â€?Plot function(s) accepting analysis result types and/or raw sim data
3. **`postproc.py`** â€?Add one `@cached_property` each to `PostAnalysisHub` and `PostVisHub`

No manual registry required.

### Priority Mapping

| Diagnostic Type | analysis/ | vis/ | Backlog # |
|---------------|-----------|------|-----------|
| RAW | `raw.py` â†?RawAnalyzer | `raw.py` | 23 |
| TRACKS | `tracks.py` â†?TracksAnalyzer | `tracks.py` | 24 |
| HISTORY | `history.py` â†?HistoryAnalyzer | `history.py` | 27 |
| UDIST | `udist.py` â†?UdistAnalyzer | `udist.py` | 28 |
| CELL_AVG | `cell_avg.py` â†?CellAvgAnalyzer | `cell_avg.py` | 29 |
| CURRENT | `current.py` â†?CurrentAnalyzer | `current.py` | 30 |
| CHARGE_CONS | `charge_cons.py` â†?ChargeConsAnalyzer | `charge_cons.py` | 31 |
| TIMINGS | `timings.py` â†?TimingsAnalyzer | `timings.py` | 32 |

## Migration Checklist

| Current Location | Destination | Handling |
|-----------------|-------------|----------|
| `vis/kspace.py::compute_k_space()` | `compute/fft.py` | Move, re-export at old location + deprecation |
| `vis/scattering.py::analyze_scattering()` | `analysis/scattering.py` | Move, re-export at old location + deprecation |
| `vis/scattering.py::ScatteringResult` | `analysis/_result_types.py` | Move, compatible import at old location |
| `vis/scattering.py::_mask_energy()` | `compute/integrate.py` renamed to `mask_energy()` | Move, remove leading underscore |
| `analysis/emf.py::EMFAnalyzer.spectrum()` | Internally call `compute/fft.py` | Eliminate duplication |
| `vis/__init__.py::VisEngine` | Retain, add deprecation warning | Guide to PostProcessor |
| `analysis/__init__.py::Analyzer` | Retain, add deprecation warning | Guide to PostProcessor |

## Backward Compatibility

- All moved symbols retain re-exports at their old locations, issuing `DeprecationWarning`
- The following public API signatures and behavior are unchanged: `plot_field()`, `plot_all_fields()`, `plot_density()`, `plot_phasespace()`, `plot_k_space()`, `process_simulation()`, `batch_process_parallel()`
- CLI entry points are outside the scope of this refactoring
- `Simulation` and `GridData` etc. in the sim/ layer are unchanged

## Implementation Order

1. **Phase 1** â€?Create `compute/` module (`fft.py`, `integrate.py`), eliminate `EMFAnalyzer.spectrum()` duplication
2. **Phase 2** â€?Create `analysis/_result_types.py`, `_protocol.py`, migrate `analyze_scattering` to `analysis/scattering.py`
3. **Phase 3** â€?Create `postproc.py` (`PostProcessor` + `PostAnalysisHub` + `PostVisHub`), integrate existing analyzers
4. **Phase 4** â€?Add `energy.py` in vis/ layer, complete the analysisâ†’vis chain
5. **Phase 5** â€?Add deprecation warnings to old entry points
6. **Phase 6** â€?Extend new diagnostic types one by one according to backlog priority (RAW P0 â†?TRACKS P0 â†?...)

## References

- Upstream: 2026-05-26-eval-diagnostic-coverage.md, 2026-05-28-eval-osiris-toolkit-architecture.md
- Downstream: 2026-05-28-plan-postproc-architecture.md
- TODO: 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
