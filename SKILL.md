---
name: duet
description: Pairs your Claude Code session with OpenAI's Codex CLI as design and engineering peers that argue to common ground on evidence, then reports what they settled and what deadlocked. Use when the user says "duet", asks to pair with or bridge to Codex/GPT, wants a second AI model to adversarially review a design, plan, or diff ("have GPT check this", "get a second opinion on this migration"), or wants two models argued to consensus instead of one model's answer. Codex runs in an isolated home that is wiped after each section. Not for ordinary single-model coding, and not when the work should stay resumable in your Codex history.
license: MIT
compatibility: Requires Claude Code with the `claude` CLI on PATH, the OpenAI Codex CLI (version 0.144 or newer) signed into an OpenAI account, Python 3.9+, and macOS or Linux. Needs no network access of its own; both models bill to the user's own subscriptions.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
metadata:
  author: CL3364
  version: 1.0.0
  homepage: https://github.com/CL3364/duet
  tags: [code-review, multi-agent, codex, adversarial-review]
---

# duet — Claude designs, Codex engineers

Two peers, one war room, mechanical guards. Both sides do real work; the
loop runs until they reach common ground on evidence, not until one side
finishes building. All commands via
`~/.claude/skills/duet/bin/duet`. Read `PROTOCOL.md` in this directory before
your first section; you (the live Claude session) are bound by the same
output contract as the headless models — `duet note` will bounce your entry
if it violates it.

## Prerequisites (once)

```bash
~/.claude/skills/duet/bin/duet init     # builds ~/.duet/codex-home, copies auth from ~/.codex
~/.claude/skills/duet/bin/duet status   # verify "ready"
```

`status` prints the exact remediation when auth is missing: `duet init` if
credentials are available in `~/.codex`, otherwise a direct login command for
the isolated home. Browser login belongs to the user — surface that command,
don't try to complete it for them. A direct login looks like:

```bash
CODEX_HOME=~/.duet/codex-home codex login
```

`duet init` seeds the isolated codex home's model from `~/.codex/config.toml`
when one exists, else `gpt-5.6-sol`; `DUET_CODEX_MODEL` overrides per run.

## Interactive mode (you are the designer, live)

1. `duet start --mission "<one sentence>" --repo <dir>`
2. Write `<dir>/.duet/CONTEXT.md` first: distill what Codex can't see — the
   user's goal from this conversation, constraints, decisions already made
   and why, relevant paths/docs. A brief, never a transcript (privacy +
   density). Then write/refresh `<dir>/.duet/DESIGN.md`. Spawn Agent
   subagents (critic, competing draft) if the design decision is genuinely
   contested — only your consolidated position goes forward.
3. Write your review entry to a scratch file, then
   `duet note --file <scratchfile> --repo <dir>`. If rejected, fix and retry.
4. `duet turn --repo <dir>` — Codex implements and replies; its entry prints
   to stdout and lands in REVIEW.md. Run it with Bash `run_in_background:
   true` and immediately arm the step monitor so the user gets "Codex is on
   step 3 of 7" as your messages while it works — see "Step progress arrives
   as Claude messages" below.
5. Do your own round of work: read the actual diff and files, re-run the
   evidence behind its claims, and form your position before you trust its
   entry — see "You are a peer, not a relay". Loop 2–4.
6. On dual SHIP (or when the human calls it): `duet end --repo <dir>` —
   writes the section summary and wipes Codex sessions automatically.

## Background mode (both sides headless)

```bash
duet run --mission "..." --repo <dir> --claude-model <this session's model> \
         [--rounds 8] [--freeze 3]
```

