"""Tests for parallel._cluster utilities."""

import os

from osiris_toolkit.parallel import (
    detect_available_workers,
    detect_job_array,
    detect_mpi_rank,
    limit_blas_threads,
    split_iterations,
)


class TestSplitIterations:
    def test_even_split(self):
        iterations = [0, 10, 20, 30, 40, 50]
        assert split_iterations(iterations, 0, 3) == [0, 30]
        assert split_iterations(iterations, 1, 3) == [10, 40]
        assert split_iterations(iterations, 2, 3) == [20, 50]

    def test_single_rank(self):
        iterations = [1, 2, 3, 4, 5]
        assert split_iterations(iterations, 0, 1) == [1, 2, 3, 4, 5]

    def test_more_ranks_than_items(self):
        iterations = [0, 10]
        assert split_iterations(iterations, 0, 4) == [0]
        assert split_iterations(iterations, 1, 4) == [10]
        assert split_iterations(iterations, 2, 4) == []
        assert split_iterations(iterations, 3, 4) == []

    def test_empty_iterations(self):
        assert split_iterations([], 0, 4) == []

    def test_nonzero_start(self):
        iterations = [5, 15, 25, 35]
        assert split_iterations(iterations, 0, 2) == [5, 25]
        assert split_iterations(iterations, 1, 2) == [15, 35]


class TestDetectAvailableWorkers:
    def test_default(self):
        n = detect_available_workers()
        assert isinstance(n, int)
        assert n >= 1

    def test_slurm_env(self, monkeypatch):
        monkeypatch.setenv("SLURM_CPUS_PER_TASK", "16")
        assert detect_available_workers() == 16

    def test_omp_env(self, monkeypatch):
        monkeypatch.setenv("OMP_NUM_THREADS", "8")
        assert detect_available_workers() == 8

    def test_slurm_takes_priority(self, monkeypatch):
        monkeypatch.setenv("SLURM_CPUS_PER_TASK", "32")
        monkeypatch.setenv("OMP_NUM_THREADS", "4")
        assert detect_available_workers() == 32


class TestLimitBlasThreads:
    def test_sets_all_vars(self, monkeypatch):
        # Clear first
        for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS",
                     "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            monkeypatch.delenv(var, raising=False)

        limit_blas_threads(1)
        assert os.environ["OMP_NUM_THREADS"] == "1"
        assert os.environ["MKL_NUM_THREADS"] == "1"
        assert os.environ["OPENBLAS_NUM_THREADS"] == "1"
        assert os.environ["NUMEXPR_NUM_THREADS"] == "1"

    def test_custom_n(self, monkeypatch):
        limit_blas_threads(2)
        assert os.environ["OMP_NUM_THREADS"] == "2"


class TestDetectJobArray:
    def test_no_env(self, monkeypatch):
        monkeypatch.delenv("SLURM_ARRAY_TASK_ID", raising=False)
        monkeypatch.delenv("SLURM_ARRAY_TASK_COUNT", raising=False)
        monkeypatch.delenv("PBS_ARRAYID", raising=False)
        monkeypatch.delenv("PBS_ARRAY_INDEX", raising=False)
        assert detect_job_array() is None

    def test_slurm_array(self, monkeypatch):
        monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "3")
        monkeypatch.setenv("SLURM_ARRAY_TASK_COUNT", "10")
        assert detect_job_array() == (3, 10)

    def test_pbs_array(self, monkeypatch):
        monkeypatch.delenv("SLURM_ARRAY_TASK_ID", raising=False)
        monkeypatch.setenv("PBS_ARRAYID", "5")
        monkeypatch.setenv("PBS_ARRAY_INDEX", "20")
        assert detect_job_array() == (5, 20)

    def test_partial_env_returns_none(self, monkeypatch):
        monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "1")
        monkeypatch.delenv("SLURM_ARRAY_TASK_COUNT", raising=False)
        assert detect_job_array() is None


class TestDetectMpiRank:
    def test_no_mpi(self):
        result = detect_mpi_rank()
        assert result is None or isinstance(result, tuple)
