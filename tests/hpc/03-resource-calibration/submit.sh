#!/bin/bash
#SBATCH --job-name=hpc-res
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

python tests/hpc/03-resource-calibration/test_estimate.py
