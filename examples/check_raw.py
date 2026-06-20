from osiris_toolkit.sim import Simulation
import numpy as np

s = Simulation("/path/to/Zmaterial/Au")  # TODO: replace with your simulation path

for it in [0, 9000, 44100]:
    ps = s.get_phasespace("p1p2", "electrons", it)
    if ps is None:
        print(f"it={it}: get_phasespace returned None")
        continue
    if not hasattr(ps, 'data') or ps.data is None:
        print(f"it={it}: ps has no data")
        continue
    
    ps = s.get_phasespace("p1p2", "electrons", 44100)
    d = ps.data
    print(f"shape={d.shape}, min={d.min():.4e}, max={d.max():.4e}, positive={(d>0).sum()}, nonzero={(d!=0).sum()}, deposited={ps.deposited_quantity}")
    # Try taking absolute value
    d_abs = np.abs(d)
    print(f"abs: min={d_abs.min():.4e}, max={d_abs.max():.4e}, sum={d_abs.sum():.4e}")
    # Check if data is stored as charge deposition (negative for electrons)
    # Try negating
    d_neg = -d
    print(f"neg: min={d_neg.min():.4e}, max={d_neg.max():.4e}, positive={(d_neg>0).sum()}")
