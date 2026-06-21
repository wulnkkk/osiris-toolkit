---
audience: [human, agent]
role: developer
topic: modules
kind: reference
module: io
updated: 2026-06-04
---

# io — ZDF & HDF5 Binary Reader & Parallel I/O

Clean-room implementation of the ZDF (Zipped Diagnostic Format) and HDF5 binary readers.
Stateless, thread-safe, parallel-ready. The ZDF reader contains no code derived from the
ZPIC/OSIRIS reference implementation.

## Architecture

```
_read_grid() / _read_particles() / _read_tracks()
        │
        ├── _read_record()      ZDF record header (id + name + length)
        ├── _read_dataset()     Regular dataset (type + dims + array)
        ├── _read_cdset()       Chunked dataset (START → CHUNK* → END)
        ├── _read_iteration()   Iteration metadata (n, t, tunits)
        ├── _read_grid_info()   Grid metadata (ndims, nx, label, axes)
        ├── _read_part_info()   Particle metadata (nparts, quants, labels)
        └── _read_track_info()  Track metadata (ntracks, ndump, niter)

_parallel.py
        └── read_many()         ThreadPoolExecutor batch reads
```

**Files:**

| File | Role |
|------|------|
| `_format.py` | ZDF binary constants: magic, record type IDs, dtype maps (functional facts of the protocol) |
| `_types.py` | Lightweight dataclasses: `ZdfRecord`, `ZdfIteration`, `ZdfGridInfo`, `ZdfPartInfo`, `ZdfTrackInfo` |
| `_reader.py` | Stateless reader functions: `read_grid()`, `read_particles()`, `read_tracks()`, `read_info()` |
| `_reader_hdf5.py` | Stateless HDF5 reader functions: same signatures as `_reader.py`, using `h5py` |
| `_parallel.py` | `read_many(paths, reader_fn, max_workers)` — concurrent batch reads |

## Format Coverage

This module supports both **ZDF** and **HDF5** output formats produced by OSIRIS.

| Aspect | Status |
|--------|--------|
| ZDF grid files | Fully supported (all 10 diagnostic kinds) |
| ZDF particles files | Fully supported (RAW dumps) |
| ZDF tracks-2 files | Fully supported (TRACKS diagnostics) |
| ZDF record versions | v0, v1, v2 all supported |
| Flat / nested directory layouts | Both auto-discovered |
| HDF5 grid files | Fully supported (via `_reader_hdf5.py`) |
| HDF5 particles files | Fully supported |
| HDF5 tracks files | Fully supported |
| HDF5 `SIMULATION` metadata | Supported (`ZdfFileInfo.simulation_info`) |

## HDF5 Support (v0.12.0+)

OSIRIS can output simulation data in HDF5 format when compiled with HDF5 libraries.
The toolkit reads both ZDF and HDF5 formats transparently — `Simulation` automatically
detects the format from the file extension (`.zdf` vs `.h5`).

**Optional dependency**: `pip install osiris-toolkit[hdf5]`

The HDF5 reader (`_reader_hdf5.py`) implements the same function signatures as the
ZDF reader, producing identical `Zdf*` dataclass types. The `Simulation` layer dispatches
to the correct reader based on file extension — no user configuration needed.

**Key differences from ZDF**:
- HDF5 files include a `SIMULATION` attribute (git version, compile time, input file content)
  accessible via `ZdfFileInfo.simulation_info`
- Data is stored as single HDF5 datasets rather than ZDF's CDSET chunked format
- HDF5 files require `h5py >= 3.0` (optional dependency)

If your simulation outputs HDF5 and you prefer ZDF, switch in the input deck:

```
simulation {
    file_format = "zdf",
}
```

## Usage

```python
from osiris_toolkit.io import read_grid, read_particles, read_tracks, read_info, read_many

# Read a grid file (fields, density, etc.)
data, grid_info, iteration = read_grid("e1-000100.zdf")
print(data.shape)       # (nx, ny) — C-order numpy array
print(iteration.n)      # 100

# Read a particles file
data_dict, part_info, iteration = read_particles("raw-000100.zdf")
print(part_info.nparts) # 4096

# Read a tracks file
tracks, track_info = read_tracks("tracks.zdf")

# Read metadata only (no array data)
info = read_info("e1-000100.zdf")
print(info.file_type)   # "grid"

# Parallel read: 100 E-field frames across 4 threads
paths = [f"e1-{i:06d}.zdf" for i in range(0, 1000, 10)]
results = read_many(paths, read_grid, max_workers=4)
```

## Key Design Decisions

- **Stateless**: every function opens its own file handle, reads, and closes. No shared state.
- **Thread-safe**: no locks needed. Each call is independent. Safe with `ThreadPoolExecutor` and `multiprocessing`.
- **Fortran → C order**: data in ZDF files is Fortran (column-major) order. The reader reverses dimensions
  to produce standard C-order (row-major) numpy arrays.
- **Chunked datasets**: large fields (e.g., 6656×9888) are stored in 500+ chunks. The reader allocates
  the full array first, then maps each chunk into the correct slice using start/stride/count from the
  CDSET_CHUNK headers.

## Format Attribution

The ZDF format was developed at Instituto Superior Tecnico (IST) as part of the ZPIC educational
code suite. This implementation is based on the format specification (`zdf/README.md`) and empirical
verification against real ZDF binary files. It contains no code from the ZPIC/OSIRIS reference implementation.
