"""Deterministic installer scenarios; all mutations use isolated temporary homes."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("agent_base", Path(__file__).resolve().parents[1] / "bootstrap/agent_base.py")
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "checkout"
        self.home = self.base / "home"
        self.codex = self.home / ".codex"
        self.snapshot = self.base / "rollback"
        self.repo.mkdir()
        for name in ("AGENTS.md", "BOOTSTRAP.md", "governance/core.md", "governance/workers.md", "profiles/codex/AGENTS.md", "docs/runtime.md", "design/README.md"):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Fixture\nScoped useful policy.\n", encoding="utf-8")
        (self.repo / "profiles/codex/AGENTS.md").write_text("# Adapter\nOptional {{BASE}}/docs/runtime.md\n", encoding="utf-8")
        config = self.repo / "profiles/codex/config.toml"
        config.write_text('model = "gpt-6-sol"\nmodel_reasoning_effort = "medium"\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 5\ndefault_subagent_model = "gpt-6-sol"\ndefault_subagent_reasoning_effort = "medium"\n', encoding="utf-8")
        skill = self.repo / "skills/ui-ux/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("---\nname: ui-ux\ndescription: A fixture\n---\nUse project guidance.\n", encoding="utf-8")
        self.addCleanup(patch.stopall)
        patch.object(app, "ROOT", self.repo).start()
        patch.object(app, "git_state", return_value={"revision": "a" * 40, "dirty": False}).start()
        self.output = io.StringIO()
        self.addCleanup(self.output.close)

    def run_cmd(self, command, *extra):
        with contextlib.redirect_stdout(self.output):
            app.main([command, "--provider", "codex", "--home", str(self.home), "--codex-home", str(self.codex), "--snapshot", str(self.snapshot), *extra])

    def write(self, name, contents):
        path = self.codex / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents.encode() if isinstance(contents, str) else contents)
        return path

    def install(self, *extra):
        self.run_cmd("setup", "--copy", *extra)

    def journals(self):
        return list((self.snapshot / "installer").glob("*.json"))

    def test_setup_generated_flat_payload_and_no_roles(self):
        self.install()
        text = app.read_text(self.codex / "AGENTS.md")
        self.assertIn("Scoped useful policy", text)
        self.assertIn((self.codex / "agent-base/docs/runtime.md").as_posix(), text)
        self.assertNotIn("{{BASE}}", text)
        self.assertFalse((self.codex / "agents").exists())
        self.run_cmd("validate")

    def test_idempotency_creates_only_one_snapshot_transaction(self):
        self.install()
        before = (self.codex / app.MANIFEST).read_bytes()
        self.install()
        self.assertEqual(len(self.journals()), 1)
        self.assertEqual(before, (self.codex / app.MANIFEST).read_bytes())

    def test_conflicts_have_no_writes(self):
        config = self.write("config.toml", 'model = "custom"\n')
        instructions = self.write("AGENTS.md", "Custom policy\n")
        with self.assertRaisesRegex(ValueError, "Unresolved conflicts"):
            self.install()
        self.assertEqual(config.read_text(), 'model = "custom"\n')
        self.assertEqual(instructions.read_text(), "Custom policy\n")
        self.assertFalse(self.snapshot.exists())

    def test_bom_crlf_and_unrelated_text_preserved(self):
        original = '\ufeff# user\r\nmodel = "old" # preference\r\nsecret = "fixture-only"\r\n[plugins.demo]\r\nenabled = false\r\n[agents] # workers\r\ncustom = 7\r\n'
        merged = app.merge_config(original)
        self.assertTrue(merged.startswith("\ufeff# user\r\n"))
        self.assertIn('secret = "fixture-only"\r\n', merged)
        self.assertIn('model = "gpt-6-sol" # preference\r\n', merged)
        self.assertEqual(app.merge_config(merged), merged)
        self.assertNotIn("\n", merged.replace("\r\n", ""))

    def test_inline_table_or_quoted_managed_keys_require_custom_merge(self):
        for text in ('"model" = "old"\n', '["agents"]\nenabled = false\n', 'agents = { enabled = false }\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                app.merge_config(text)

    def test_snapshot_inside_discovery_rejected(self):
        self.snapshot = self.codex / "backup"
        with self.assertRaisesRegex(ValueError, "outside"):
            self.install()
        self.assertFalse(self.codex.exists())

    def test_missing_snapshot_rejected_before_writes(self):
        with self.assertRaisesRegex(ValueError, "requires --snapshot"):
            app.main(["setup", "--provider", "codex", "--home", str(self.home), "--codex-home", str(self.codex), "--copy"])
        self.assertFalse(self.codex.exists())

    def test_existing_snapshot_audit_files_untouched(self):
        self.snapshot.mkdir()
        audit = self.snapshot / "snapshot.json"
        audit.write_text('"original audit"')
        self.install()
        self.assertEqual(audit.read_text(), '"original audit"')

    def test_local_instruction_drift_blocks_setup_and_validate(self):
        self.install()
        path = self.write("AGENTS.md", "Later user edit\n")
        with self.assertRaisesRegex(ValueError, "drift|locally modified"):
            self.run_cmd("validate")
        with self.assertRaisesRegex(ValueError, "locally modified"):
            self.install()
        self.assertEqual(path.read_text(), "Later user edit\n")

    def test_rollback_restores_bytes_and_preserves_later_unrelated_config(self):
        original = b'\xef\xbb\xbfmodel = "old"\r\n[plugins.a]\r\nenabled = true\r\n'
        config = self.write("config.toml", original)
        old = self.write("AGENTS.md", b"Prior reviewed policy\r\n")
        self.install("--config-resolution", "baseline", "--reviewed-instructions-sha256", app.sha(old))
        config.write_bytes(config.read_bytes() + b'\r\n[plugins.b]\r\nenabled = false\r\n')
        self.run_cmd("rollback")
        self.assertEqual(old.read_bytes(), b"Prior reviewed policy\r\n")
        parsed = tomllib.loads(app.read_text(config))
        self.assertEqual(parsed["model"], "old")
        self.assertFalse(parsed["plugins"]["b"]["enabled"])
        self.assertFalse((self.codex / app.MANIFEST).exists())
        self.assertTrue((self.repo / "governance/core.md").exists())

    def test_rollback_refuses_later_resource_edit_without_any_partial_restore(self):
        self.install()
        self.write("AGENTS.md", "User edit\n")
        manifest = (self.codex / app.MANIFEST).read_bytes()
        with self.assertRaisesRegex(ValueError, "Rollback conflict"):
            self.run_cmd("rollback")
        self.assertEqual((self.codex / app.MANIFEST).read_bytes(), manifest)

    def test_uninstall_restores_prior_managed_values_preserves_local_config(self):
        cfg = self.write("config.toml", 'model = "prior"\nsecret = "fixture"\n')
        self.install("--config-resolution", "baseline")
        cfg.write_bytes(cfg.read_bytes() + b'\n[plugins.later]\nenabled = true\n')
        self.run_cmd("uninstall")
        data = tomllib.loads(app.read_text(cfg))
        self.assertEqual(data["model"], "prior")
        self.assertEqual(data["secret"], "fixture")
        self.assertTrue(data["plugins"]["later"]["enabled"])
        self.assertNotIn("model_reasoning_effort", data)
        self.assertFalse((self.codex / "AGENTS.md").exists())
        self.assertFalse((self.home / ".agents/skills/ui-ux").exists())
        self.assertTrue(self.repo.exists())

    def test_uninstall_preserves_later_user_managed_key_and_instruction_edits(self):
        self.install()
        cfg = self.codex / "config.toml"
        cfg.write_text(app.read_text(cfg).replace('model = "gpt-6-sol"', 'model = "user-choice"'))
        self.write("AGENTS.md", "User policy")
        with self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
            self.run_cmd("uninstall")
        self.assertEqual(tomllib.loads(app.read_text(cfg))["model"], "user-choice")
        self.assertEqual(app.read_text(self.codex / "AGENTS.md"), "User policy")
        self.assertTrue((self.codex / app.MANIFEST).exists())
        self.assertNotIn("Uninstalled;", self.output.getvalue())

    def test_legacy_role_retirement_owned_hash_only_and_rollback(self):
        role = self.write("agents/agent-base-judgment.toml", 'model = "gpt-6-astra"\n')
        self.write(app.MANIFEST, json.dumps({"provider": "codex", "repository": str(self.repo), "mode": "linked", "managed_agents": {role.name: app.sha(role)}}))
        loader = self.write("AGENTS.md", app.legacy_loader(self.codex))
        before = loader.read_bytes()
        self.install()
        self.assertFalse(role.exists())
        self.run_cmd("rollback")
        self.assertTrue(role.exists())
        self.assertEqual(loader.read_bytes(), before)

    def test_legacy_role_edit_blocks_retirement(self):
        role = self.write("agents/agent-base-mechanical.toml", 'model = "old"\n')
        self.write(app.MANIFEST, json.dumps({"provider": "codex", "managed_agents": {role.name: app.sha(role)}}))
        role.write_text('model = "local-change"\n')
        with self.assertRaisesRegex(ValueError, "role|pin"):
            self.install()
        self.assertTrue(role.exists())

    def test_override_and_active_profile_conflicts(self):
        for name, text in (("AGENTS.override.md", "override"), ("config.toml", 'profile = "custom"\n[profiles.custom]\nmodel = "other"\n')):
            path = self.write(name, text)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Unresolved conflicts"):
                self.install()
            path.unlink()

    def test_unrelated_roles_profiles_fallbacks_are_notices_and_preserved(self):
        self.write("config.toml", 'project_doc_fallback_filenames = ["RULES.md"]\n[profiles.custom]\nmodel = "other"\n')
        role = self.write("agents/custom.toml", 'model = "other"\n')
        self.run_cmd("inspect")
        report = json.loads(self.output.getvalue())
        self.assertFalse(report["conflicts"])
        self.assertTrue(any("pin" in n for n in report["notices"]))
        self.install()
        self.assertEqual(role.read_text(), 'model = "other"\n')

    def test_wrong_provider_never_installs(self):
        with self.assertRaisesRegex(ValueError, "No approved provider"):
            app.main(["setup", "--provider", "other", "--home", str(self.home)])
        self.assertFalse(self.home.exists())

    def test_copy_refresh_requires_explicit_flag_and_detects_local_edits(self):
        self.install()
        (self.repo / "design/README.md").write_text("Reviewed new design")
        with self.assertRaisesRegex(ValueError, "copy stale"):
            self.run_cmd("validate")
        with self.assertRaisesRegex(ValueError, "refresh-copy"):
            self.install()
        self.install("--refresh-copy")
        self.assertEqual(app.read_text(self.codex / "agent-base/design/README.md"), "Reviewed new design")
        (self.codex / "agent-base/design/README.md").write_text("Local edit")
        with self.assertRaisesRegex(ValueError, "locally modified"):
            self.install("--refresh-copy")

    def test_update_requires_clean_reviewed_revision_never_runs_git_mutations(self):
        self.install()
        with patch.object(app, "git_state", return_value={"revision": "b" * 40, "dirty": True}):
            with self.assertRaisesRegex(ValueError, "clean"):
                self.run_cmd("update", "--reviewed-revision", "b" * 40)
        with self.assertRaisesRegex(ValueError, "Review"):
            self.run_cmd("update")
        with patch.object(app.subprocess, "run") as process:
            self.run_cmd("update", "--reviewed-revision", "a" * 40)
            process.assert_not_called()

    def test_real_platform_directory_links_and_scoped_rollback(self):
        self.run_cmd("setup")
        link = self.codex / "agent-base"
        self.assertTrue(app.is_link(link))
        self.assertTrue(app.linked_to(link, self.repo))
        self.assertFalse((self.codex / "AGENTS.md").is_symlink())
        self.run_cmd("validate")
        self.run_cmd("rollback")
        self.assertFalse(app.present(link))
        self.assertTrue((self.repo / "skills/ui-ux/SKILL.md").is_file())

    def test_stale_and_occupied_registration_conflict(self):
        occupied = self.home / ".agents/skills/ui-ux"
        occupied.mkdir(parents=True)
        (occupied / "SKILL.md").write_text("User skill")
        with self.assertRaisesRegex(ValueError, "Occupied"):
            self.install()
        self.assertEqual((occupied / "SKILL.md").read_text(), "User skill")

    def test_manifest_has_no_unrelated_settings_or_credentials(self):
        self.write("config.toml", 'private_token = "fixture-sensitive"\n')
        self.install()
        manifest = app.read_text(self.codex / app.MANIFEST)
        self.assertNotIn("fixture-sensitive", manifest)
        self.assertNotIn("private_token", manifest)

    def test_reviewed_active_profile_persists_but_detects_changed_profile(self):
        cfg = self.write("config.toml", 'profile = "custom"\n[profiles.custom]\nmodel = "other"\n')
        self.install("--reviewed-config-sha256", app.sha(cfg))
        self.run_cmd("validate")
        cfg.write_text(app.read_text(cfg).replace('model = "other"', 'model = "changed"'))
        with self.assertRaisesRegex(ValueError, "Selected profile"):
            self.run_cmd("validate")

    def test_added_ignored_or_empty_copy_directory_is_preserved_on_uninstall(self):
        self.install()
        user_dir = self.codex / "agent-base/.git"
        user_dir.mkdir()
        (user_dir / "local-work").write_text("User work")
        with self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
            self.run_cmd("uninstall")
        self.assertEqual((user_dir / "local-work").read_text(), "User work")
        self.assertTrue((self.codex / app.MANIFEST).exists())
        self.assertNotIn("Uninstalled;", self.output.getvalue())

    def test_legacy_lookalike_loader_is_not_owned(self):
        self.write(app.MANIFEST, json.dumps({"provider": "codex", "repository": str(self.repo)}))
        self.write("AGENTS.md", app.legacy_loader(self.codex) + "User addition\n")
        with self.assertRaisesRegex(ValueError, "locally modified"):
            self.install()

    def test_bom_before_first_table_preserved(self):
        merged = app.merge_config('\ufeff[plugins.a]\r\nenabled = true\r\n')
        self.assertTrue(merged.startswith("\ufeff"))
        self.assertTrue(tomllib.loads(merged.lstrip("\ufeff"))["plugins"]["a"]["enabled"])

    def test_single_snapshot_bundle_enforced_after_install(self):
        self.install()
        self.snapshot = self.base / "other-rollback"
        with self.assertRaisesRegex(ValueError, "original snapshot"):
            self.run_cmd("uninstall")

    def test_manifest_cannot_claim_paths_outside_scope(self):
        self.install()
        manifest = self.codex / app.MANIFEST
        data = json.loads(manifest.read_text())
        data["resources"][str(self.base / "unrelated")] = "fake"
        manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "ownership scope"):
            self.run_cmd("uninstall")

    def test_legacy_owned_identical_links_are_removed_on_uninstall(self):
        base_link = self.codex / "agent-base"
        skill_link = self.home / ".agents/skills/ui-ux"
        app.directory_link(base_link, self.repo)
        app.directory_link(skill_link, self.repo / "skills/ui-ux")
        self.write(app.MANIFEST, json.dumps({"provider": "codex", "repository": str(self.repo), "mode": "linked", "managed_agents": {}}))
        self.write("AGENTS.md", app.legacy_loader(self.codex))
        self.run_cmd("setup")
        self.run_cmd("uninstall")
        self.assertFalse(app.present(base_link))
        self.assertFalse(app.present(skill_link))
        self.assertTrue((self.repo / "skills/ui-ux/SKILL.md").is_file())

    def test_unowned_identical_preexisting_links_are_preserved(self):
        base_link = self.codex / "agent-base"
        skill_link = self.home / ".agents/skills/ui-ux"
        app.directory_link(base_link, self.repo)
        app.directory_link(skill_link, self.repo / "skills/ui-ux")
        self.run_cmd("setup")
        self.run_cmd("uninstall")
        self.assertTrue(app.linked_to(base_link, self.repo))
        self.assertTrue(app.linked_to(skill_link, self.repo / "skills/ui-ux"))
        # Remove test-owned junctions before TemporaryDirectory cleans the fixture.
        app.unlink_resource(base_link)
        app.unlink_resource(skill_link)

    def test_validate_rejects_dirty_or_changed_source_revision(self):
        self.install()
        for source in ({"revision": "a" * 40, "dirty": True}, {"revision": "b" * 40, "dirty": False}):
            with self.subTest(source=source), patch.object(app, "git_state", return_value=source):
                with self.assertRaisesRegex(ValueError, "recorded clean installed revision"):
                    self.run_cmd("validate")

    def test_partial_uninstall_retains_edited_skill_ownership_and_retry_finishes(self):
        self.install()
        skill = self.home / ".agents/skills/ui-ux"
        (skill / "SKILL.md").write_text("Edited user skill")
        initial = json.loads((self.codex / app.MANIFEST).read_text())
        with self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
            self.run_cmd("uninstall")
        pending = json.loads((self.codex / app.MANIFEST).read_text())
        self.assertEqual(pending["status"], "partial_uninstall")
        self.assertEqual(pending["initial_transaction"], initial["initial_transaction"])
        self.assertEqual(pending["resources"], {str(skill): initial["resources"][str(skill)]})
        self.assertEqual((skill / "SKILL.md").read_text(), "Edited user skill")
        self.assertFalse((self.codex / "AGENTS.md").exists())
        self.assertNotIn("Uninstalled;", self.output.getvalue())
        transactions = len(self.journals())
        with self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
            self.run_cmd("uninstall")
        self.assertEqual(len(self.journals()), transactions)
        for command in ("setup", "validate"):
            with self.subTest(command=command), self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
                self.run_cmd(command)
        saved = self.base / "saved-user-skill"
        skill.rename(saved)
        # Retry must leave user config edits made after partial removal untouched.
        config = self.codex / "config.toml"
        config.write_text('model = "gpt-6-sol"\nuser_setting = true\n')
        self.run_cmd("uninstall")
        self.assertFalse((self.codex / app.MANIFEST).exists())
        self.assertEqual((saved / "SKILL.md").read_text(), "Edited user skill")
        self.assertEqual(tomllib.loads(app.read_text(config))["model"], "gpt-6-sol")
        self.assertIn("Uninstalled;", self.output.getvalue())

    def test_partial_uninstall_preserves_changed_link_and_target_until_resolved(self):
        self.run_cmd("setup")
        skill = self.home / ".agents/skills/ui-ux"
        alternate = self.base / "custom-skill"
        alternate.mkdir()
        (alternate / "SKILL.md").write_text("Custom link target")
        app.unlink_resource(skill)
        app.directory_link(skill, alternate)
        with self.assertRaisesRegex(ValueError, "PARTIAL uninstall"):
            self.run_cmd("uninstall")
        self.assertTrue(app.linked_to(skill, alternate))
        self.assertEqual((alternate / "SKILL.md").read_text(), "Custom link target")
        self.assertIn(str(skill), json.loads((self.codex / app.MANIFEST).read_text())["resources"])
        self.assertNotIn("Uninstalled;", self.output.getvalue())
        app.unlink_resource(skill)
        app.directory_link(skill, self.repo / "skills/ui-ux")
        self.run_cmd("uninstall")
        self.assertFalse(app.present(skill))
        self.assertFalse((self.codex / app.MANIFEST).exists())
        self.assertTrue((alternate / "SKILL.md").is_file())
        self.assertTrue((self.repo / "skills/ui-ux/SKILL.md").is_file())

    def test_cli_partial_uninstall_exits_two_without_success_claim(self):
        self.install()
        skill = self.home / ".agents/skills/ui-ux/SKILL.md"
        skill.write_text("Edited skill")
        result = app.subprocess.run([app.sys.executable, "-B", app.__file__, "uninstall",
                                     "--provider", "codex", "--home", str(self.home),
                                     "--codex-home", str(self.codex), "--snapshot", str(self.snapshot)],
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("PARTIAL uninstall", result.stderr)
        self.assertNotIn("Uninstalled;", result.stdout + result.stderr)
        self.assertTrue((self.codex / app.MANIFEST).is_file())
        self.assertEqual(skill.read_text(), "Edited skill")

    def test_transaction_failure_restores_prior_state(self):
        self.write("config.toml", 'model = "prior"\n')
        original_restore = app.restore
        failed = False
        def fail_once(path, state):
            nonlocal failed
            if path.name == app.MANIFEST and not failed:
                failed = True
                raise OSError("injected failure")
            original_restore(path, state)
        with patch.object(app, "restore", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "injected"):
                self.install("--config-resolution", "baseline")
        self.assertEqual(app.read_text(self.codex / "config.toml"), 'model = "prior"\n')
        self.assertFalse((self.codex / "AGENTS.md").exists())
        self.assertEqual(json.loads(self.journals()[0].read_text())["status"], "failed")


if __name__ == "__main__":
    unittest.main()
