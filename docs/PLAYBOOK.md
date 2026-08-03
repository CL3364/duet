# Playbook — getting the most out of `/duet`

Everything here is downstream of one idea: **you are the CEO, and you have two
VPs who disagree.** duet is worth its cost exactly when both of them do real
work and you arbitrate. It is worth nothing when one of them narrates while the
other builds.

Read [PROTOCOL.md](../PROTOCOL.md) for *why* the rules are shaped this way.
This file is *how to drive*.

---

## 1. Pick a mission that can actually converge

A section is one mission is one bounded piece of work. The round cap is 8 and
convergence normally lands in 3–6. If you're hitting the cap, the mission was
almost always two missions.

| Good mission | Why |
| --- | --- |
| "Make the ingest retry policy correct under partial network failure" | One behavior, testable, has a right answer |
| "Decide and implement the cache eviction strategy for the session store" | Genuinely contested, evidence can settle it |
| "Get the flaky auth tests green without weakening what they assert" | Sharp acceptance criterion, invites pushback |

| Bad mission | Why |
| --- | --- |
| "Improve the codebase" | Nothing to converge on; scope freeze can't bite |
| "Add the settings page" | No contention — you don't need two models to agree that a form is a form |
| "Refactor the API and add rate limiting and fix the tests" | Three sections. Run three. |

**The tell:** if you can't imagine the two of them disagreeing about it, use a
normal Claude Code session. duet's overhead only pays for itself on contested
work.

---

## 2. `.duet/CONTEXT.md` is the highest-leverage file in the repo

Codex reads your project **cold**. It has none of your conversation, none of
your last three sessions, no idea which of the two competing modules is the
dead one. Everything it doesn't know, it will guess — confidently, in an
`OPEN` item you then have to argue down.

Claude writes CONTEXT.md at section start. Read what it wrote before the first
turn. It should be a brief, never a transcript:

- What you're actually trying to achieve, in your words
- Constraints that aren't visible in the code (deadlines, a migration in
  flight, a customer commitment, an API you can't change)
- **Decisions already made, and why** — this is the part that saves rounds.
  Codex is explicitly instructed to act as consistency auditor and will raise
  contradictions with settled decisions as OPEN items with citations. Give it
  the settled decisions and that power works for you instead of against you.
- Paths and docs that matter, and which ones are dead

If a first round comes back with Codex relitigating something you settled
weeks ago, that's a CONTEXT.md failure, not a Codex failure. Fix the file, and
keep it current — Claude is told to update it whenever a decision changes.

---

## 3. Set territory in the mission itself

The relay enforces the big one: the designer never edits implementation files,
the engineer never edits `DESIGN.md` or `REVIEW.md`. Everything else is yours
to declare, and it holds — say it in the mission and it lands in the prompt:

```
/duet — rework the sync queue. Codex owns src/server and src/shared only:
it must not touch src/client, src/components, or any frontend file, and it
must not git-commit — I'm the sole committer on this branch.
```

Two things worth knowing from real sections:

- **Codex respects file-level territory well** — but it will edit docs and
  spec files widely unless told not to. Review those diffs; they're easy to
  wave through.
- **Codex commits every turn by default** (its prompt tells it to, so evidence
  has a shape). If you're the sole committer on the branch, say so explicitly.

---

## 4. What a good Claude round contains

The failure mode this loop keeps falling into: Codex does all the thinking and
building while Claude forwards step numbers. `SKILL.md` calls a round whose
only Claude output is forwarded progress a **failed round**. You are the one
who notices, so here is the checklist:

Every round, Claude should be doing four things:

1. **Reading the diff itself** — `git diff` and the changed files, not Codex's
   summary of them. Codex's entry is a claim, not a result.
2. **Re-running the evidence.** Codex's `EVIDENCE:` line points at a test log.
   Claude runs that test. "Verified: 263/263 locally" is a contribution.
   "The log shows 263 but the suite skips the integration tier" is a better
   one. Repeating Codex's number back is neither.
3. **Bringing something Codex doesn't have** — a failure case it missed, a
   measurement, a constraint from CONTEXT.md, a competing approach with a
   reason. Claude owns the design, the acceptance criteria, and all the domain
   context Codex can't see.
4. **Naming what changed.** Each entry should say what the two of them now
   agree on *and why it changed*, and what still separates them.

**If a round is just agreement, say so.** "You didn't verify that — run the
test yourself before you agree" is a legitimate and often necessary
instruction. So is "you've agreed with Codex three rounds running; what does
it have wrong?"

---

## 5. A background turn is twenty minutes of your time, not idle waiting

`duet turn` and `duet run` are launched in the background and can run for a
long while. Claude relays *"Codex is on step 3 of 7"* as those arrive — that
is plumbing, not work.

Meanwhile Claude should be: reviewing the previous round's diff, drafting this
round's acceptance checks, verifying last round's claims, or spawning subagents
for a competing draft or an adversarial read. If you see a long quiet stretch
punctuated only by step numbers, redirect it.

Two step-counter facts worth recognizing:

- **"codex is thinking — no step counter yet"** means Codex ignored its plan
  tool this turn. It's honest — the relay refuses to invent progress. Historically
  it happens on roughly a third of turns.
- **Steps can arrive in bursts.** Codex reports its plan in batches, so several
  lines may land at once. The relay fills in the steps it skipped over so you
  see 1, 2, 3, 4, 5 rather than 1 then 5.

---

## 6. Verdicts, and using them on purpose

Every entry ends in exactly one:

- **`SHIP`** — the mission is met, with evidence in hand. Claude should SHIP on
  *its own* verification, never because Codex says the tests pass.
