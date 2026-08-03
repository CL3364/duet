# Architecture decision records

Decisions that would otherwise look arbitrary — or wrong — to someone reading
the code cold.

A decision earns a record here only when all three are true: it is **hard to
reverse**, it is **surprising without context**, and it was a **real trade-off**
with genuine alternatives. Everything failing that bar lives closer to the code:
the protocol's reasoning is in [PROTOCOL.md](../../PROTOCOL.md), the vocabulary
in [CONTEXT.md](../../CONTEXT.md), and the day-to-day guidance in
[PLAYBOOK.md](../PLAYBOOK.md).

Records are immutable once accepted. A decision that changes gets a new record
that supersedes the old one; the original stays as written.

| Decision | Status | Date |
| --- | --- | --- |
| [The repository is the skill folder](repo-is-the-skill-folder.md) | Accepted | 2026-08-03 |
| [Codex sessions are destroyed at every section end](sessions-are-wiped-at-section-end.md) | Accepted | 2026-08-03 |
| [Driver liveness is a file lease, not process inspection](driver-liveness-via-file-lease.md) | Accepted | 2026-08-03 |
