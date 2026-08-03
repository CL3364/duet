## Driver liveness is a file lease, not process inspection

Date: 2026-08-03

### Status

Accepted

### Context

`duet progress --follow` tails a section's step counter and must exit when that
section's driver is gone — not when *any* duet process is gone, or a concurrent
section would hold the follower open forever, and not early, or the user stops
seeing progress mid-turn.

The original implementation asked the operating system about the pid recorded in
each progress record: `os.kill(pid, 0)` to test existence, then `ps` to
distinguish a live process from a zombie and to confirm the pid had not been
reused by something else.

That has a failure mode which is invisible until you hit it. A driver that has
exited but has not yet been reaped by its parent is a **zombie**, and a zombie
still accepts signal 0 — so `os.kill` reports it alive. `ps` is then the only
thing that can tell the difference. When `ps` cannot be executed, the code
answered "cannot tell, keep following," and the follower never terminated.

This was not hypothetical. It was found when duet audited its own repository:
the sandbox running the audit denied `ps`, five suites passed, and the
integration test hung until its 180-second cap. An earlier attempt to reproduce
it by removing `ps` from `PATH` *passed*, because the child had already been
reaped and `os.kill` short-circuited before reaching `ps` at all — the bug only
appears in the narrow window where the process is dead, unreaped, and `ps` is
unavailable.

A bounded timeout was considered and rejected: any fixed grace is either long
enough to strand the user or short enough to cut off a legitimately slow turn,
and neither answers the actual question.

### Decision

Each driver opens a section-scoped lock file and holds a **shared** `flock` on it
for its entire process lifetime. The follower probes for an **exclusive** lock,
non-blocking: if the probe fails, a driver is alive; if it succeeds, none is.

The lock file is never unlinked. Its presence is not the signal — the kernel's
release of the lock is.

Drivers take a shared lock rather than exclusive so that concurrent drivers on
the same section keep the monitor alive, and so a follower's momentary probe can
never prevent a driver from starting.

Sections whose logs predate the lease fall back to the old pid inspection, now
bounded by a finite grace instead of waiting forever.

### Consequences

**What this buys.** The kernel releases file locks on process death
unconditionally — including `SIGKILL`, including while the process is still an
unreaped zombie, and including a crash that runs no cleanup code. That is
precisely the question `ps` was being asked, answered by a mechanism that cannot
be denied by a sandbox and cannot be confused by pid reuse.

**What it costs.** `fcntl.flock` is POSIX-only, which formalises the existing
macOS-and-Linux support boundary. A stray lock file per section is left on disk
by design; deleting it is harmless but pointless.

**The lesson worth keeping.** The offline suite that missed this was written by
the same author as the code under test, and passed. It took an adversarial run
in a *differently constrained environment* to surface it — and the first attempt
to reproduce it failed for an unrelated reason, which nearly buried the finding
a second time. When a failure cannot be reproduced, the reproduction is suspect
before the report is.
