# Agent Dev Environment

Language for discussing the security boundaries of the development environment.

## Language

**Untrusted agent**:
The AI agent and the programs it runs, whose compliance with instructions is not a security assumption.
_Avoid_: Trusted assistant

**System guard**:
A security boundary enforced independently of the untrusted agent, with policy the agent cannot change.
_Avoid_: Agent instructions as a security boundary

**Shared project workspace**:
The collection of all application projects available to both the agent and the developer, including their local Git histories. Projects within this workspace are not isolated from one another.
_Avoid_: Single-project sandbox
