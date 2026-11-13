# RESEARCH-ONLY REFERENCE BENCHMARK. Not a decoder candidate. bench.py/refbench.py import the banned
# 'ldpc' package (installed in a throwaway venv) purely to obtain reference numbers. Never import from decoders/.
# Usage: python refbench.py <repo-root> [args]
"""Reference benchmarks (research only; uses banned ldpc for a reference number, never for submission).
Usage: refbench.py <repo> <N_ILP> <N_eval> <N_LUT>. Eval: fresh shots, seed 7. ILP-MLE on the first N_ILP eval shots. LUT from N_LUT independent shots (seeds 1000+, 1M per seed)."""
import sys, time, json, stim, numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csc_matrix, hstack, identity
sys.path.insert(0, sys.argv[1] + "/src")
from hackathon_2026.circuit_tools import problem_info
from ldpc.bposd_decoder import BpOsdDecoder
root=sys.argv[1]; N=int(sys.argv[3]); N_ILP=int(sys.argv[2]); N_LUT=int(sys.argv[4]); out={"N_eval":N,"N_ILP":N_ILP,"N_LUT":N_LUT}
try:  # low CPU priority on Windows so the laptop stays responsive
    import ctypes; ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x40)
except Exception: pass
def keys_of(d):
    pk = np.packbits(d, axis=1, bitorder='little')  # 9 bytes
    lo = pk[:, :8].copy().view(np.uint64)[:, 0]; hi = pk[:, 8].astype(np.uint64)
    return lo, hi
for b in "XZ":
    c = stim.Circuit.from_file(f"{root}/data/train/{b}_circuit.stim")
    m = problem_info(c); H, L, p = m["H"], m["L"], m["p"]; n = H.shape[1]
    d, o = c.compile_detector_sampler(seed=7).sample(N, separate_observables=True)
    r = {}
    # BP-OSD-CS7 reference
    dec = BpOsdDecoder(csc_matrix(H), error_channel=list(p), max_iter=100, bp_method="minimum_sum", ms_scaling_factor=0.0, schedule="parallel", osd_method="osd_cs", osd_order=7)
    t=time.time(); osd = np.array([(L @ dec.decode(s.astype(np.uint8))) % 2 for s in d]).astype(bool); r["bposd_cs7_us_per_shot"]=1e6*(time.time()-t)/N
    r["bposd_cs7_ler"]=float(np.mean(osd!=o))
    # ILP exact MLE: min w.e  s.t. H e - 2 k = s
    w = np.log((1-p)/p); m70 = H.shape[0]
    A = hstack([csc_matrix(H.astype(float)), -2*identity(m70, format='csc')]).tocsc()
    cvec = np.concatenate([w, np.zeros(m70)]); integ = np.ones(n+m70)
    bnds = Bounds(np.zeros(n+m70), np.concatenate([np.ones(n), np.full(m70, 4)]))
    ilp = np.zeros((N_ILP,4),bool); t=time.time(); nfail=0
    for i in range(N_ILP):
        s = d[i].astype(float)
        res = milp(cvec, constraints=LinearConstraint(A, s, s), integrality=integ, bounds=bnds, options={"disp":False})
        if res.x is None: nfail+=1; continue
        e = np.round(res.x[:n]).astype(np.uint8); ilp[i] = (L @ e) % 2
    r["ilp_ms_per_shot"]=1e3*(time.time()-t)/N_ILP; r["ilp_fail"]=nfail
    r["ilp_ler_subset"]=float(np.mean(ilp!=o[:N_ILP])); r["bposd_cs7_ler_subset"]=float(np.mean(osd[:N_ILP]!=o[:N_ILP]))
    r["ilp_vs_osd_bits_ilp_only_wrong"]=int(((ilp!=o[:N_ILP])&(osd[:N_ILP]==o[:N_ILP])).sum())
    r["ilp_vs_osd_bits_osd_only_wrong"]=int(((ilp==o[:N_ILP])&(osd[:N_ILP]!=o[:N_ILP])).sum())
    print(b, "ILP done", r, flush=True)
    # LUT from 20M independent shots: per-syndrome count and per-bit ones
    los=[];his=[];obs=[]
    for k in range(N_LUT//1_000_000):
        dd, oo = c.compile_detector_sampler(seed=1000+k).sample(1_000_000, separate_observables=True)
        lo,hi = keys_of(dd); los.append(lo); his.append(hi); obs.append(oo)
    lo=np.concatenate(los); hi=np.concatenate(his); ob=np.concatenate(obs); del los,his,obs
    order=np.lexsort((lo,hi)); lo=lo[order]; hi=hi[order]; ob=ob[order]
    new=np.ones(len(lo),bool); new[1:]=(lo[1:]!=lo[:-1])|(hi[1:]!=hi[:-1]); starts=np.flatnonzero(new)
    cnt=np.diff(np.append(starts,len(lo))); ones=np.add.reduceat(ob.astype(np.int64),starts,axis=0)
    ulo=lo[starts]; uhi=hi[starts]; r["lut_distinct"]=int(len(starts))
    # lookup eval shots
    elo,ehi=keys_of(d)
    # combine to sortable key: hi*2^64+lo via lexsort-search: use structured
    U=np.empty(len(ulo),dtype=[('h','<u8'),('l','<u8')]); U['h']=uhi; U['l']=ulo
    E=np.empty(N,dtype=U.dtype); E['h']=ehi; E['l']=elo
    idx=np.searchsorted(U,E); idx=np.minimum(idx,len(U)-1); hit=(U[idx]==E)
    ecnt=np.where(hit,cnt[idx],0); eones=np.where(hit[:,None],ones[idx],0)
    lutpred = 2*eones > ecnt[:,None]
    r["lut_hybrid"]={}
    for thr in [1,5,20,100,1000]:
        use = ecnt>=thr
        hyb = np.where(use[:,None], lutpred, osd)
        r["lut_hybrid"][thr]={"coverage":float(use.mean()),"ler":float(np.mean(hyb!=o)),
            "covered_lut_ler":float(np.mean(lutpred[use]!=o[use])) if use.any() else None,
            "covered_osd_ler":float(np.mean(osd[use]!=o[use])) if use.any() else None}
    out[b]=r; print(b, json.dumps(r,indent=1), flush=True)
json.dump(out, open("refbench_result.json","w"), indent=1)
