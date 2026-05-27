#!/bin/bash
#SBATCH --job-name=hpc-ana
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-ana-%j.out
#SBATCH --error=slurm-ana-%j.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

export SIM_DATA_PATH="<SIM_DATA_DIR>"

python tests/hpc/04-large-data-scale/test_throughput.py --mode analysis
