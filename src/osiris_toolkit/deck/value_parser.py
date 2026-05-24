"""Convert raw token strings to typed Python values and assemble arrays.

Schema-aware type coercion: when a section name is provided, parameter types
are looked up from the OSIRIS Fortran namelist definitions in schemas,
overriding heuristic token type inference.

Slice metadata (e.g. nx_p(1:2)) is preserved in the output alongside values
as structured wrappers.
"""

from typing import Any

from .lexer import TokenType
from .schemas.parameters import ParamSpec, get_param_spec


def parse_real(raw: str) -> float:
    """Parse a real number, normalizing Fortran 'd' exponent to 'e'."""
    return float(raw.lower().replace('d', 'e'))


def parse_integer(raw: str) -> int:
    return int(raw)


def parse_boolean(raw: str) -> bool:
    """Parse .true. / .false. (case-insensitive)."""
    return raw.lower() == 'true'


def parse_string(raw: str) -> str:
    """Return string value as-is (quotes already stripped by lexer)."""
    return raw


def parse_slice_dims(raw: str) -> list[tuple[int | None, int | None]]:
    """Parse slice notation like '1:3' or '1:2,1' or ':,1'.

    Returns a list of (start, end) tuples. None means wildcard colon.
    """
    dims = []
    for part in raw.split(','):
        part = part.strip()
        if ':' in part:
            s_str, e_str = part.split(':', 1)
            s = int(s_str.strip()) if s_str.strip() else None
            e = int(e_str.strip()) if e_str.strip() else None
            dims.append((s, e))
        else:
            # Single index: '1'
            idx = int(part.strip())
            dims.append((idx, idx))
    return dims


def parse_value(raw: str, token_type: TokenType) -> Any:
    """Convert a raw token string to its typed Python value."""
    if token_type == TokenType.STRING:
        return raw
    elif token_type == TokenType.BOOLEAN:
        return parse_boolean(raw)
    elif token_type == TokenType.INTEGER:
        return parse_integer(raw)
    elif token_type == TokenType.REAL:
        return parse_real(raw)
    else:
        return raw


def _coerce_to_type(value: Any, spec: ParamSpec) -> Any:
    """Coerce a parsed value to the type specified by ParamSpec.

    When the token type matches the schema type, the value is returned as-is.
    When they differ (e.g. integer token for a real parameter), conversion occurs.
    """
    target = spec.python_type
    if target is float and isinstance(value, (int, float)):
        return float(value)
    elif target is int and isinstance(value, float) and value == int(value):
        return int(value)
    elif target is bool and isinstance(value, str):
        lower = value.lower()
        if lower in ('.true.', 'true', 't', '.t.', '1'):
            return True
        if lower in ('.false.', 'false', 'f', '.f.', '0'):
            return False
    return value


def _wrap_sliced_value(
    value: Any,
    slice_raw: str,
    dims: list[tuple[int | None, int | None]],
    spec: ParamSpec | None,
) -> dict[str, Any]:
    """Wrap a sliced array value with dimension metadata."""
    result: dict[str, Any] = {
        "value": value,
        "slice": slice_raw,
        "dims": dims,
    }
    if spec is not None:
        result["type"] = spec.fortran_type
    return result


def assemble_params(
    raw_params: list,
    section_name: str | None = None,
) -> dict[str, Any]:
    """Assemble typed parameters from a list of ParamAssignment objects.

    Handles:
      - Simple scalars: dt = 0.07
      - 1D array slices: nx_p(1:3) = 32, 32, 32
      - Multi-line 2D arrays: type(1:2,1) = ..., type(1:2,2) = ...
      - Scalar override of single-element slices: param(1:1) = value

    When *section_name* is provided, parameter types are looked up from the
    OSIRIS Fortran namelist schemas in param_schemas for accurate type coercion.

    Slice metadata is preserved in the output for all array (sliced) parameters.
    """
    # For each parameter assignment, parse keys and values.
    # Collect all assignments, then assemble arrays.
    result: dict[str, Any] = {}

    # Group assignments by base name
    # For sliced parameters, collect (slice_raw, dims, values) tuples
    sliced: dict[str, list[tuple[str, list[tuple[int | None, int | None]], list[Any]]]] = {}

    for pa in raw_params:
        raw_vals = pa.raw_values
        for key in pa.keys:
            name = key.name
            spec = get_param_spec(section_name, name) if section_name else None

            # Schema-aware type coercion
            coerced_vals = []
            for v in raw_vals:
                if spec is not None:
                    coerced_vals.append(_coerce_to_type(v, spec))
                else:
                    coerced_vals.append(v)

            if key.slice is None:
                # Scalar — single value (or multi-value for non-sliced multi-assign)
                if len(coerced_vals) == 1:
                    result[name] = coerced_vals[0]
                elif len(coerced_vals) > 1:
                    result[name] = coerced_vals
            else:
                if name not in sliced:
                    sliced[name] = []
                sliced[name].append((key.slice, key.slice.dims, coerced_vals))

    # Now assemble sliced arrays
    for name, entries in sliced.items():
        spec = get_param_spec(section_name, name) if section_name else None
        slice_raw = str(entries[0][0])
        dims = entries[0][1]

        if len(entries) == 1:
            _, _, vals = entries[0]
            result[name] = _wrap_sliced_value(
                _build_array(dims, vals), slice_raw, dims, spec,
            )
        else:
            # Multi-line assignment: build N-dimensional array
            all_dims = [e[1] for e in entries]
            result[name] = _wrap_sliced_value(
                _build_nd_array(entries), slice_raw, _dedup_dims(all_dims), spec,
            )

    return result