- **`CONTINUE`** — something still separates them. Should name what.
- **`BLOCKED: <reason>`** — evidence cannot settle this; it needs you.

**`BLOCKED` is a feature, not a failure.** A genuine tie escalated to you beats
another round of prose or, worse, two models splitting the difference on a
product decision. If you watch a disagreement go three rounds without new
evidence, tell Claude to force it: "stop arguing, take that to BLOCKED."

Answer a `BLOCKED` by adding your decision to `REVIEW.md` (Claude can do it via
`duet note`), then `duet run --continue`.

`NITS:` exists so style opinions have somewhere to go that can never block a
SHIP. If Codex is blocking on taste, that's what the line is for.

---

## 7. Rounds, freeze, and the caps

- **Round cap 8** (`--rounds`). Hitting it is a *result* — "no convergence" —
  reported to you, not a license to keep going. Interactive mode enforces it
  too; `note` and `turn` refuse once the budget is spent. Only you may raise
  it, by editing `rounds` in `.duet/state.json`.
- **Scope freezes after round 3** (`--freeze`). New `OPEN` items after that
  need a `REGRESSION:` justification plus `EVIDENCE:`. This is what stops the
  late-arriving "one more thought" that turns a 4-round section into a 9-round
  one.
- **No time cap per turn** by default. A single Codex turn can legitimately run
  20+ minutes. Set `--turn-timeout` in seconds if you need one; pacing is meant
  to be bounded by rounds, not clocks.

---

## 8. When to use `duet review` instead of the full loop

The one-shot review is read-only, single-pass, and cheap by comparison. Reach
for it when you want a second pair of eyes rather than a negotiation:

```
/duet review --focus "the new locking in src/queue.py — I care about
correctness under concurrent consumers, not style"
```

The `--focus` line matters. Unfocused, it reviews the latest diff and returns
competent generalities. Focused on a specific worry, it returns findings.

**Point it at code you just wrote.** A live review against fresh code has
repeatedly found real defects that an offline test suite — written by the same
author who wrote the code — missed entirely. Author blind spots are exactly
what an adversarial second model is for.

---

## 9. When *not* to use duet

- **Uncontested work.** A form, a migration, a rename. One model is enough.
- **When you want the Codex history afterwards.** The privacy wipe is the
  point of duet, and it is destructive: the section's Codex context is gone at
  `duet end`. If the work should stay resumable in your Codex history, talk to
  Codex directly.
- **Exploratory "what should we even build" chats.** Take that to a normal
  session, then bring the resulting decision to duet as a mission.

---

## 10. Gotchas that cost real time

**Relay bounce on reused `OPEN` ids.** Item ids are relay-assigned. If Codex
tries to `CLOSE` and re-raise a still-contested item under its original id, the
entry bounces (`already used; next available id is OPEN-18`) and, after two
tries, the turn fails. The damage is asymmetric and easy to miss: **the code
changes are already on disk, but no entry was recorded and no verdict counted.**
To keep contesting an item, leave it open — don't close and re-raise. Genuinely
new findings get fresh ids.

**Background turns die on session limits.** A long section can outlive your
Claude usage window. On resume, always `git status` first — there will be
partial writes — and re-dispatch with an "audit the partial work, then finish
it" brief rather than restarting the round from scratch.

**Codex's sandbox is narrower than yours.** It commonly can't bind a local
listener (EPERM) and has no CA trust for tools that fetch over TLS. The pattern
that works: run the browser tests, the acceptance script, and the strict
security gate on your side, and feed the results back as `EVIDENCE:` lines.
Codex runs the type-checker and unit tests itself. `--codex-net` opens network
access inside the sandbox when it genuinely needs npm or pip.

**Stale Codex session after an interruption.** If a turn fails with `no rollout
found for thread id`, clear `codex_session` in `<repo>/.duet/state.json` and
re-run `duet turn`. A fresh session re-reads the war-room files; nothing
durable is lost — that's the point of keeping state in files.

**A bounced entry auto-retries once.** When it does, treat the retry's content
as authoritative; the bounced draft is not in `REVIEW.md`.

**Concurrent sections are safe.** Wipes are surgical — only the ending
section's Codex session — and the full sweep runs when the last active section
ends.

---

## 11. A worked shape

What a healthy 4-round section looks like from the outside:

```
R1  DESIGNER   Design + acceptance criteria. OPEN-1: retry budget is unspecified
               under partial failure — what's the ceiling?
               VERDICT: CONTINUE
R1  ENGINEER   Implemented exponential backoff, capped at 5. OPEN-2: the
               design's idempotency assumption doesn't hold for the batch
               endpoint — src/ingest/batch.py:88.
               EVIDENCE: .duet/logs/r1-tests.txt (41/41)
               VERDICT: CONTINUE
R2  DESIGNER   Verified 41/41 locally. OPEN-2 is real; batch was out of scope
               in DESIGN.md and shouldn't have been. Scoping it out explicitly.
               CLOSE OPEN-1 — ceiling is 5, matching the upstream SLA.
               EVIDENCE: docs/sla.md:14
               VERDICT: CONTINUE
R2  ENGINEER   CLOSE OPEN-2 — batch excluded, guard added at batch.py:91.
               EVIDENCE: .duet/logs/r2-tests.txt (43/43)
               VERDICT: SHIP
R3  DESIGNER   Re-ran 43/43 and read the guard; it fails closed, which is
               right. NITS: the log line at batch.py:94 buries the reason.
               VERDICT: SHIP
                                    → dual SHIP, zero open items, section over
```

Note what isn't there: no "great point", no restating, no agreement about
things already agreed. Silence is agreement — that's a protocol rule, and it's
why the transcript is short enough to actually read six months later.
