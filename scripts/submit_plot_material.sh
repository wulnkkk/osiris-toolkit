#!/bin/bash
#SBATCH -J plot_material
#SBATCH -p <partition>
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --time=04:00:00
#SBATCH -o slurm-plot-%j.out
#SBATCH -e slurm-plot-%j.err

source <CONDA_HOME>/etc/profile.d/conda.sh
conda activate <conda_env>

export MPLBACKEND=Agg
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1

cd <PROJECT_ROOT>
python scripts/plot_material.py
