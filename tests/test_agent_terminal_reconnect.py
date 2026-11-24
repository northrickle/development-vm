"""Exercise terminal reconnects with real tmux and a harmless Codex stand-in."""

import json
import os
from pathlib import Path
import pty
import shutil
import subprocess
import tempfile
import time
import unittest


@unittest.skipUnless(shutil.which("tmux"), "tmux is required")
class TerminalReconnectTest(unittest.TestCase):
    def test_reconnect_preserves_process_and_separate_sessions(self):
        for tool in ['codex', 'claude', 'agy']:
            with self.subTest(tool=tool):
                self.check_reconnect(tool)

    def check_reconnect(self, tool):
        with tempfile.TemporaryDirectory(prefix="codex-terminal-test-") as directory:
            root = Path(directory)
            socket = str(root / "tmux.sock")
            tmux = ["tmux", "-S", socket]
            source = Path(__file__).resolve().parents[1] / "ansible/files/agent-session-tmux"
            launcher = root / "launcher"
            launcher.write_text(source.read_text().replace("/home/agent/.local/bin/codex", str(root / "codex")).replace("/home/agent/.local/bin/claude", str(root / "codex")).replace("/home/agent/.local/bin/agy", str(root / "codex")).replace(
                'tmux -L "$launcher" -f /dev/null', f"tmux -S '{socket}' -f /dev/null"
            ))
            fake = root / "codex"
            fake.write_text(
                "#!/usr/bin/python3\n"
                "import json, os, sys, time\n"
                "with open(os.environ['TEST_STARTS'], 'a') as out:\n"
                " out.write(json.dumps([os.getpid(), os.getcwd(), sys.argv[1:]]) + '\\n')\n"
                " out.flush()\n"
                "while True: time.sleep(1)\n"
            )
            fake.chmod(0o700)
            starts = root / "starts.jsonl"
            env = dict(os.environ, HOME=str(root), XDG_STATE_HOME=str(root / "state"),
                       TERM="xterm-256color",
                       PATH=str(root) + ":" + os.environ["PATH"], TEST_STARTS=str(starts))
            env.pop("TMUX", None)
            project = root / "project with ' quotes, #{session_name} and ##"
            project.mkdir()
            other = root / "worktree"
            other.mkdir()
            clients = []

            def command(*args):
                return subprocess.check_output(tmux + list(args), text=True,
                                               stderr=subprocess.DEVNULL).strip()

            def client_session(pid):
                try:
                    for line in command("list-clients", "-F", "#{client_pid} #{session_name}").splitlines():
                        client_pid, session = line.split()
                        if client_pid == str(pid):
                            return session
                except subprocess.CalledProcessError:
                    pass
                return None

            def wait_for(predicate):
                deadline = time.monotonic() + 8
                while time.monotonic() < deadline:
                    if predicate():
                        return
                    time.sleep(0.05)
                self.fail("Timed out waiting for tmux state")

            def records():
                return [json.loads(line) for line in starts.read_text().splitlines()] if starts.exists() else []

            def attach(folder, name, *args):
                master, slave = pty.openpty()
                proc = subprocess.Popen(["bash", str(launcher), tool, str(folder), name, *args],
                                        stdin=slave, stdout=slave, stderr=slave, env=env)
                os.close(slave)
                clients.append((proc, master))
                wait_for(lambda: proc.poll() is not None or client_session(proc.pid))
                self.assertIsNone(proc.poll(), "tmux client exited before attaching")
                self.assertTrue(client_session(proc.pid).endswith("-" + name))
                return proc

            def listing(folder):
                return subprocess.check_output(
                    ["bash", str(launcher), tool, str(folder), "list"], env=env, text=True)

            try:
                self.assertIn("No active sessions.", listing(project))
                self.assertEqual(records(), [])
                first = attach(project, "main", "--model", "example model")
                second = attach(project, "review")
                wait_for(lambda: len(records()) == 2)
                main_session = client_session(first.pid)
                review_session = client_session(second.pid)
                self.assertNotEqual(main_session, review_session)
                self.assertEqual(command("show-options", "-gv", "mouse"), "on")
                main_style = command("show-options", "-t", main_session, "-v", "status-style")
                self.assertEqual(main_style, command(
                    "show-options", "-t", review_session, "-v", "status-style"))
                self.assertEqual(command("show-options", "-t", main_session,
                                         "-v", "status-left"), project.name)
                self.assertEqual(command("show-options", "-t", main_session,
                                         "-v", "status-right"), "main")
                original = records()
                self.assertEqual(original[0][1], str(project))
                expected = [
                    "--no-daemon", "--sandbox", "danger-full-access", "--ask-for-approval", "never",
                    "-c", "tui.vim_mode_default=true", "-C", str(project),
                    "--model", "example model",
                ]
                if tool == 'claude':
                    expected = [
                        '--settings', '{"editorMode":"vim"}',
                        '--model', 'example model',
                    ]
                elif tool == 'agy':
                    expected = [
                        '--settings', '{"editorMode":"vim","vimInsertFirst":false}',
                        '--model', 'example model',
                    ]
                self.assertEqual(original[0][2], expected)

                # Simulate losing the terminal transport, without exiting Codex.
                first_master = clients[0][1]
                os.close(first_master)
                clients[0] = (first, None)
                first.wait(timeout=8)
                wait_for(lambda: client_session(first.pid) is None)
                command("set-option", "-g", "mouse", "off")
                resumed = attach(project, "main")
                self.assertEqual(command("show-options", "-gv", "mouse"), "on")
                self.assertEqual(client_session(resumed.pid), main_session)
                self.assertEqual(command("show-options", "-t", main_session,
                                         "-v", "status-style"), main_style)
                self.assertEqual(records(), original)
                for pid, _, _ in original:
                    os.kill(pid, 0)
                self.assertEqual(client_session(second.pid), review_session)

                # A complete SSH disconnect loses both clients at once.
                for index in (1, 2):
                    proc, master = clients[index]
                    os.close(master)
                    clients[index] = (proc, None)
                    proc.wait(timeout=8)
                    wait_for(lambda: client_session(proc.pid) is None)
                resumed = attach(project, "main")
                attach(project, "review")
                self.assertEqual(records(), original)

                other_client = attach(other, "main")
                wait_for(lambda: len(records()) == 3)
                self.assertEqual(records()[-1][1], str(other))
                self.assertNotEqual(main_style, command(
                    "show-options", "-t", client_session(other_client.pid), "-v", "status-style"))
                self.assertEqual(listing(project).splitlines()[1:], ["  main", "  review"])
                self.assertEqual(listing(other).splitlines()[1:], ["  main"])
                self.assertEqual(len(records()), 3)
                self.assertEqual(client_session(resumed.pid), main_session)
                self.assertNotEqual(client_session(other_client.pid), main_session)

                # Saved project colors survive loss of the entire tmux server.
                command("kill-server")
                for proc, _ in clients:
                    proc.wait(timeout=8)
                restarted = attach(project, "main")
                self.assertEqual(command("show-options", "-t", client_session(restarted.pid),
                                         "-v", "status-style"), main_style)
            finally:
                subprocess.run(tmux + ["kill-server"], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=False)
                for proc, master in clients:
                    if master is not None:
                        os.close(master)
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.terminate()
                        proc.wait(timeout=3)

if __name__ == "__main__":
    unittest.main()
