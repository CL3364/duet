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

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-repo-is-the-skill-folder.md) | The repository is the skill folder | Accepted |
| [0002](0002-sessions-are-wiped-at-section-end.md) | Codex sessions are destroyed at every section end | Accepted |
| [0003](0003-driver-liveness-via-file-lease.md) | Driver liveness is a file lease, not process inspection | Accepted |
