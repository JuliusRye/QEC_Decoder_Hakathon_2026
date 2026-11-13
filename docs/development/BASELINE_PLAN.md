# Original baseline implementation plan

Goal: establish testable original decoders behind the organizer's existing interface; keep optimization and architecture choices visible.

Fixed by competition: binary input (shots,70), binary output (shots,4), separate X/Z circuits, bitwise LER, no existing QEC decoder implementations. User requests original BP baseline, practical LUT feasibility, optional Colab ML proof of concept, and shared repo context.

Implementation choices: normalized min-sum BP with deterministic reliability-guided GF(2) correction on nonconvergence; sparse empirical bitwise-majority LUT with zero fallback and reported coverage; optional small ML training notebook exporting NumPy-only inference weights. The BP correction is a global baseline, not a claim to implement LSD. Matching is deferred until a circuit-level projection/lifting construction is validated.

- [x] BP: hand-derived tiny cases, zero priors, syndrome consistency, inconsistent syndromes, deterministic repeats, output contract; then original NumPy/Numba kernel and standalone decoder folder.
- [x] LUT: per-bit majority, unseen syndromes, circuit fingerprint and save/load; then original compact packed-key implementation and training CLI.
- [x] Evaluation: frozen fresh paired samples, immutable result directory, exact source/data/package fingerprints, accuracy versus all-zero, first-call and repeated times; integration tests.
- [x] ML: Colab-ready original small MLP training and portable NumPy inference, export parity check; optional compute only, no paid resources.
- [x] Context: AGENTS.md, CLAUDE.md link, CONTRIBUTING.md, source-indexed competition snapshots, references, memory entry point, measured findings and a prepared repeatable CI template.
- [x] Verify whole suite, real-circuit baseline comparison, independent review, then report evidence and publishing constraints.

Acceptance: each baseline loads through --decoder; no banned decoder package is introduced; no labels enter decode; stand-alone folders install from exact pins; tests include independently hand-derived examples and empirical results are explicitly exploratory.

Current evidence: rank(H)=70 for both bases; H shapes X=(70,2470), Z=(70,2465); error mechanisms have detector degree up to 7. A complete four-bit LUT needs 2^69 bytes per basis. Upstream fixes 8447b59 and 2614389 have been merged on baseline/original-decoders. This task-owned checkout is isolated from teammates' checkouts; no new worktree is needed.

## Verified handoff

Twelve regression tests pass, including out-of-order GF(2) pivots, detector bits63/64/69, rejection of deterministic fault probabilities, invalid/mutating/nondeterministic outputs, bitwise LUT majority, NumPy MLP inference, and incomplete/mismatched ML packaging. An independent review exercised2,116 tiny/boundary GF(2) oracle cases after correction. The original runner accepts the BP candidate; a fresh hand-in environment runs it without the development package. Source links and hashes pass the context checker.

Exploratory evidence: docs/evidence/baselines-002.json, standalone-bp.json, lut-training.json, colab-mlp-smoke.json. The CPU Colab smoke checks training/export, not useful ML accuracy; packaging hardening afterward is regression-tested locally but has not been rerun in Colab. A fresh full Data-page source export and Rules recapture remain unverified; the main Overview and earlier full Rules are preserved. No prediction upload has been made.

Next research work: implement genuine LSD cluster growth or higher-order search only as a separately tested method; validate any color-code restriction/lifting mapping before ordinary matching; optimize kernels only against frozen paired samples.

CI activation: workflow template is preserved as docs/development/github-tests.yml. GitHub rejected workflow-file publication because the current OAuth sign-in lacks workflow scope. Baseline/context publication is independent; no additional permission was granted.
