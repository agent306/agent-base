import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("agent_base", Path(__file__).resolve().parents[1] / "bootstrap/agent_base.py")
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class BootstrapTests(unittest.TestCase):
    def args(self, root, *extra):
        return ["--provider", "codex", "--home", str(root), "--codex-home", str(root / ".codex"), *extra]

    def test_merge_preserves_unrelated_secrets_and_tables(self):
        original = '# private\nmodel = "old"\nsecret = "do-not-print"\n[plugins.a]\nenabled = false\n[agents]\ncustom = 7\n'
        merged = app.merge_config(original)
        parsed = tomllib.loads(merged)
        self.assertEqual(parsed["secret"], "do-not-print")
        self.assertEqual(parsed["plugins"]["a"], {"enabled": False})
        self.assertEqual(parsed["agents"]["custom"], 7)
        self.assertIn("# private", merged)
        self.assertEqual(app.merge_config(merged), merged)

    def test_conflict_preflight_has_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = root / ".codex"
            cfg.mkdir()
            (cfg / "config.toml").write_text('model = "gpt-6-astra"\n')
            (cfg / "AGENTS.md").write_text("Never delegate anything.\n")
            before = {p.name: p.read_bytes() for p in cfg.iterdir()}
            with self.assertRaises(ValueError):
                app.main(["setup", *self.args(root)])
            self.assertEqual(before, {p.name: p.read_bytes() for p in cfg.iterdir()})

    def test_copy_setup_backup_validation_and_idempotence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = root / ".codex"
            cfg.mkdir()
            (cfg / "config.toml").write_text('model = "gpt-6-astra"\n[plugins.example]\nenabled = true\n')
            (cfg / "AGENTS.md").write_text("Reviewed previous preferences.\n")
            args = self.args(root, "--copy", "--config-resolution", "baseline", "--reviewed-instructions-sha256", app.sha(cfg / "AGENTS.md"))
            app.main(["setup", *args])
            app.main(["validate", *args])
            app.main(["setup", *args])
            self.assertEqual(len(list((cfg / "agent-base-backups").rglob("*.*"))), 2)
            self.assertTrue(tomllib.loads((cfg / "config.toml").read_text())["plugins"]["example"]["enabled"])
            self.assertEqual(json.loads((cfg / "agent-base-install.json").read_text())["mode"], "copy")

    def test_override_and_skill_conflicts_stop_before_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = root / ".codex"
            cfg.mkdir()
            (cfg / "AGENTS.override.md").write_text("Different authority")
            (root / ".agents/skills/ui-ux").mkdir(parents=True)
            with self.assertRaises(ValueError):
                app.main(["setup", *self.args(root)])
            self.assertFalse((cfg / "agent-base").exists())

    def test_unix_link_behavior_without_affecting_user_home(self):
        if app.os.name == "nt":
            self.skipTest("Unix symlink path must be exercised on Unix; Windows gets real junction validation")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            app.main(["setup", *self.args(root)])
            self.assertTrue((root / ".codex/AGENTS.md").is_symlink())
            app.main(["validate", *self.args(root)])

    def test_unknown_provider_does_not_guess(self):
        with self.assertRaisesRegex(ValueError, "Ask the user"):
            app.main(["setup", "--provider", "unknown"])

    def test_explicit_keep_preserves_instruction_and_config_choices(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            cfg = root / ".codex"
            cfg.mkdir()
            (cfg / "AGENTS.md").write_text("User chose to retain this policy.\n")
            (cfg / "config.toml").write_text('model = "gpt-6-astra"\n')
            app.main(["setup", *self.args(root, "--copy", "--keep-instructions", "--config-resolution", "keep")])
            self.assertEqual((cfg / "AGENTS.md").read_text(), "User chose to retain this policy.\n")
            self.assertEqual(tomllib.loads((cfg / "config.toml").read_text())["model"], "gpt-6-astra")


if __name__ == "__main__":
    unittest.main()