Run it with Bash `run_in_background: true`, arm the step monitor (see "Step
progress arrives as Claude messages"), and report the outcome when it
exits. Always pass `--claude-model` — see "Which model the designer runs". It terminates on dual-SHIP, BLOCKED (a
decision only the human can make), or the round cap — never runs unbounded.
`duet run --continue` resumes a BLOCKED section after the human answers (add
their answer to REVIEW.md by hand or via `duet note`).

## One-shot adversarial review

```bash
duet review --repo <dir> [--focus "what to scrutinize"]
```

Single read-only Codex pass: hunts for behavior/correctness/cost/security
defects, steelmans the design first, cites file:line, wipes its session
after. Its thinking is never shown — arm the step monitor so the user gets
"Codex is on step N of M" as your messages while it runs. Use it for "have
GPT check this" moments that don't need the full loop.

Inspired by openai/codex-plugin-cc's `/codex:adversarial-review`. The plugin
itself is deliberately NOT installed: it runs on `~/.codex` (the shared
account's live state), creates persistent threads resumable in the Codex
app, and its `/codex:transfer` imports Claude Code transcripts into
shared-account threads — all three violate this setup's privacy model. Do
not install it "to be helpful."

## Thinking is always maximum

Both sides run at their model's ceiling by default. The engineer runs at
`model_reasoning_effort = "ultra"` with `model_reasoning_summary = "detailed"`
(kept only so step markers exist for `duet progress` — the text itself is
dropped); designer turns run at `--effort max`, the claude CLI's top level
(valid: low/medium/high/xhigh/max; override: `DUET_CLAUDE_EFFORT`). Both are
written into `~/.duet/codex-home/config.toml` at `duet init` — edit that file
to dial either back. Thinking stays internal — only evidence-backed entries
cross the bridge (see PROTOCOL.md research notes).

## Which model the designer runs

**The headless designer must be the same model as the live session.** duet
cannot detect that on its own, so pass it every time you launch background
mode:

```bash
duet run --mission "..." --repo <dir> --claude-model <this session's alias>
```

You know the alias from your own system prompt — `fable`, `opus`, `sonnet`.
Pass it verbatim; don't guess and don't leave it off because the default
looks close enough.

Defaults when it isn't passed: `--claude-model fable`
(`DUET_CLAUDE_MODEL` overrides), max effort.

**Quota fallback.** If the primary model's usage runs out mid-section, the
designer continues on `--claude-fallback-model` (default `opus`) at the same
max effort, and stays there for the rest of the section rather than
re-hitting the exhausted limit each round. This is the one sanctioned
automatic model switch and it is never silent — the relay prints
`[duet] fable usage is exhausted — the designer continues on opus for the
rest of this section` to stdout and the feed, and each designer log records
the model that ran. Only quota exhaustion triggers it; an ordinary failed
turn stays on the model it started with. `DUET_CLAUDE_FALLBACK_MODEL=""`
disables it and makes the turn fail instead. duet also passes the CLI's own
`--fallback-model` for the separate "overloaded or unavailable" case, and
announces it if the API ends up serving a model other than the one asked for.

## Following the exchange

Codex's raw thinking is **never viewable, live or otherwise** — the relay
drops reasoning text on arrival (not printed, not written to the feed, and
filtered out of the debug logs). The only trace of it is the step counter
below. (Codex's own resumable session rollouts under the duet codex home do
hold reasoning until the section-end wipe — inherent to resume, never
rendered anywhere.) What does stream to stdout and the per-section feed file:
the designer's forwarded entry (`CLAUDE → CODEX` block), Codex's shell
commands (`$`), file edits (`✎`), its reply (`CODEX · R<n>` block), and relay
bounces.

- `duet stream --repo <dir>` in a VSCode terminal follows that feed
  (`--all` replays from the start).
- `duet watch --repo <dir>` remains for the entries-only ledger view.

Neither side's thinking is ever fed to the other (anchoring/contamination
risk, and reasoning-extraction prompts trigger Claude's refusal classifiers).
Only final entries cross the bridge. The exchange is never visible in the
ChatGPT app — that's deliberate (shared-account privacy).

## Step progress arrives as Claude messages

Every time you launch `duet turn`, `duet run`, or `duet review` (always via
Bash `run_in_background: true`), immediately arm a Monitor on —

```text
Monitor command: ~/.claude/skills/duet/bin/duet progress --follow --repo <dir>
```

For `duet review` add `--section <rev-id>` — reviews keep no state.json, and
the id is printed on the review's first output line.

**Relay the step and nothing else.** "Codex is on step 3 of 5." is the whole
message — no prefixes, no section labels even with several in flight, no
tool-call counts, no file names, no editorializing, no speculation about
what it is doing. If several lines arrive at once, relay each in order
(Codex reports its plan in bursts; the relay expands a batch into one line
per step it genuinely completed). `[duet] follow ended` is plumbing — never
relay it. `codex is thinking — no step counter yet` means Codex ignored its
plan tool; say that once and don't invent progress it hasn't reported.

Waiting is not the job — see "You are a peer, not a relay" below. Relay each
line the moment it arrives, and spend the rest of the turn working.

`duet progress --repo <dir>` (no `--follow`) is a one-shot check for your own
use between turns. Never present either form to the user as something to run.

## You are a peer, not a relay

The failure mode this loop keeps falling into: Codex does all the thinking
and building while Claude forwards step numbers. A round whose only Claude
output is forwarded progress is a **failed round** — the human is paying for
two senior models and getting one.

Every round, before you write your entry:

- **Read the diff yourself.** `git diff` and the changed files — not Codex's
  summary of them. Its entry is a claim, not a result.
- **Re-run its evidence.** Execute the test or command behind its EVIDENCE
  line yourself and say what you got. "Verified: 263/263 locally" or
  "its log shows 263 but the suite skips X" — either is a contribution;
  repeating its number back is not.
- **Bring something it doesn't have.** A failure case it missed, a
  measurement, a constraint from CONTEXT.md or the project's own docs, a
  competing approach with a reason. You own the design, the acceptance
  criteria, and the domain context Codex cannot see.
- **Investigate independently while its turn runs.** A background turn is
  20+ minutes of your time, not idle waiting: review the previous diff, draft
  this round's acceptance checks, verify last round's claims, spawn Agent
  subagents for a competing draft or an adversarial read.

Converge deliberately: each entry names what you now agree on **and why it
changed**, and what still separates you. SHIP when your own verification
passes — never because Codex says it does. Genuine deadlock goes to the
human as BLOCKED rather than another round of prose.

Both sides run at their ceiling and both are expected to do real work: Codex at
ultra, the designer at max effort on **the same model this session is
running** — see "Which model the designer runs".

## Privacy model

Designed for a ChatGPT account shared with other people; the same isolation is
what keeps duet's throwaway sections out of the user's real Codex history on a
solo account.

- Codex runs with `CODEX_HOME=~/.duet/codex-home` — never `~/.codex`, which
  is the user's own live Codex state and must not be touched.
- CLI-only, exec mode: duet sessions do not appear in the ChatGPT web UI or
  the Codex cloud tasks page. Never use `codex cloud` or web tasks for duet
  work.
- Sessions/history in the duet home are wiped at every section end (any
  outcome, including crashes), keeping only auth + config. Durable state
  lives solely in local repo files (DESIGN.md, REVIEW.md, code), which other
  account users cannot see.
- Concurrent sections are safe: automatic wipes are surgical (only the
  ending section's session); the full sweep of the codex home runs when the
  last active section ends. `duet wipe` forces a full sweep manually.
- Residual exposure that cannot be hidden: shared rate-limit consumption,
  and any server-side retention OpenAI applies account-wide.
- The wipe is also the one reason not to reach for duet: if you want the work
  to stay resumable in your Codex history afterwards, talk to Codex directly
  instead.

## When something fails

Read `docs/TROUBLESHOOTING.md` in this directory — it covers exit 137, expired
auth, stale sessions, relay bounces, quota exhaustion, missing step counters,
sandbox/network limits, model knobs and turn timeouts, each with the command
that fixes it. Do not guess at a fix or invent a workaround before reading it.

Two failure modes are worth knowing without opening the file, because they look
like bugs and are not:

- **No step counter for a whole turn.** Codex skipped its plan tool despite
  `prompts/engineer.md` requiring one. The counter has no other honest source,
  so the relay stays quiet rather than padding the feed. Say so once and do not
  invent progress.
- **A bounced entry auto-retries once.** Treat the retry's content as
  authoritative; the bounced draft never reaches REVIEW.md. If a turn fails
  after two bounces, the code changes are still on disk — read the diff before
  continuing.
