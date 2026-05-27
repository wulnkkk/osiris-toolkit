#!/bin/bash
#SBATCH --job-name=hpc-env
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --array=0-3
#SBATCH --time=00:15:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-%j-%a.out
#SBATCH --error=slurm-%j-%a.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

export SIM_DATA_PATH="<SIM_DATA_DIR>"

python tests/hpc/02-slurm-env/test_env.py
