# io — ZDF Binary Reader & Parallel I/O

Clean-room implementation of the ZDF (Zipped Diagnostic Format) binary reader. Stateless,
thread-safe, parallel-ready. Contains no code derived from the ZPIC/OSIRIS reference implementation.

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
| `_parallel.py` | `read_many(paths, reader_fn, max_workers)` — concurrent batch reads |

## Format Coverage

This module supports **ZDF (Zipped Diagnostic Format) only**. HDF5 output is not supported.

| Aspect | Status |
|--------|--------|
| ZDF grid files | Fully supported (all 10 diagnostic kinds) |
| ZDF particles files | Fully supported (RAW dumps) |
| ZDF tracks-2 files | Fully supported (TRACKS diagnostics) |
| ZDF record versions | v0, v1, v2 all supported |
| Flat / nested directory layouts | Both auto-discovered |
| HDF5 output | Not supported |

OSIRIS uses ZDF as its default output format. If your simulation is configured to output HDF5,
switch to ZDF by setting in the input deck:

```
simulation {
    file_format = "zdf",
}
```

The `osiris-toolkit sim info` command automatically detects the output format and will
warn if HDF5 files are detected.

For a detailed assessment of format coverage, see
[IO Coverage Evaluation](../devlog/io-osiris-coverage-evaluation.md).

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
