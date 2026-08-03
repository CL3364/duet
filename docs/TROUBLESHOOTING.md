# Troubleshooting

Start with `duet status --repo <dir>`. It prints auth state, how many Codex
sessions are awaiting a wipe, and the section in flight with its open items.

---

## Setup

### `status` says `NO AUTH`

`~/.duet/codex-home/auth.json` is missing. Follow the action on the status
line. If credentials already exist in `~/.codex`, it says:

```bash
duet init                   # copy existing credentials into the isolated home
```

If this machine has no Codex credentials, status instead prints the direct
interactive login against the isolated home:

```bash
CODEX_HOME=~/.duet/codex-home codex login
```

### Auth expired mid-section

Same fix — `codex login`, then `duet init --refresh-auth`. Credentials are one
of the few things the privacy wipe deliberately preserves, so this only happens
when the token itself expires.

### `WARNING: codex is not on PATH` / `claude is not on PATH`

`npm i -g @openai/codex` for the first; install Claude Code for the second. If
they're installed somewhere unusual, point duet at them:
`DUET_CODEX_BIN=/opt/homebrew/bin/codex`, `DUET_CLAUDE_BIN=...`.

### The `/duet` skill doesn't appear in Claude Code

`SKILL.md` has to sit at `~/.claude/skills/duet/SKILL.md`. Check the clone
landed at the right path (`ls ~/.claude/skills/duet/SKILL.md`) and restart the
session. Skills are read at startup.

---

## Turns failing

### `codex exec failed twice, exit 137`

137 is SIGKILL. It shows up when Codex's own sandbox is nested inside another
sandbox. Run duet from a plain terminal, or — only if you are *already*
externally sandboxed and know what that means:

```bash
DUET_CODEX_SANDBOX=danger-full-access
```

### `no rollout found for thread id`

A stale Codex session, usually after an interrupted turn. Clear it and re-run:

```bash
# in <repo>/.duet/state.json, set:  "codex_session": null
duet turn --repo <dir>
```

A fresh session cold-starts from the war-room files. Nothing durable is lost —
that's why state lives in files.

### `<model> usage is exhausted and no fallback is available`

The designer's model ran out of quota and `DUET_CLAUDE_FALLBACK_MODEL` is
empty. Set it to a model you still have headroom on, or wait for the reset.
When a fallback *is* configured, duet switches automatically, announces it
loudly, and stays there for the rest of the section rather than re-hitting the
exhausted limit every round.

### `designer turn was served by X, not the requested Y`

The API served a different model than asked for — usually the CLI's own
overload fallback. Informational, not an error, but worth noticing if you care
which model wrote a given entry. Every designer log records the model that ran.

### A background turn just stopped

Long sections can outlive your Claude usage window. `git status` first — there
will be partial writes — then re-dispatch with an "audit the partial work, then
finish it" brief rather than restarting the round.

### `codex exec` hangs with "Reading additional input from stdin..."

duet already passes `stdin=DEVNULL` to prevent this. If you see it, you're
invoking `codex` directly somewhere, not through the relay.

### Codex can't reach npm / pip / the network

Its sandbox is `workspace-write` with no network by default. Pass `--codex-net`
to open network access inside the sandbox when it genuinely needs to install
something. Leave it off otherwise — most turns don't need it, and the narrower
sandbox is the safer default.

### A turn runs longer than you want to wait

There is **no time cap per turn** by default (`--turn-timeout 0`); a single
Codex turn legitimately runs 20+ minutes. Pacing is meant to be bounded by the
round cap, not the clock. Set a cap explicitly if you need one:

```bash
duet turn --repo <dir> --turn-timeout 1800    # or: DUET_TURN_TIMEOUT=1800
```

### The wrong model ran on one side

Every designer log records the model that actually ran; check it before
assuming. The knobs:

| | |
| --- | --- |
| `--codex-model` / `DUET_CODEX_MODEL` | Engineer model. Defaults to whatever `duet init` wrote into `~/.duet/codex-home/config.toml`. |
| `--claude-model` / `DUET_CLAUDE_MODEL` | Designer model. The skill is instructed to pass the live session's model on every launch; the env default only applies when it doesn't. |
| `DUET_CLAUDE_FALLBACK_MODEL` | Where the designer continues on quota exhaustion. Empty disables it and fails the turn instead. |

