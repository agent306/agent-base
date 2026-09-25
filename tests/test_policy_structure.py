"""Structural/discovery fixtures; these do not certify model behavior."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('policy_bootstrap', ROOT/'bootstrap/agent_base.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PolicyStructureTests(unittest.TestCase):
    def test_flat_payload_is_small_and_optional_paths_resolve(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)/'.codex'
            text = module.generated(home).decode()
            self.assertLessEqual(len(text.split()), 800)
            self.assertLess(len(text.encode()), 32768)
            self.assertNotIn('{{BASE}}', text)
            self.assertEqual(text.count('# Working agreements'), 1)
            self.assertEqual(text.count('# Codex adapter'), 1)
            paths = re.findall(r'`([^`]+)`', text)
            for path in paths:
                relative = Path(path).relative_to(home/'agent-base')
                self.assertTrue((ROOT/relative).is_file(), relative)

    def test_legacy_policy_and_pins_are_not_distributed(self):
        self.assertFalse((ROOT/'profiles/codex/routing.md').exists())
        self.assertEqual(list((ROOT/'profiles/codex/agents').glob('*.toml')), [])
        self.assertNotIn('Read `', (ROOT/'profiles/codex/AGENTS.md').read_text())

    def test_shared_skill_does_not_require_personal_install(self):
        text = (ROOT/'skills/ui-ux/SKILL.md').read_text()
        self.assertIn('works independently', text)
        self.assertNotIn('CODEX_HOME', text)
        self.assertNotIn('D:/', text)
        self.assertNotIn('C:/Users/', text)


if __name__ == '__main__':
    unittest.main()
