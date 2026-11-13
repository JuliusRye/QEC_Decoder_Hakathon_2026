# Team start

Cornell-QCA's canonical repository is [Cornell-QCA/QEC_Decoder_Hakathon_2026](https://github.com/Cornell-QCA/QEC_Decoder_Hakathon_2026). `origin` is this fork; `upstream` is [JuliusRye/QEC_Decoder_Hakathon_2026](https://github.com/JuliusRye/QEC_Decoder_Hakathon_2026). Organizer updates through `739d627` are merged into `main`; the latest update replaces the scoring plot. The imported starter was `6c03afb`.

- [Competition format, rules, deadlines, and conflicts](COMPETITION.md)
- [Contribution and review procedure](../CONTRIBUTING.md)
- [Experiment and optional Colab procedure](WORKFLOW.md)
- [Source coverage and dated Kaggle context](sources/README.md)
- [Candidate algorithms and exploratory BP/LUT results](ALGORITHMS.md)
- [Standalone BP check](evidence/standalone-bp.json), [full local BP timing](evidence/bp-full-local.json), and [Colab pipeline smoke](evidence/colab-mlp-smoke.json)
- [Papers and technical documentation](references/README.md)
- [Literature review, decoder ranking, and reference LERs (BP-OSD, exact MLE, hybrid LUT)](LITERATURE.md)
- [Private source-memory access](memory/README.md)
- [Initial setup evidence](evidence/setup-verification.json) — historical observations, including the first incorrect sample IDs
- [Experiment record template](templates/EXPERIMENT.md)

## Local setup

For a fresh checkout:

```sh
git clone https://github.com/Cornell-QCA/QEC_Decoder_Hakathon_2026.git
cd QEC_Decoder_Hakathon_2026
```

Use Python 3.13 for parity with the organizer's described hand-in environment. The verified baseline environment uses Python 3.13.7, NumPy 2.2.6, Stim 1.16.0, and Numba 0.61.2. Install from the lockfile:

```sh
python3 scripts/bootstrap.py
source .venv/bin/activate
NUMBA_NUM_THREADS=2 python -m unittest discover -s tests -v
```

The bootstrap requires Git, Python, `uv`, and authenticated private-repository access. Accept your GitHub invitation first; if needed, use `gh auth login` and `gh auth setup-git` with your own account. It creates or updates a private memory clone beside the checkout under `.qca-memory/`, and saves its location in ignored `.qca-local.json`. Re-run after pulling to refresh the environment and archive. Read the private clone's `AGENTS.md`, then search relevant transcripts. See [memory onboarding and troubleshooting](memory/README.md). Public contributors without private access can install the decoder environment alone with `uv sync --locked --extra baselines`.

The base package supports the organizer notebooks. The optional `tutorials` extra includes QEC decoder packages banned in competition submissions. The baseline extra supplies Numba; it does not install those decoder packages.

Download all five files from the [Kaggle Data tab](https://www.kaggle.com/competitions/quantum-error-correction-decoder/data) to `data/kaggle/`: `train.csv`, `test.csv`, `sample_submission.csv`, and the X/Z circuit files. These downloads and `runs/` are ignored. An existing local symlink `data/kaggle/kaggle.csv -> test.csv` lets the organizer runner read this download; create it only if absent:

```sh
ln -s test.csv data/kaggle/kaggle.csv
mkdir -p runs
python submission_template/run_local.py --problem-set data/kaggle --out runs/placeholder.csv
```

The runner above uses the organizer all-zero placeholder. It verifies loading and CSV output. The corrected root `sample_submission.csv` uses `gen_` IDs; an older downloaded sample may use `test_`. Preserve IDs from `test.csv`, compare them with the current corrected template, and record the file hashes before upload. See [the source correction](COMPETITION.md#source-conflicts-and-corrections).

## Candidate evaluation

Candidate folders implement the same standalone `decode` contract. The [MLP Colab notebook](../notebooks/colab_mlp_baseline.ipynb) is an optional training starting point; only a small CPU training/export smoke check is established here; it did not beat the zero baseline. The BP candidate uses normalized min-sum with a global reliability-ordered GF(2) fallback. The LUT candidate uses empirical bitwise majority for observed syndromes and zeros for unseen syndromes. Read the implementation and relevant tests before changing either; global elimination is not an implementation of localized statistics decoding (LSD) or a searched OSD decoder.

```sh
# Analyze the official circuit models.
python scripts/analyze_model.py --circuits data/kaggle

# Train the sparse LUT on generated shots (once per fresh model directory).
python decoders/lut/train.py --circuits data/kaggle --shots 200000 --seed 20261113

# Evaluate candidates on identical newly sampled X and Z data.
# Choose a new output directory every time; existing directories are rejected.
NUMBA_NUM_THREADS=2 python scripts/evaluate.py --decoders bp lut \
  --circuits data/kaggle --shots 2000 --seed 719 --runs 3 \
  --out runs/bp-lut-719
```

Keep training samples separate from evaluation samples. Evaluation saves the frozen samples, circuit text, predictions, source copies, hashes, environment, and paired error counts. Its per-candidate first-call and median timings include work performed inside `decode`; they are local observations. Finalists are timed on the organizer's hardware and complete test batch. Review provenance and any dirty working tree before publishing an experiment claim.

LUT training uses `python decoders/lut/train.py --circuits data/kaggle --shots 200000 --seed 20261113`. It refuses to replace an existing model for the same circuit. Preserve the prior model and its record before deliberately training a replacement; keep both training code and the selected model for hand-in.

## What the initial setup verified

The [dated setup record](evidence/setup-verification.json) checked installation, 70 detectors and 4 observables per circuit, and 200,000 rows in each train/test file with 100,000 per basis. The all-zero placeholder was repeatable and had training bit error rate 0.28814625. Downloaded and bundled circuits differed in raw bytes but agreed when parsed by Stim. These checks establish plumbing, not candidate accuracy or organizer-machine speed.

Kaggle team membership and GitHub collaborator access require their own checks. The intended four contributors are Kevin, Iván (`smokevan`), Matt (`machommcan`), and Alec (`AlecRiso`). Repository access alone does not establish official Kaggle team membership. Do not infer repository visibility; check before pushing competition code and apply the sharing rules in [COMPETITION.md](COMPETITION.md).
