# RESEARCH-ONLY REFERENCE BENCHMARK. Not a decoder candidate. bench.py/refbench.py import the banned
# 'ldpc' package (installed in a throwaway venv) purely to obtain reference numbers. Never import from decoders/.
# Usage: python bench.py <repo-root> [args]
import sys, time, stim, numpy as np
sys.path.insert(0, sys.argv[1] + "/src")
from hackathon_2026.circuit_tools import problem_info
from ldpc.bposd_decoder import BpOsdDecoder
from scipy.sparse import csc_matrix
root=sys.argv[1]; N=int(sys.argv[2])
cfgs = {"BP-OSD0": dict(osd_method="osd0", osd_order=0),
        "BP-OSD-CS7": dict(osd_method="osd_cs", osd_order=7),
        "BP-OSD-CS12": dict(osd_method="osd_cs", osd_order=12)}
for b in "XZ":
    c = stim.Circuit.from_file(f"{root}/data/train/{b}_circuit.stim")
    m = problem_info(c); H, L, p = m["H"], m["L"], m["p"]
    d, o = c.compile_detector_sampler(seed=7).sample(N, separate_observables=True)
    for name, kw in cfgs.items():
        dec = BpOsdDecoder(csc_matrix(H), error_channel=list(p), max_iter=100, bp_method="minimum_sum", ms_scaling_factor=0.0, schedule="parallel", **kw)
        t=time.time(); pred = np.array([(L @ dec.decode(s.astype(np.uint8))) % 2 for s in d])
        dt=time.time()-t
        print(f"[{b}] {name:12s} LER={np.mean(pred!=o):.5f}  shot-fail={np.mean((pred!=o).any(1)):.4f}  {1e6*dt/N:.0f} us/shot (1 core)", flush=True)
