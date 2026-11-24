#!/usr/bin/env python3
"""Check that agent-controlled home paths are never modified as root."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class SecurityChecks(unittest.TestCase):
    def test_agent_home_operations_run_as_agent(self):
        checked = 0
        for path in (ROOT / 'ansible/tasks').glob('*.yml'):
            for task in yaml.safe_load(path.read_text()):
                for module in ('file', 'blockinfile', 'copy', 'template', 'git'):
                    args = task.get('ansible.builtin.' + module, {})
                    target = args.get('path', args.get('dest', ''))
                    if target.startswith('/home/{{ development_account }}/'):
                        checked += 1
                        with self.subTest(task=task['name']):
                            self.assertEqual(task.get('become_user'), '{{ development_account }}')
                    elif target.startswith('/home/agent/'):
                        checked += 1
                        with self.subTest(task=task['name']):
                            self.assertEqual(task.get('become_user'), 'agent')
        self.assertGreater(checked, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