def _dedup_dims(
    dims_list: list[list[tuple[int | None, int | None]]],
) -> list[tuple[int | None, int | None]]:
    """Merge dimension lists from multi-line assignments."""
    if not dims_list:
        return []
    # Take the first entry's dimensions as primary
    primary = list(dims_list[0])
    for other in dims_list[1:]:
        for i, (a, b) in enumerate(other):
            if i < len(primary):
                ps, pe = primary[i]
                if ps is None or (a is not None and a < ps):
                    ps = a
                if pe is None or (b is not None and b > pe):
                    pe = b
                primary[i] = (ps, pe)
    return primary


def _build_array(
    dims: list[tuple[int | None, int | None]], vals: list[Any]
) -> Any:
    """Build a 1D array from slice dimensions and values.

    If the slice is exactly one element in all dimensions, return a scalar.
    If there are fewer values than the slice size, use the given values as-is.
    """
    if not dims:
        return vals[0] if len(vals) == 1 else vals

    # Compute expected size
    total_size = 1
    for s, e in dims:
        if s is not None and e is not None:
            total_size *= (e - s + 1)

    if total_size == 1 and len(vals) == 1:
        return vals[0]

    # If fewer values than slice size, use the given values as-is
    return vals if len(vals) > 1 else vals[0]


def _build_nd_array(
    entries: list[tuple],
) -> Any:
    """Build an N-dimensional array from multi-line slice assignments.

    Each entry is (slice_obj, dims, values).
    For a 2D array like type(1:2,1), type(1:2,2), builds a list of lists.
    """
    if not entries:
        return []

    # Determine number of dimensions
    # The first dimension of the slice is the one iterated across entries.
    # Subsequent dimensions are per-entry dimensions.

    # For 2D: entries = [( [(1,2), (1,1)], [val1, val2] ), ( [(1,2), (2,2)], [val3, val4] )]
    # Result should be: [[val1, val2], [val3, val4]]

    # Sort entries by fixed (single-index) dimensions
    if len(entries[0][1]) > 1:
        # Sort by non-varying (fixed) dimension index
        def sort_key(entry):
            return tuple(
                dims_i[0] if dims_i[0] == dims_i[1] else 0
                for dims_i in entry[1]
            )
        sorted_entries = sorted(entries, key=sort_key)

        result_2d = []
        for _, dims, vals in sorted_entries:
            # Check if inner values need further expansion
            inner_dims = dims[:-1]  # dimensions before the fixed dimension
            if inner_dims and len(vals) > 1:
                # Inner dimensions are sliced
                inner_size = 1
                for s, e in inner_dims:
                    if s is not None and e is not None:
                        inner_size *= (e - s + 1)

                if inner_size == len(vals):
                    result_2d.append(list(vals))
                elif inner_size == 1 and len(vals) == 1:
                    result_2d.append(vals[0])
                else:
                    result_2d.append(list(vals))
            else:
                result_2d.append(vals[0] if len(vals) == 1 else list(vals))

        return result_2d

    # 1D: return all expanded values directly
    all_vals = []
    for _, _, vals in entries:
        if len(vals) == 1:
            all_vals.append(vals[0])
        else:
            all_vals.extend(vals)
    return all_vals
