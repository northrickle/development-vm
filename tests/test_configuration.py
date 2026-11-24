#!/usr/bin/env python3
"""Repository-only checks. Never run Ansible, system services or firewall commands."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / 'ansible/files'


class ConfigurationChecks(unittest.TestCase):
    def test_yaml_and_task_references(self):
        paths = list((ROOT / 'ansible/tasks').glob('*.yml'))
        paths += [ROOT / 'ansible/site.yml',
                  ROOT / 'ansible/group_vars/local.yml.example']
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsNotNone(yaml.safe_load(path.read_text()))
        site = yaml.safe_load((ROOT / 'ansible/site.yml').read_text())[0]
        for task in site['tasks']:
            reference = task.get('ansible.builtin.import_tasks',
                                 task.get('ansible.builtin.include_tasks'))
            self.assertTrue((ROOT / 'ansible' / reference).is_file())

    def test_terminal_dispatch_and_help(self):
        with tempfile.TemporaryDirectory() as temp:
            stub = Path(temp) / 'agent-run'
            stub.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            stub.chmod(0o755)
            env = dict(os.environ, PATH=temp + ':' + os.environ['PATH'])
            env.pop('TMUX', None)
            for tool in ['codex', 'claude', 'agy']:
                base = ['bash', str(FILES / 'agent-terminal'), tool]
                for args in [[], ['list'], ['main', '--example', 'two words']]:
                    output = subprocess.check_output(base + args, cwd=temp, env=env, text=True)
                    self.assertEqual(json.loads(output.splitlines()[0]),
                                     ['/usr/local/libexec/agent-session-tmux', tool, temp,
                                      *(args or ['list'])])
                for flag in ['help', '-h', '--help']:
                    output = subprocess.check_output(base + [flag], cwd=temp, env=env, text=True)
                    self.assertIn(f'Usage: {tool}-agent', output)
                result = subprocess.run(base + ['main'], cwd=temp,
                                        env=dict(env, TMUX='example'), text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn('outside tmux', result.stderr)
                self.assertEqual(result.stdout, '')
                wrapper = (FILES / f'{tool}-agent').read_text().replace(
                    '/usr/local/libexec/agent-terminal', str(FILES / 'agent-terminal'))
                local = Path(temp) / 'wrapper'
                local.write_text(wrapper)
                output = subprocess.check_output(['bash', str(local), 'main'], cwd=temp, env=env, text=True)
                self.assertEqual(json.loads(output)[1], tool)

    def test_launcher_preserves_argv_and_directory(self):
        # Stub sudo: record arguments without invoking privilege changes or /etc files.
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp) / 'project with spaces'
            directory.mkdir()
            sudo = Path(temp) / 'sudo'
            sudo.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n')
            sudo.chmod(0o755)
            env = dict(os.environ, PATH=temp + ':' + os.environ['PATH'])
            args = ['printf', '%s', 'space argument', '$(false)', ';exit 1', 'quote"']
            result = subprocess.check_output(
                ['bash', str(FILES / 'agent-run'), *args], cwd=directory, env=env, text=True)
            recorded = json.loads(result)
            self.assertEqual(recorded[:6], ['-u', 'agent', '-H', '--', '/bin/bash', '-c'])
            self.assertEqual(recorded[7:], ['agent-run', str(directory), *args])

    def test_managed_bash_syntax(self):
        tasks = yaml.safe_load((ROOT / 'ansible/tasks/shell-account.yml').read_text())
        for task in tasks:
            settings = task.get('ansible.builtin.blockinfile', {})
            if not settings.get('path', '').endswith('/.bashrc'):
                continue
            block = settings['block']
            subprocess.run(['bash', '-n'], input=block, text=True, check=True)

    def test_shell_and_readline_enable_vi(self):
        tasks = yaml.safe_load((ROOT / 'ansible/tasks/shell-account.yml').read_text())
        with tempfile.TemporaryDirectory() as temp:
            bashrc = Path(temp) / '.bashrc'
            inputrc = Path(temp) / '.inputrc'
            bash_blocks = []
            for task in tasks:
                settings = task.get('ansible.builtin.blockinfile', {})
                if settings.get('path', '').endswith('/.bashrc'):
                    bash_blocks.append(settings['block'])
                elif settings.get('path', '').endswith('/.inputrc'):
                    inputrc.write_text(settings['block'])
            bashrc.write_text('\n'.join(bash_blocks))
            env = dict(os.environ, HOME=temp, INPUTRC=str(inputrc))
            # Disable history writes and avoid loading any real account configuration.
            subprocess.check_call(
                ['bash', '--noprofile', '--norc', '-c',
                 'source "$1"; [[ -o vi ]]', 'check', str(bashrc)],
                env=env, text=True)
            output = subprocess.check_output(
                ['bash', '--noprofile', '--norc', '-i', '-c',
                 'HISTFILE=/dev/null; bind -v'],
                env=env, text=True, stderr=subprocess.PIPE)
            self.assertIn('set editing-mode vi', output)

    def test_node_update_selects_latest_24_lts_and_is_repeatable(self):
        tasks = yaml.safe_load((ROOT / 'ansible/tasks/node.yml').read_text())
        script = next(t['ansible.builtin.shell'] for t in tasks
                      if 'ansible.builtin.shell' in t)
        with tempfile.TemporaryDirectory() as temp:
            nvm_dir = Path(temp)
            (nvm_dir / 'alias').mkdir()
            stub = nvm_dir / 'nvm.sh'
            stub.write_text('nvm() {\n  case "$1" in\n    current) cat "$TEST_NVM/current" 2>/dev/null || { echo none; return 3; } ;;\n    install)\n      [[ "$2" == 24 ]] || return 1\n      echo v24.1.0 > "$TEST_NVM/current"\n      ;;\n    alias) printf \'%s\\n\' "$3" > "$TEST_NVM/alias/default" ;;\n    *) return 1 ;;\n  esac\n}\n')
            script = script.replace('/home/agent/.nvm', temp)
            env = dict(os.environ, TEST_NVM=temp)
            for initial in [None, 'v24.0.0']:
                for path in [nvm_dir / 'current', nvm_dir / 'alias/default']:
                    if initial:
                        path.write_text(initial + '\n')
                    else:
                        path.unlink(missing_ok=True)
                result = subprocess.check_output(['bash', '-c', script], env=env, text=True)
                self.assertIn('NODE_CHANGED', result)
                self.assertEqual((nvm_dir / 'alias/default').read_text().strip(), 'v24.1.0')
                result = subprocess.check_output(['bash', '-c', script], env=env, text=True)
                self.assertNotIn('NODE_CHANGED', result)

    def test_shell_syntax(self):
        for name in ['agent-run', 'codex-agent', 'agent-session-tmux', 'agent-terminal', 'agy-agent', 'claude-agent']:
            subprocess.run(['bash', '-n', str(FILES / name)], check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
