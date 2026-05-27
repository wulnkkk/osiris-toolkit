#!/bin/bash
#SBATCH --job-name=hpc-pipe
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:30:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

python tests/hpc/05-pipeline-e2e/test_pipeline.py
