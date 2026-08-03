# Glossary

The vocabulary duet uses in its code, prompts, docs and transcripts. One term,
one meaning. If a word here starts meaning two things, that is a bug in the
language before it is a bug in the code.

This file is a glossary only. It holds no design decisions (those are in
[PROTOCOL.md](PROTOCOL.md) and `docs/adr/`) and no implementation detail.

---

**Section** — one mission, one bounded piece of work, start to finish. The unit
that begins with `duet start` or `duet run` and ends in an outcome. Sections do
not overlap within a repo.

**Mission** — the one-sentence statement of what a section is for. Fixed at
section start; changing it means starting a different section.

**Round** — one designer turn followed by one engineer turn. Rounds are counted
and capped; the cap is a budget on *exchanges*, never on time.

**Turn** — one model's half of a round. A turn ends when exactly one entry has
been produced.

**Entry** — the single reviewable artifact a turn produces. Prose plus
structured lines, ending in exactly one verdict. Entries are the only thing
that crosses between the two sides.

**Verdict** — how an entry ends. Exactly one of **SHIP** (mission met, with
evidence), **CONTINUE** (something still separates the two sides), or
**BLOCKED** (evidence cannot settle it; a human must decide).

**Dual SHIP** — both sides SHIP with no open items. The only outcome that means
convergence rather than exhaustion.

**Open item** — a numbered contention raised in an entry. Owned by whoever
raised it: only its raiser may close it, and only with evidence. Ids are
assigned by the relay and never reused.

**Evidence** — something a second party can re-run or look up: a test log path,
a measurement, a specification or `file:line` reference. An assertion of
changed opinion is not evidence.

**Bounce** — the relay rejecting a non-conformant entry and asking for a
corrected one. A bounce is a protocol event, not a model failure.

**Scope freeze** — the round after which new open items require an explicit
regression justification plus evidence.

**Designer** — the role that owns intent: the vision, the interfaces, the
acceptance criteria, and the domain context the engineer cannot see. Played by
the live Claude Code session, or by a headless Claude in background mode.

**Engineer** — the role that owns implementation: source, tests, build files.
Played by the Codex CLI. Also acts as consistency auditor over the designer's
claims.

**Territory** — the boundary between the roles. The designer does not edit
implementation files; the engineer does not edit the design or the transcript.
Requests across the boundary travel as open items rather than as edits.

**Relay** — the program between the two sides. It enforces the protocol
mechanically, appends every entry to the transcript, and is the only writer of
that transcript. Neither model writes it directly.

**War room** — the per-repo directory holding a section's durable state: the
design, the brief, the transcript, and the evidence logs. Survives the wipe by
design; it is the only lasting record of a section.

**Brief** — the designer-written distillation of everything the engineer cannot
see: the goal in the user's words, constraints, and decisions already made.
A brief, never a transcript.

> **Naming collision, deliberate.** The brief is stored as `.duet/CONTEXT.md`,
> which is *not* this file. This file is the project's glossary; the brief is a
> per-section input written for the engineer and discarded with the section.
> They share a filename and nothing else.

**Duet home** — the isolated Codex home a section runs against. Never the
user's own Codex state, which duet reads once for credentials and never writes.

**Wipe** — the destruction of a section's Codex sessions and history at section
end, on any outcome including a crash. Credentials and configuration survive;
conversation-derived state does not.

**Step counter** — the only signal that escapes a turn in flight: which numbered
step of its own plan the engineer is on. Never its reasoning, never its output.
A turn that opens no plan has no honest counter, and the relay stays silent
rather than inventing one.

**Trigger** — a phrase that should cause the skill to load. Triggers live in the
skill's description and are exercised in
[references/trigger-tests.md](references/trigger-tests.md).
