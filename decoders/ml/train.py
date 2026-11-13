"""Optional PyTorch training; inference exports use NumPy and Stim only.

Run in Colab's existing PyTorch environment or a separate training environment.
All train/validation shots are independently generated from the supplied circuits.
"""

import argparse
from hashlib import sha256
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import platform
import numpy as np
import stim
from decoder import MLP, fingerprint


def train(circuit, out, shots=50000, epochs=5, hidden=64, seed=41, batch_size=512):
    # Set before PyTorch/CUDA initialization for deterministic matrix products.
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch

    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    events, labels = circuit.compile_detector_sampler(seed=seed).sample(
        shots, separate_observables=True
    )
    validation, truth = circuit.compile_detector_sampler(seed=seed + 1000000).sample(
        10000, separate_observables=True
    )
    x = torch.tensor(events, dtype=torch.float32, device=device)
    y = torch.tensor(labels, dtype=torch.float32, device=device)
    model = torch.nn.Sequential(
        torch.nn.Linear(circuit.num_detectors, hidden),
        torch.nn.ReLU(),
        torch.nn.Linear(hidden, circuit.num_observables),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    generator = torch.Generator(device=device).manual_seed(seed)
    for epoch in range(epochs):
        order = torch.randperm(shots, generator=generator, device=device)
        for start in range(0, shots, batch_size):
            indices = order[start : start + batch_size]
            optimizer.zero_grad()
            loss = loss_fn(model(x[indices]), y[indices])
            loss.backward()
            optimizer.step()
        print(
            f"epoch {epoch + 1}: last minibatch BCE {loss.detach().item():.5f}",
            flush=True,
        )
    key = fingerprint(circuit)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{key}.npz"
    pending = out / f"{key}.pending.npz"
    if path.exists() or path.with_suffix(".json").exists() or pending.exists():
        raise FileExistsError(path)
    params = {
        name: value.detach().cpu().numpy() for name, value in model.state_dict().items()
    }
    with pending.open("xb") as handle:
        np.savez_compressed(
            handle,
            w0=params["0.weight"].T,
            b0=params["0.bias"],
            w1=params["2.weight"].T,
            b1=params["2.bias"],
            circuit_hash=key,
        )
    exported = MLP.load(pending, key)
    with torch.no_grad():
        reference = (
            model(torch.tensor(validation[:1000], dtype=torch.float32, device=device))
            .cpu()
            .numpy()
        )
    np.testing.assert_allclose(
        exported.logits(validation[:1000]), reference, rtol=1e-4, atol=1e-5
    )
    # All reported predictions use the hand-in NumPy path, not the training framework.
    predictions = exported.predict(validation)
    record = {
        "circuit_hash": key,
        "seed": seed,
        "validation_seed": seed + 1000000,
        "shots": shots,
        "validation_shots": len(truth),
        "epochs": epochs,
        "hidden": hidden,
        "batch_size": batch_size,
        "device": device,
        "python": platform.python_version(),
        "packages": {p: metadata.version(p) for p in ["torch", "numpy", "stim"]},
        "validation_ler": float(np.mean(predictions != truth)),
        "zero_ler": float(truth.mean()),
        "weights_sha256": sha256(pending.read_bytes()).hexdigest(),
        "training_source_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    # Publish only after parity passes. Exclusive sidecar/link creation prevents
    # replacing a prior selected artifact; interrupted pending files remain visible.
    with path.with_suffix(".json").open("x") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")
    os.link(pending, path)
    pending.unlink()
    print(json.dumps(record, indent=2), flush=True)
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--circuits", type=Path, default=Path("data/kaggle"))
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "models")
    parser.add_argument("--shots", type=int, default=50000)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--seed", type=int, default=41)
    args = parser.parse_args()
    if min(args.shots, args.epochs, args.hidden) < 1:
        parser.error("shots,epochs,hidden must be positive")
    for i, b in enumerate("XZ"):
        train(
            stim.Circuit.from_file(args.circuits / f"{b}_circuit.stim"),
            args.out,
            args.shots,
            args.epochs,
            args.hidden,
            args.seed + i,
        )
