#!/bin/bash
#SBATCH --job-name=hpc-vis-test
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --partition=<partition>
#SBATCH --output=slurm-vis-test-%j.out
#SBATCH --error=slurm-vis-test-%j.err

source ~/miniconda3/etc/profile.d/conda.sh && conda activate <conda_env>
cd <PROJECT_ROOT>

export SIM_DATA_PATH="<SIM_DATA_DIR>"
export OMP_NUM_THREADS=1

# Quick test: only 5 iterations
python3 -c "
import os, time, multiprocessing
import matplotlib
matplotlib.use('Agg')
from concurrent.futures import ProcessPoolExecutor, as_completed
from osiris_toolkit.sim import Simulation
from osiris_toolkit.vis.field import plot_field
from osiris_toolkit.parallel._cluster import limit_blas_threads

def worker(args):
    sim_path, it, qty, out = args
    limit_blas_threads(1)
    sim = Simulation(sim_path)
    plot_field(quantity=qty, iteration=it, sim=sim, output=out)
    return out

sim_path = os.environ['SIM_DATA_PATH']
sim = Simulation(sim_path)
qty = 'e1'
iters = sim.list_iterations(qty)[:5]

print(f'Testing {len(iters)} iterations with 4 workers')
t0 = time.perf_counter()

ctx = multiprocessing.get_context('spawn')
tasks = [(sim_path, it, qty, f'/tmp/test_vis_{it:06d}.png') for it in iters]

with ProcessPoolExecutor(max_workers=4, mp_context=ctx) as ex:
    futures = {ex.submit(worker, t): t for t in tasks}
    for f in as_completed(futures):
        try:
            f.result()
            print(f'  OK: {futures[f][1]}')
        except Exception as e:
            print(f'  FAIL: {futures[f][1]}: {e}')

print(f'Done, elapsed: {time.perf_counter()-t0:.1f}s')
"
