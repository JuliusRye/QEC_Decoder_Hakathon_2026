# Candidate algorithms and limits

This note defines the original implementations in `decoders/`. It separates methods already present from research ideas in [the reference index](references/README.md). Candidate quality requires independent evaluation; no method name establishes accuracy.

## Shared decoding problem

From each supplied circuit, merge detector-error mechanisms with identical detector **and** observable effects, combining probabilities by odd parity. Let `H` be the detector-by-mechanism binary matrix, `L` the observable-by-mechanism matrix, and `p_i` the mechanism priors. For a sampled hidden mechanism vector `e`,

$$s=He\pmod2,\qquad o=Le\pmod2.$$

The scored output is the four observable bits. The empirical bitwise loss is

$$\widehat{\mathrm{LER}}=\frac{1}{4N}\sum_{a=1}^N\sum_{j=0}^3[\widehat o_{aj}\ne o_{aj}].$$

Predicting the most likely entire four-bit class and predicting each marginal bit are different objectives. The latter minimizes this bitwise loss when conditional marginals are known.

## BP and global linear fallback

`decoders/bp/decoder.py` starts from prior log odds `log((1-p_i)/p_i)` and applies normalized min-sum messages on `H`'s Tanner graph. A check message has the syndrome-dependent sign product and the smallest incoming absolute magnitude, excluding its destination edge. Defaults are 30 iterations, scale 0.8, damping 0.2, with message clipping. It stops early when hard decisions satisfy `H e_hat = s`.

If BP does not converge, it retains its hard decision, forms residual syndrome `r = s + H e_hat mod 2`, and orders columns by increasing absolute posterior log odds. A GF(2) solve finds a correction `delta` supported on a reliability-preferred independent column set, satisfying `H delta = r`. Output is `L (e_hat + delta) mod 2`.

The fallback restores syndrome consistency for reachable syndromes; consistency alone does not identify the correct logical class. It uses global elimination. It does not implement the local cluster growth/factorization of LSD, a combinatorial OSD search, or color-code restriction and lifting. Report BP convergence/fallback counts with accuracy and timing. First-call Numba compilation and circuit preparation inside `decode` affect the first-call time.

## Sparse empirical LUT

`decoders/lut/decoder.py` packs each detector string, groups matching training syndromes, and stores the majority decision **separately for each observable bit**. For training count `n(s)` and bit-one count `n_j(s)`,

$$\widehat o_j(s)=[2n_j(s)>n(s)].$$

Ties and unseen syndromes predict zero. This is a sparse learned table; it does not enumerate all detector strings. Model loading checks the parsed circuit's SHA-256 fingerprint. Training seed, shot count, circuit fingerprint, number of distinct syndromes, and file size accompany the model. The recorded 200,000-shot training set per basis produced 152,928 distinct X syndromes (1,988,064 payload bytes; 749,337 compressed bytes) and 151,297 distinct Z syndromes (1,966,861 payload bytes; 741,522 compressed bytes); see `decoders/lut/models/*.json`. These are stored-sample sizes, not full-space coverage.

The actual official models have rank 70 for each basis, with 2,470 X mechanisms and 2,465 Z mechanisms; maximum detector support per mechanism is seven. Run `scripts/analyze_model.py` to reproduce these structural counts. A dense four-bit output table for every attainable syndrome requires at least

$$2^{70}\times4/8=2^{69}=590{,}295{,}810{,}358{,}705{,}651{,}712\text{ bytes}$$

per basis (about 590 decimal exabytes), before indexing or metadata. Code distance four and 18 data qubits do not reduce this circuit-level table to a small enumeration. Sparse-table coverage and unseen-syndrome error therefore need measurement.

## Small MLP candidate

`decoders/ml/decoder.py` evaluates a two-layer ReLU network with NumPy:

$$z(s)=\operatorname{ReLU}(sW_0+b_0)W_1+b_1,\qquad\widehat o_j=[z_j>0].$$

The training code uses optional PyTorch to fit weights from generated shots; inference needs NumPy/Stim and saved weights. The self-contained [Colab notebook](../notebooks/colab_mlp_baseline.ipynb) provides a training starting point; a separate [CPU smoke run](evidence/colab-mlp-smoke.json) completed one epoch on 2,000 generated training shots per basis and checked export parity. Its fresh validation LER was 0.50105 (X) and 0.42445 (Z), worse than the corresponding zero baselines; it is a pipeline check, not a useful trained candidate. A model file must match the circuit fingerprint. An untrained or missing model is not a usable decoder. Useful trained accuracy, GPU behavior, and full-batch hand-in timing remain unverified. The packaging helper rejects missing basis exports or mismatched artifact hashes. The BP/LUT benchmark below does not evaluate ML.

## Exploratory BP/LUT run

The [preserved report](evidence/baselines-002.json) records 2,000 fresh shots per basis (8,000 scored bits per basis), seeds 719/720, and three repeated calls on a local Intel Mac with four CPU threads as reported by the evaluator owner. It records a dirty working tree and source hashes; the commit alone does not identify the evaluated code.

| Basis | Zero bit LER | BP bit LER | LUT bit LER | LUT coverage |
| --- | ---: | ---: | ---: | ---: |
| X | 0.280625 | 0.083375 | 0.245875 | 0.2745 |
| Z | 0.272000 | 0.084500 | 0.238750 | 0.2980 |

On identical samples, BP alone was wrong on 368 X bits and 372 Z bits; LUT alone was wrong on 1,668 X bits and 1,606 Z bits. These are exploratory paired counts, with correlated bits within shots; they are not independent Bernoulli trials for a naive bit-level significance calculation.

BP first X call took 12.8845 s; its median X/Z times were 0.6767/0.7946 s. LUT medians were 0.00255/0.00372 s. These are small-batch local observations, including cold setup on the first call. They do not establish leaderboard LER, 100,000-shot performance, or timing on the organizer's B200 machine. Preserve the full frozen samples and source copies in `runs/baselines-002/` when comparing a later candidate.
