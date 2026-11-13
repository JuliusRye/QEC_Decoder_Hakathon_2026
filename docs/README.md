# Team start

This is Cornell-QCA's fork of the organizer's starter for the November 13, 2026 QEC decoder hackathon. The decoder approach is undecided. The shared interface supports lookup tables, belief propagation, optimization, ML, and other original methods.

- [Competition format, rules and unresolved conflicts](COMPETITION.md)
- [Team workflow, migration and optional Colab training](WORKFLOW.md)
- [Measured setup evidence](evidence/setup-verification.json)
- [Experiment record template](templates/EXPERIMENT.md)
- [Organizer documentation](../README.md)

## Repository and access

Canonical repository: https://github.com/Cornell-QCA/QEC_Decoder_Hakathon_2026

`origin` is the Cornell-QCA fork. `upstream` is `JuliusRye/QEC_Decoder_Hakathon_2026`. The imported organizer revision is `6c03afbf06068f2ad10e6ddff0d68852835b9888`.

Intended contributors: Kevin, Iván (`smokevan`), Matt (`machommcan`), and Alec (`AlecRiso`). Access is verified separately from a real clone/push drill. This is a public fork; the previous practice repository is private. Keep private team materials and credentials out of public commits. Competition code shared publicly must also be made available through the competition's Kaggle Discussion or Code tabs under the rules.

## Local setup

From the repository root:

```sh
uv sync --locked
source .venv/bin/activate
```

Install the base environment only. The optional `tutorials` extra includes decoder packages prohibited in competition submissions. The verified local interpreter is Python 3.13.7, with NumPy 2.2.6 and Stim 1.16.0. The package's ordinary notebook support is installed; no ML framework was added.

Download all five files from the [Kaggle Data tab](https://www.kaggle.com/competitions/quantum-error-correction-decoder/data) into `data/kaggle/`: `train.csv`, `test.csv`, `sample_submission.csv`, and the two circuit files. The current local checkout already contains the download. Downloaded files, `runs/`, and root-level generated submission CSVs are excluded through `.gitignore`.

The organizer's runner expects the CSV name to match its directory name. A local symlink `data/kaggle/kaggle.csv -> test.csv` allows its unchanged runner to read the official download:

```sh
# On a fresh checkout, after downloading the five files:
ln -s test.csv data/kaggle/kaggle.csv

# Local format/timing smoke check with the organizer's all-zero placeholder:
mkdir -p runs
python submission_template/run_local.py --problem-set data/kaggle --out runs/placeholder.csv
```

These are local checks, not submissions. **The downloaded test IDs disagree with the sample submission IDs; resolve this before uploading any prediction file.** See [the evidence and conflicts](COMPETITION.md#unresolved-source-conflicts).

## What was verified

The base environment installs, both official circuits have 70 detectors and 4 observables, and training/test files each have 200,000 rows with 100,000 per basis. The unchanged placeholder returns binary arrays of the expected shape and identical predictions across five repeats. Its training bit error rate is 0.28814625. This only verifies plumbing, not a useful decoder or performance on the organizer's machine.

The downloaded circuits differ in bytes from the bundled copies but are equal after Stim parses them. No listed banned decoder package is installed. No Kaggle prediction was submitted. Submission readiness remains blocked by the ID discrepancy.
