#!/bin/bash
#SBATCH --job-name=hpc-vis
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-vis-%j.out
#SBATCH --error=slurm-vis-%j.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
export MPLBACKEND=Agg
cd <PROJECT_ROOT>

export SIM_DATA_PATH="<SIM_DATA_DIR>"

python tests/hpc/04-large-data-scale/test_throughput.py --mode vis
