---
name: duet
description: Claude(designer) ⇄ Codex(engineer) peer review loop — this session's model and gpt-5.6-sol argue to common ground over an evidence-gated relay, with automatic privacy wipe for shared ChatGPT accounts. Use when asked to "duet", "pair with codex", "bridge to codex/gpt", or run a design⇄engineering loop with GPT.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
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

## Troubleshooting

- `codex exec` exit 137 (SIGKILL): known when nested inside another sandbox.
  Run duet from a plain terminal or set
  `DUET_CODEX_SANDBOX=danger-full-access` (only when already externally
  sandboxed).
- Auth expired in duet home: `duet init --refresh-auth` (re-copies from
  ~/.codex after the user logs in there).
- Model knobs: `DUET_CODEX_MODEL` (default: duet config, gpt-5.6-sol),
  `DUET_CLAUDE_MODEL` (default: fable — but pass `--claude-model` with the
  live session's model instead), `DUET_CLAUDE_FALLBACK_MODEL` (default:
  opus, on quota exhaustion only; see "Which model the designer runs").
  Entry length has no hard cap — it is
  steered by the output contract plus `model_verbosity = "low"` in the duet
  codex config (see PROTOCOL.md research notes).
- Engineer needs npm/pip: pass `--codex-net`.
- Turn time vs conversation budget: model turns have **no time cap by
  default** (`--turn-timeout 0`; set seconds explicitly or `DUET_TURN_TIMEOUT`
  to restore one). Runaway dialogue is bounded by the **round cap instead**,
  now enforced in interactive mode too: `note`/`turn` refuse once the
  section's `rounds` budget (default 8) is used; only a human may raise it
  (edit `rounds` in `.duet/state.json`).
- Codex thinking is intentionally invisible: reasoning text is dropped by
  the relay everywhere (stream, feed file, debug logs). Step numbers,
  relayed by Claude as chat messages from the `duet progress --follow`
  monitor, are the only window into a turn in flight.
  `model_reasoning_summary = "detailed"` stays in the duet codex config
  solely to make those step markers available; effort stays `ultra`.
- No step counter for a whole turn: Codex skipped its plan tool despite
  `prompts/engineer.md` requiring it — the counter has no other honest
  source, so the relay stays quiet rather than padding the feed. Per-section
  transitions are kept in `~/.duet/logs/<section>/progress.jsonl` (the
  append-only log the follower tails) alongside `progress.json` (the
  snapshot the one-shot form reads); check the log when a step looks
  missing — if it isn't there, Codex never reported it.
- A monitor that never exits: current drivers hold a section-scoped kernel
  lease, released automatically even on crashes, so a concurrent duet section
  neither holds this follower open nor ends it early. Legacy sections fall
  back to pid inspection with a finite grace when process inspection is
  unavailable. `--replay <s>` controls startup history (default 20s), and
  `--startup <s>` controls the missing/unknown-driver grace.
