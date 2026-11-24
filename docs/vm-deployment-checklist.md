# VM deployment checklist

## Overview

- **Run as:** the human operator, as `developer`, from the reviewed checkout under `/home/developer`.
- **Sequence:** prerequisites → deployment → accounts → internet → applications.
- **Keep available:** the VM console for recovery.
- **Done when:** the checks pass and results are recorded without private values.

The coding agent prepares repository changes and static checks only.

## 1. Before deployment

- [ ] Configure VM networking and host SSH access; the optional [Windows 11 / Hyper-V example](examples/hyper-v-host.md) provides one setup.
- [ ] Review the playbook and ignored local Git identity values.
- [ ] Verify SSH connectivity; keep the VM console available.

## 2. Apply reviewed changes

```bash
cd /home/developer/dev-environment/ansible
ansible-playbook --syntax-check site.yml
ansible-playbook site.yml -K
```

1. Wait for a successful recap.
2. Reconnect to refresh group membership and shell settings.
3. Repeat the playbook with the same configuration.

**Expected:** no changes, unless an upstream Node
patch release became available.

## 3. Check accounts and project workflow

| Check | Expected result |
|---|---|
| `stat -c '%a %U %G' /home/developer` | `700 developer developer` |
| `sudo -u agent test -r /home/developer/dev-environment/README.md` | Fails |
| `id agent` and effective sudo permissions | No sudo or container administration |
| SSH login as `agent` | Denied |
| SSH login as `developer` | Works |
| SSH agent variables inside `agent-run` | Absent |
| `agent-run node --version` | Node 24 |
| `agent-run /home/agent/.local/bin/codex --version` | Native Codex installed for agent |

### Shared Git and launcher

1. Create a disposable project under `/srv/projects` and initialize Git.
2. Create files and commits alternately as both accounts.
3. Check both can edit the other's new files without unsafe-ownership errors.
4. Compare their Git identities locally; keep personal values out of reports.
5. Repeat with pre-existing projects. Correct existing permissions deliberately;
   inherited ACLs apply to new files only.
6. Check launcher arguments containing spaces/quotes, exit status and Ctrl-C.

### User configuration and system packages

- [ ] Both accounts use Bash and share Vim preferences, `EDITOR`/`VISUAL`, history limits, and programmable completion.
- [ ] In fresh interactive shells as `developer` and through `agent-run`, `set -o` reports `vi on`. Type a disposable command, press `Esc`, and verify `b` and `w` move by words; `i` resumes typing.
- [ ] For both accounts, `bind -v` reports `set editing-mode vi`. Existing custom `.inputrc` entries remain present; newly created files also include `/etc/inputrc`.

- [ ] In a disposable Git project, compare fresh interactive shells as `developer` and through `agent-run`: both show the branch, mark uncommitted changes with `*`, shorten long paths, and provide the `ga` alias.

- [ ] `codex-agent` starts Codex without sandbox or approval prompts.
- [ ] `codex-agent`, `claude-agent`, and `agy-agent` use Vim keybindings. Press `Esc` for Normal mode, then `i` for Insert mode.
- [ ] Existing `~/.codex/config.toml`, including multiline instruction strings, is unchanged by the playbook and launcher.
- [ ] System package installation is performed by `developer` with sudo.
- [ ] Agent-owned configuration and project dependency installs do not receive root privileges.

## 4. Check ordinary internet and DNS

Run the commands below as `developer`; `agent-run` executes the target program
as `agent`. Then check the equivalent operations directly as `developer`,
without the launcher:

- [ ] `agent-run curl -I --max-time 10 https://nodejs.org` connects directly.
- [ ] `agent-run curl -I --max-time 10 https://example.org` also connects; no domain approval is needed.
- [ ] Ordinary DNS resolution works through the installed system resolver.
- [ ] npm dependency installs and public Git downloads work without managed proxy settings.
- [ ] Actual project API clients and Codex authentication/model connections work.
- [ ] Localhost and local VM project servers remain reachable.

HTTP responses such as redirects or authorization errors may still demonstrate
successful transport. Check actual application behavior separately.

## 5. Check application access

1. As `developer`, start a temporary server through `agent-run`, which runs it as `agent`:
   `agent-run python3 -m http.server 8765 --bind 0.0.0.0`.
2. From the host, open `http://VM_ADDRESS:8765`.
3. Repeat with the project's actual HTTP/HTTPS server and certificates.
4. Stop the temporary servers.
5. Reboot the VM and verify SSH, internet and application access again.

If access fails, inspect the listener address and existing host/network firewall
settings. This project does not guarantee host-only application access or block
VM connections to other LAN devices.

## 6. Check services and finish

- [ ] SSH keys and tokens used from the VM have access only to development resources.
- [ ] Verify on GitLab and GitHub, wherever the project is hosted, that accounts and tokens used from the VM cannot push directly to the protected `main` branch, bypass its rules, or change them.
- [ ] Non-Git data can be restored from copies outside agent write access.

Record pass/fail results without personal values. End administration with
`sudo -k` and `exit`, following [Operational safety](../SAFETY.md).

## Optional editor example

If using Zed, follow the checks in [the Zed example](examples/zed-editor.md).
These checks are separate from Ubuntu deployment acceptance.
