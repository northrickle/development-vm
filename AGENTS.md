# Repository instructions

Treat this repository as public, regardless of its current visibility.

- Keep Git identity values in the ignored `ansible/group_vars/local.yml`. Preserve existing local values; commit only `local.yml.example` with generic placeholders.
- Never add information identifying the owner or other people: real names, personal email addresses, usernames, hostnames, IP addresses, key fingerprints, or account and project URLs.
- Use generic examples and placeholders in code, documentation, and command output included in changes.
- Never commit private keys, passphrases, passwords, tokens, or local credential files. Do not read private keys or credential files during routine review.
- Keep personal configuration in ignored local files or outside the repository. Use variables and generic example files without personal defaults.
- Manage reproducible Ubuntu configuration in `ansible/tasks/`, imported by `ansible/site.yml`; document manual steps and limitations in `README.md`.
- Leave VM deployment to the human operator, who runs the playbook as `developer` from the reviewed checkout at `/home/developer/dev-environment`. Agents can run local checks that do not deploy changes.
- Keep README documentation at the level of responsibilities, setup, usage, and operational limitations. Omit cosmetic details and implementation walkthroughs already expressed in the playbook.
