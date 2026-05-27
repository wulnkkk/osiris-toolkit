#!/bin/bash
#SBATCH --job-name=hpc-mpi
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --time=00:30:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

module load <mpi_module_openmpi>

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

export SIM_DATA_PATH="<SIM_DATA_DIR>"

mpirun -np $SLURM_NTASKS python tests/hpc/01-mpi-multinode/test_mpi.py
