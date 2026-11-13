# Team workflow and migration

The decoder family is undecided. Start with the organizer's `submission_template/decoder.py` contract and choose an approach after brainstorming. No ML architecture, framework, GPU service, or training notebook has been selected.

## What carries over from practice

The previous workspace is [Cornell-QCA/qec-decoder-hackathon-2026](https://github.com/Cornell-QCA/qec-decoder-hackathon-2026), with a local checkout at `/Users/kevinsulli/Programming/QCA/qec-decoder-hackathon-2026`.

Carry over the habits: one experiment per branch, frozen evaluation data, source/configuration/data fingerprints, immutable run records, deterministic repeats, named owners, and one evaluation owner when comparing runtime. Use the [experiment template](templates/EXPERIMENT.md) to keep a hypothesis and its evidence together.

The practice `matching` and `bposd` candidates depend on prohibited QEC decoder libraries, so they cannot be competition candidates. Their toy surface-code fixtures, graph restrictions, any-error-per-shot score, and warm-timing interpretation also do not match this challenge. No practice decoder or harness code was ported. Reusing the workflow does not require importing the old implementation.

## Minimal experiment loop

1. Record one hypothesis and its falsifying check before running it.
2. Implement an original candidate behind `decode(circuit, detector_events)`.
3. Evaluate on fixed labelled data, using bitwise LER; retain a fresh holdout for generalization checks.
4. Record the commit, data hashes, package versions, training seed, artifacts, accuracy, setup cost and decode timing.
5. Have another teammate review the evidence and hand-in dependencies.
6. Before a submission, resolve the ID conflict, verify exact column order and test IDs, preserve the selected model/weights, and confirm the remaining submission budget.

The hand-in must import from its folder alone after installing its pinned requirements. It must not depend on the editable `hackathon_2026` checkout or fetch anything at runtime. If using organizer helpers inside the decoder, make the necessary code/package available in the hand-in under its license and test in a fresh environment.

## Optional Colab training

Google Colab is a possible training environment if the team chooses ML. It is not needed for BP, lookup-table, solver, or other CPU approaches, and it is not the organizer's timing environment.

If ML is chosen, a bounded Colab experiment should record the repository commit, exact framework version, GPU type, seeds, circuit hashes and generated training data policy. Save weights plus training code and configuration to persistent storage; a runtime reset must not lose the experiment. Export a self-contained decoder and exact requirements, then check predictions and timing independently of Colab. Select compute and storage only after the method and resource budget are agreed; no Colab session or paid compute was started.

## Open decisions

- Decoder approach and cheapest useful first experiment.
- Integration/evaluation owner and backup.
- Private working location for team code: this public fork does not provide private team development.
- Official Kaggle team membership for all four people.
- Organizer clarification of ID and scoring conflicts in [COMPETITION.md](COMPETITION.md).
