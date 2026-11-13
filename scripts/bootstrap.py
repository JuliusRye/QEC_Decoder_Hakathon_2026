"""Prepare the locked decoder environment and a separate private memory clone."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MEMORY_URL = "https://github.com/kevinsullivan0/cornell-qca-hackathon-memory-2026.git"
LOCAL = ROOT / ".qca-local.json"


def git(*args, cwd=None):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode:
        # Classify errors without echoing remote URLs, credential helpers, or
        # other possibly sensitive Git diagnostics into an agent's report.
        error = result.stderr.lower()
        if (
            "fast-forward" in error
            or "diverg" in error
            or "unrelated histories" in error
        ):
            detail = "History has diverged; a fast-forward update was refused. Coordinate with the clone's owner."
        elif "not a git repository" in error:
            detail = "The destination is not a Git repository; select another private directory."
        elif ".lock" in error:
            detail = "Another Git operation may hold a lock. Wait for it to finish; do not delete locks blindly."
        elif any(
            word in error
            for word in (
                "authentication",
                "permission denied",
                "repository not found",
                "username",
                "password",
            )
        ):
            detail = "GitHub access was denied. Accept your invitation and use your own account (gh auth login; gh auth setup-git)."
        elif any(
            word in error
            for word in ("resolve", "timed out", "connection", "unable to access")
        ):
            detail = "Git could not reach the remote. Check network, proxy, and Git authentication."
        else:
            detail = "Inspect the clone and Git configuration locally; private access and a reachable remote are required."
        raise RuntimeError(
            f"Git {args[0]} failed (exit {result.returncode}). {detail} "
            "No reset, stash, or force-push was attempted."
        )
    return result.stdout.strip()


def repository_id(url):
    return (
        url.removeprefix("https://")
        .removeprefix("ssh://git@")
        .replace("git@github.com:", "github.com/")
        .removesuffix("/")
        .removesuffix(".git")
    )


def sync_memory(destination, url=MEMORY_URL):
    destination = Path(destination).expanduser().resolve()
    if destination.is_relative_to(ROOT) or ROOT.is_relative_to(destination):
        raise RuntimeError(
            "The private memory clone must be outside the decoder checkout."
        )
    if destination.exists():
        if (
            Path(git("rev-parse", "--show-toplevel", cwd=destination)).resolve()
            != destination
        ):
            raise RuntimeError(
                "The memory destination is not an independent Git clone."
            )
        origin = git("remote", "get-url", "origin", cwd=destination)
        if repository_id(origin) != repository_id(url):
            raise RuntimeError(
                "The memory clone's origin is different; choose another destination."
            )
        if git("status", "--porcelain", cwd=destination):
            raise RuntimeError(
                "The memory clone has local changes; preserve them before updating."
            )
        if git("branch", "--show-current", cwd=destination) != "main":
            raise RuntimeError("The memory clone must be on main before updating.")
        git("pull", "--ff-only", "origin", "main", cwd=destination)
    else:
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        git("clone", "--branch", "main", url, str(destination))
    return git("rev-parse", "HEAD", cwd=destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--memory-dir", type=Path, help="private clone outside this checkout"
    )
    parser.add_argument(
        "--skip-env", action="store_true", help="only sync private memory"
    )
    args = parser.parse_args()
    try:
        saved = json.loads(LOCAL.read_text()) if LOCAL.exists() else {}
        destination = (
            args.memory_dir
            or saved.get("memory_dir")
            or (ROOT.parent / ".qca-memory" / "cornell-qca-hackathon-memory-2026")
        )
        destination = Path(destination).expanduser().resolve()
        revision = sync_memory(destination)
        required = (
            "AGENTS.md",
            "CLAUDE.md",
            "STATE.md",
            "TRANSCRIPTS.md",
            "TRANSCRIPTS.jsonl",
        )
        missing = [name for name in required if not (destination / name).is_file()]
        if missing:
            raise RuntimeError(
                "Private archive onboarding files are missing: " + ", ".join(missing)
            )
        LOCAL.write_text(
            json.dumps(
                {"memory_dir": str(destination), "memory_commit": revision}, indent=2
            )
            + "\n"
        )
        print(f"Private memory ready: {destination}\nRevision: {revision}", flush=True)
        if not args.skip_env:
            uv = shutil.which("uv")
            if not uv:
                raise RuntimeError(
                    "Memory is ready. Install uv, then rerun to prepare the decoder environment."
                )
            subprocess.run(
                [uv, "sync", "--locked", "--extra", "baselines"], cwd=ROOT, check=True
            )
        print(
            "Read the private AGENTS.md, then STATE.md; search TRANSCRIPTS.md only as needed."
        )
        print(
            "Use .qca-local.json to locate this private clone. Never commit its contents or local paths."
        )
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Setup incomplete: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