Entry length has no hard cap — it is steered by the output contract plus
`model_verbosity = "low"` in the duet codex config. See
[PROTOCOL.md](../PROTOCOL.md#research-notes-why-the-rules-are-shaped-this-way).

---

## Relay bounces

The relay rejects a non-conformant entry, tells the model exactly why, and
lets it resubmit once. Twice non-conformant fails the turn. The messages are
meant to be self-explanatory; these are the ones with consequences.

### `OPEN-n already used; next available id is OPEN-m`

Item ids are relay-assigned and never reused. This fires when a model tries to
`CLOSE` and re-raise a still-contested item under its original id.

**Watch out:** by the time the turn fails, the code changes are already on
disk — but no entry was recorded in `REVIEW.md` and no verdict counted. Review
the diff before continuing. To keep contesting an item, leave it open rather
than closing and re-raising.

### `CLOSE without EVIDENCE`

Working as intended. A concession needs a test log path, a measurement, or a
spec/`file:line` — "on reflection you're right" is exactly what the rule
exists to reject.

### `SHIP while your own items are open — that is phantom agreement`

Also working as intended. Close them with evidence, or stay on `CONTINUE`.

### `scope is frozen: new OPEN items now require REGRESSION: and EVIDENCE:`

Past the freeze round (3 by default). Either justify the late item as a
regression with evidence, or start `--freeze` higher next section if your work
genuinely surfaces new scope late.

### `banned filler phrase`

"Great point", "you're absolutely right", thanks, apologies. Rejected rather
than discouraged, on purpose.

---

## Progress and monitoring

### `codex is thinking — no step counter yet` for a whole turn

Codex skipped its plan tool, despite `prompts/engineer.md` requiring a 4–8 step
plan every turn. The step counter has no other honest source, so the relay
stays quiet rather than padding the feed. Roughly a third of turns
historically. Check `~/.duet/logs/<section>/progress.jsonl` — if a transition
isn't there, Codex never reported it.

### Steps arrive several at a time

Expected. Codex reports its plan in bursts; the relay expands a batch into one
line per step it actually completed, so you see 1, 2, 3, 4, 5 rather than 1
then 5.

### The step monitor never exits

Current drivers hold a section-scoped kernel lease that is released on normal
exit, failure, or crash; another section cannot hold this follower open. Logs
created before the lease existed fall back to pid inspection and stop after a
finite grace if the process table is unavailable. If a current monitor is
genuinely stuck, the driver still holds that section's lease.

### I want to see what Codex is thinking

You can't, anywhere, by design. Reasoning text is dropped on arrival — not
printed, not written to the live feed, and filtered out of the debug logs.
`model_reasoning_summary = "detailed"` stays in the Codex config *only* so
step markers exist to extract.

What you can watch:

```bash
duet stream --repo <dir>    # forwarded entries, $ commands, ✎ edits, replies
duet watch  --repo <dir>    # the REVIEW.md entry ledger alone
```

---

## Sections and state

### `a section is already in flight here`

One section per repo at a time. Finish it (`duet end`), continue it
(`duet run --continue`), or delete `<repo>/.duet/state.json` if it's dead.

### `conversation cap reached (8 rounds used)`

The round budget is spent. Hitting it is a result — "no convergence" — not a
prompt to keep going. Read `REVIEW.md`, then either `duet end`, or make the
human call and raise `rounds` in `.duet/state.json`.

### Resuming a dead section's items

Don't. If a section was abandoned, its `OPEN` ids are spent. Start a fresh
section; `REVIEW.md` keeps the history either way.

---

## Privacy

### Did anything reach the ChatGPT app?

No. duet uses exec-mode CLI only, in an isolated `CODEX_HOME`. Sessions don't
appear in the ChatGPT web UI or the Codex cloud tasks page. Never use
`codex cloud` or web tasks for duet work.

### Force a wipe now

```bash
duet wipe
```

Full allowlist sweep of `~/.duet/codex-home` — sessions, history, memories,
logs, shell snapshots — keeping only auth and config. Automatic wipes at
section end are surgical (that section's session), with the full sweep running
once no other duet section is active.

### `refusing to wipe ~/.codex`

A safety check firing correctly: `DUET_CODEX_HOME` resolved to your real Codex
home. Unset it, or point it somewhere else. duet never writes to `~/.codex`.

### Do not install `openai/codex-plugin-cc` alongside duet

It runs on `~/.codex`, creates persistent threads resumable in the Codex app,
and its `/codex:transfer` imports Claude Code transcripts into them. All three
defeat the isolation above.

---

## Diagnosing the relay itself

Replay one recorded turn and see exactly what the step plumbing produced:

```bash
python3 tests/replay_test.py ~/.duet/logs/<section>/r1-engineer.log
```

Run the full suite (no network, no Codex calls, no cost):

```bash
tests/run_all.sh
DUET_REPLAY_LOGS=~/.duet/logs tests/run_all.sh   # + your own recorded turns
```
