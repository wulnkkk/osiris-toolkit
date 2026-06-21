"""Tests for io._format — ZDF binary format constants."""

import pytest

from osiris_toolkit.exceptions import FormatError
from osiris_toolkit.io._format import (
    DTYPE_NAMES,
    DTYPE_TO_NUMPY,
    MAGIC,
    RecordType,
    numpy_dtype,
    record_type_name,
    record_version,
)


class TestMagic:
    def test_magic_value(self):
        assert MAGIC == b"ZDF1"

    def test_magic_length(self):
        assert len(MAGIC) == 4


class TestRecordType:
    def test_all_types_distinct(self):
        types = [
            RecordType.INT32,
            RecordType.DOUBLE,
            RecordType.STRING,
            RecordType.DATASET,
            RecordType.CDSET_START,
            RecordType.CDSET_CHUNK,
            RecordType.CDSET_END,
            RecordType.ITERATION,
            RecordType.GRID_INFO,
            RecordType.PART_INFO,
            RecordType.TRACK_INFO,
        ]
        assert len(set(types)) == len(types)

    def test_type_ids_are_upper_16_bits(self):
        for t in [RecordType.STRING, RecordType.DATASET, RecordType.ITERATION]:
            assert t & 0x0000FFFF == 0

    def test_record_type_name_known(self):
        assert record_type_name(RecordType.STRING) == "string"
        assert record_type_name(RecordType.DATASET) == "dataset"
        assert record_type_name(RecordType.CDSET_START) == "cdset_start"
        assert record_type_name(RecordType.ITERATION) == "iteration"
        assert record_type_name(RecordType.GRID_INFO) == "grid_info"

    def test_record_type_name_unknown(self):
        unknown = 0x99990000
        assert "unknown" in record_type_name(unknown)


class TestRecordVersion:
    def test_extracts_lower_16_bits(self):
        id_ver = RecordType.GRID_INFO | 1
        assert record_version(id_ver) == 1

    def test_version_zero(self):
        assert record_version(RecordType.STRING | 0) == 0

    def test_version_max(self):
        assert record_version(RecordType.STRING | 0xFFFF) == 0xFFFF


class TestDtypeMapping:
    def test_known_dtypes(self):
        assert numpy_dtype(1) == "int8"
        assert numpy_dtype(2) == "uint8"
        assert numpy_dtype(5) == "int32"
        assert numpy_dtype(9) == "float32"
        assert numpy_dtype(10) == "float64"

    def test_unknown_dtype_raises(self):
        with pytest.raises(FormatError, match="Unknown ZDF data type ID"):
            numpy_dtype(999)

    def test_all_dtype_names_mapped(self):
        for dtype_id in DTYPE_NAMES:
            if dtype_id != 0:  # null has no numpy mapping
                assert numpy_dtype(dtype_id) is not None

    def test_dtype_to_numpy_coverage(self):
        assert len(DTYPE_TO_NUMPY) == 10
        for k in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            assert k in DTYPE_TO_NUMPY
