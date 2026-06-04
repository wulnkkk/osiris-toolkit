# Frequently Asked Questions

## ZDF vs HDF5 Support

**Q: Does osiris-toolkit support HDF5 files?**

A: Yes, since v0.12.0. OSIRIS traditionally outputs ZDF (Zipped Diagnostic Format) files, which are the default. If your simulation was configured to write HDF5 output, osiris-toolkit can read those files as well. Both formats are handled transparently through the `io/` module. You do not need to change anything — the toolkit auto-detects the format.

---

## No Input Deck, No Unit Conversion

**Q: I don't have an input deck file. Can I still use the toolkit?**

A: Most operations work without an input deck (e.g., loading fields, plotting raw normalized data). However, **unit conversion to physical units requires an input deck**, because the normalization parameters (e.g. plasma density `n0`, magnetic field `B0`) come from the deck file. If no deck is available, pass `system=None` to functions that accept a `system` parameter, and work in normalized units.

---

## K-Space Plot Shows Blank Areas

**Q: My k-space plots have blank/white regions or the axis limits look wrong. How do I fix this?**

A: This was a known issue fixed in **v0.15.0**. The x-axis limits were previously too restrictive. If you are on an older version, upgrade to >= 0.15.0 or use `ax.set_xlim()` manually after plotting.

---

## K-Space Axis Label Mismatch

**Q: The k-space axis labels don't match what I expect — there's an extra /2π factor?**

A: This was fixed in **v0.15.0**. Previously, axis tick labels incorrectly included a division by 2π. This has been corrected. Upgrade to v0.15.0 or later to get the corrected labels.

---

## Batch Processing Is Silent for 20+ Minutes

**Q: `vis batch` runs for a long time with no output. Is it stuck?**

A: Batch processing can take a while, especially with many iterations. Use the `--progress` flag to get real-time feedback:

```bash
osiris-toolkit vis batch --progress <path> <name>
```

You can also use `--dry-run` first to see what will be processed without actually generating files.

---

## Density Plots Missing Some Species

**Q: I know my simulation has electrons, but the density plot doesn't show them. What's wrong?**

A: Per-species density files (e.g. `charge-electrons-NNNNNN.zdf`) use naming patterns that may not be matched by all `list_*()` regex patterns. This is a known limitation. As a workaround, you can manually list the files and load them with the lower-level `io` API.

---

## Memory Issues with `-j 8`

**Q: When I use `-j 8` for parallel processing, I run out of memory. What can I do?**

A: Each field of size 4000×3600 float32 consumes roughly 57 MB, and 8 workers each holding one field gives a baseline of ~456 MB — not counting overhead. Reduce the number of parallel workers:

```bash
osiris-toolkit vis batch -j 4 <path> <name>
```

Or even `-j 2` on memory-constrained machines. The toolkit will still process files in parallel, just with fewer concurrent workers.

---

## UnitConverter vs UnitSystem

**Q: I see both `UnitConverter` and `UnitSystem` in the API. Which one should I use?**

A: `UnitSystem` is the recommended interface (introduced in v0.15.0). It provides a cleaner, more intuitive API:

```python
from osiris_toolkit.units import UnitSystem

system = UnitSystem.from_params(params)
length_um = system.length.to(1.0, "um")   # 1 normalized length -> μm
```

The older `UnitConverter` class is still available for backward compatibility but is deprecated in favor of `UnitSystem`. See the [Unit Conversion user guide](user-guide/unit-conversion.md) for a detailed migration guide.

---

## How Do I Report a Bug?

Open an issue at <https://github.com/wulnkkk/osiris-toolkit/issues>. Please include:

- osiris-toolkit version (`osiris-toolkit --version`)
- Python version (`python --version`)
- A minimal reproducing example
- The OSIRIS simulation setup (if relevant)
