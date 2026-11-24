# Operational Safety

## Overview

- **Use this guide:** before project work, publication, administration or recovery.
- **Start with:** the five rules below, then pick the checklist for your task.
- **Deployment and tests:** use [VM deployment checklist](docs/vm-deployment-checklist.md).
- **Responsibility:** these checklists guide the operator; Ansible does not enforce every item.

## Five Rules to Remember

1. **No production credentials in the VM.** Neither account gets them.
2. **Run project code as `agent`.** Keep its account without sudo.
3. **Assume `developer` can be compromised.** Limit credentials at the service.
4. **Review before sudo or publication.** Use the trusted infrastructure checkout.
5. **Keep recovery outside the VM.** Verify that restoration works.

```text
Host -- SSH --> developer -- launch --> agent
                  |                     |
                  |                     +--> Dependencies, tests, applications
                  +--> Review, Git publication, human administration

Production access --> Separate environment outside this VM
```

## Pick Your Task

| I am about to… | Checklist |
|---|---|
| Work on a project | [Project work](#project-work) |
| Commit, push, or merge | [Git](#git) |
| Run Ansible or sudo | [Administration](#administration) |
| Add a credential | [Credentials](#credentials) |
| Configure a service | [Service permissions](#service-permissions) |
| Expose an application or change networking | [Network access](#network-access) |
| Prepare for data loss | [Backups](#backups) |
| Respond to suspected compromise | [Recovery](#recovery) |

## Project Work

- [ ] Run installs, tests, builds, and servers as `agent`.
- [ ] Keep unrelated private data outside the shared workspace.
- [ ] Keep credentials out of source, prompts, logs, and tracked configuration.

**Remember:** the agent can change or delete every shared project. Dependency installs can execute code.

## Git

- [ ] Review changes before publishing or merging.
- [ ] Treat local hooks and repository configuration as untrusted.
- [ ] Keep an independent backup; local commits alone are insufficient.

**Accepted risk:** Git run as `developer` may execute agent-controlled code with developer permissions. A source diff does not cover local hooks or `.git/config`.

## Administration

1. Connect as `developer`; launch coding agents as `agent`.
2. Use a separate administrative terminal, without project code or hooks.
3. Review playbooks, scripts, and inputs before granting elevated privileges.
4. Run Ansible from the trusted checkout outside agent write access.
5. Run `sudo -k` to clear cached sudo authentication for that session.
6. End the administrative session with `exit`. Open a fresh session for project work.

**Keep sudo password-protected.** Do not add passwordless sudo for convenience.

```text
Administrative session --> Reviewed sudo operations --> sudo -k --> exit
Project work           --> Fresh session             --> Run code as agent
```

Closing a window or disconnecting from a persistent terminal does not necessarily end its session. End the administrative shell explicitly.

<details>
<summary>Why end the session, and what are the limits?</summary>

With the default per-terminal sudo cache, authentication is tied to the terminal session. Ending that session prevents a new login from reusing its cached authentication. A global cache has different behavior; do not assume that logout clears authentication in every configuration. See the [sudo timestamp documentation](https://manpages.ubuntu.com/manpages/noble/man5/sudoers_timestamp.5.html).

Modified shell configuration or administrative inputs can affect later sudo operations. A sudo password and a separate terminal reduce exposure; they do not restore trust in the account.

</details>

## Credentials

- [ ] Use credentials restricted to development resources and operations.
- [ ] Keep repository credentials with `developer`, outside shared projects.
- [ ] Protect private SSH keys with passphrases.
- [ ] Keep production, service administration, and recovery access outside the VM.

**Never store, load, or forward production credentials into the VM.**

- `developer` may use `ssh-add` and keep keys unlocked in its SSH agent during work.
- Do not explicitly share that SSH agent's socket with the `agent` account. This preserves the basic separation between accounts.
- **Accepted risk:** code that gains execution as `developer` can use its unlocked SSH agent. Account separation does not guarantee protection against this path.

<details>
<summary>Limit: a passphrase does not protect an unlocked SSH agent</summary>

The SSH agent is the program holding unlocked keys. Its socket lets programs request authentication without reading private key files. A passphrase protects the stored key, but does not prevent code running as `developer` from using an already unlocked key.

</details>

## Service Permissions

- [ ] Protect the main branch against direct pushes from VM-held credentials.
- [ ] Ensure those identities cannot disable or bypass branch protection.
- [ ] Review changes through the server's merge workflow.
- [ ] Prevent irreversible service data loss through permissions and recovery controls.

**Verify effective permissions.** A token's name or intended use is insufficient. These controls are configured in the services, outside this playbook.

## Network Access

- [ ] Verify the VM network setup; [Windows 11 / Hyper-V](docs/examples/hyper-v-host.md) is an optional NAT example.
- [ ] Bind applications only to intended interfaces and check who can reach them.
- [ ] Keep credentials and administrative capabilities out of agent-accessible services.

This project adds no firewall rules, domain filtering or protection against
attacks on LAN devices. NAT does not provide that isolation. Network protection
against untrusted code is a separate workstation/network concern.

## Backups

- [ ] Keep recovery copies outside agent write access.
- [ ] Include service data that Git does not contain.
- [ ] Verify restoration before relying on a backup.

## Recovery

1. Stop agent workloads.
2. From a trusted environment, revoke exposed credentials in affected services.
3. Inspect remote changes and access logs.
4. Rebuild the VM if the account or administrative environment cannot be trusted.
5. Load replacement credentials only after establishing a trusted environment.

**Removing one suspicious hook does not establish that the account is safe.**

## Scope of This Guide

- These are operator responsibilities, not guarantees enforced by Ansible.
- See [Security and limitations](README.md#security-and-limitations) for the protections the playbook provides and their limits.
