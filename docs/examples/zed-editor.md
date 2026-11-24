# Using Zed with the development VM

Use Zed on the host to edit a project inside Ubuntu and run the agent launchers
in remote terminals. This optional example assumes working `ssh vm` access and
a project under `/srv/projects`. Editor configuration is outside the playbook's scope.

## Connect

On the host, using your normal desktop account:

1. Install Zed.
2. Open **Remote Projects → Connect New Server** and connect with `ssh vm`.
3. Open `/srv/projects/first-project`.
4. In a remote terminal, run `codex-agent main`, `claude-agent main`, or `agy-agent main`.

See [Zed Remote Development](https://zed.dev/docs/remote-development) for editor setup details.

## Verify

- [ ] The remote project opens and files can be edited.
- [ ] A remote terminal runs in the project directory as `developer`.
- [ ] An agent launcher starts or reconnects to its tmux session.
