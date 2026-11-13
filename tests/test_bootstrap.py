"""Exercise local Git clones without network access or private source text."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def test_clone_update_and_preserve_local_work(self):
        spec = importlib.util.spec_from_file_location(
            "bootstrap", ROOT / "scripts/bootstrap.py"
        )
        bootstrap = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bootstrap)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "source"
            subprocess.run(
                ["git", "init", "-b", "main", str(source)],
                check=True,
                capture_output=True,
            )

            def commit(text, location=source):
                (location / "STATE.md").write_text(text)
                subprocess.run(
                    ["git", "-C", str(location), "add", "STATE.md"], check=True
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(location),
                        "-c",
                        "user.name=Test",
                        "-c",
                        "user.email=test@example.invalid",
                        "-c",
                        "commit.gpgsign=false",
                        "commit",
                        "-m",
                        "Update",
                    ],
                    check=True,
                    capture_output=True,
                )

            commit("first\n")
            destination = base / "memory"
            bootstrap.sync_memory(destination, str(source))
            self.assertEqual((destination / "STATE.md").read_text(), "first\n")
            commit("second\n")
            bootstrap.sync_memory(destination, str(source))
            self.assertEqual((destination / "STATE.md").read_text(), "second\n")
            (destination / "STATE.md").write_text("local work\n")
            with self.assertRaisesRegex(RuntimeError, "local changes"):
                bootstrap.sync_memory(destination, str(source))
            self.assertEqual((destination / "STATE.md").read_text(), "local work\n")
            (destination / "STATE.md").write_text("second\n")
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(destination),
                    "remote",
                    "set-url",
                    "origin",
                    str(base / "unrelated"),
                ],
                check=True,
            )
            with self.assertRaisesRegex(RuntimeError, "origin"):
                bootstrap.sync_memory(destination, str(source))
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(destination),
                    "remote",
                    "set-url",
                    "origin",
                    str(source),
                ],
                check=True,
            )
            commit("local commit\n", destination)
            local_head = bootstrap.git("rev-parse", "HEAD", cwd=destination)
            commit("upstream commit\n")
            with self.assertRaisesRegex(RuntimeError, "Git pull.*diverg"):
                bootstrap.sync_memory(destination, str(source))
            self.assertEqual(
                bootstrap.git("rev-parse", "HEAD", cwd=destination), local_head
            )
            self.assertEqual((destination / "STATE.md").read_text(), "local commit\n")


if __name__ == "__main__":
    unittest.main()
