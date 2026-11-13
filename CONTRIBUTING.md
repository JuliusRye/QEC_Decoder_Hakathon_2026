# Contributing

Work from [team setup](docs/README.md) and [the competition contract](docs/COMPETITION.md). Claim one bounded experiment or fix with an owner, expected result, and cheap falsifying check. Check for another contributor's changes before editing shared files.

## Share work with the team

Use a short-lived branch in this repository for each contribution, including research notes. Matt can put his existing technical docs on a branch and open a pull request; a second permanent docs repository is unnecessary. Include references and distinguish hypotheses from measured results. Keep private transcripts in the private archive.

Start with a clean working tree and update the shared branch:

```sh
git switch main
git pull --ff-only origin main
git switch -c docs/topic-name
# Edit and verify the contribution, then stage the specific changed files.
git add docs/path-to-note.md
git commit -m "Document topic and supporting references"
git push -u origin HEAD
```

Open a pull request into `main` and ask a teammate to review it. Use `decoder/`, `experiment/`, or `fix/` branch prefixes for other work. After merge, everyone updates with `git switch main` and `git pull --ff-only origin main`. If Git reports local changes or divergent history, preserve the work and resolve it deliberately; do not reset or force-push shared `main`.

Multiple agents may read in parallel. Assign an owner and branch to each writing task; avoid concurrent edits to the same checkout or files. A separate clone or worktree gives each writer an independent working tree. Record a compact handoff with the branch/commit, changed files, evidence, open questions, and next owner. Pull before starting and again before integrating a contribution. Private archive access and Site task assignment are separate; follow [memory coordination](docs/memory/README.md).

## Develop and verify

1. Use a branch for one candidate or hypothesis. Keep the organizer utilities separate from original decoder implementations.
2. Preserve the `decode(circuit, detector_events)` interface and bitwise LER definition. Add meaningful regression checks for algorithm or interface changes, then run the test suite below.
3. Evaluate competing candidates on identical frozen X/Z samples independent of training. Save provenance, predictions, paired error counts, first-call time, repeated decode times, hardware, and thread count under a new `runs/` directory.
4. Update the relevant setup, candidate description, and agent instructions alongside a tested change. Add a compact experiment record with [this template](docs/templates/EXPERIMENT.md), linking the immutable evidence.
5. Ask a teammate to review the method, rule compliance, evidence, and self-contained hand-in. State which checks ran and which remain unverified in the pull request.

```sh
uv sync --locked --extra baselines
NUMBA_NUM_THREADS=2 uv run --locked --extra baselines python -m unittest discover -s tests -v
```

An optional [GitHub Actions template](docs/development/github-tests.yml) runs this suite and the context checker on Python 3.13 without a Kaggle login. It is not activated: the current GitHub sign-in lacks permission to publish workflow files. Downloaded competition data and full timing runs are local checks; do not imply CI validates leaderboard accuracy, GPU behavior, or organizer-machine speed. Updating dependencies requires a consistent lockfile and exact candidate hand-in requirements.

## Prepare a submission

Preserve the selected commit, model files, training code, seeds, circuit/data hashes, and output. Validate every row against `test.csv`, using corrected `gen_` IDs and columns `id,L0,L1,L2,L3`. Compare a fresh hand-in installation's predictions against the selected CSV and aim for exact reproduction. Check remaining team submission allowance and official team membership. Uploads and external messages require explicit authorization.

All code must satisfy the original-decoder rules. Keep prohibited tutorial decoder dependencies out of candidate environments. Confirm current repository visibility before a push; public sharing must also be available to all participants through Kaggle Discussion or Code as required by the rules. Private source transcripts and credentials belong outside this repository; see [the memory access boundary](docs/memory/README.md).
