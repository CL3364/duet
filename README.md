# duet

**A Claude Code skill that makes Claude and Codex argue to common ground.**

`/duet` puts your Claude Code session (as VP of Product & Design) and OpenAI's
Codex CLI (as VP of Engineering) in one war room and runs them until they agree
on evidence — not until one of them finishes building. A Python relay sits
between them and enforces the rules mechanically, because two frontier models
left alone reliably do two things: keep talking after the work is done, and
cave to each other's pushback to seem agreeable.

```
┌──────────────┐   entry (evidence-gated)   ┌──────────────┐
│  CLAUDE      │ ─────────────────────────▶ │   CODEX      │
│  designer    │                            │   engineer   │
│  owns        │ ◀───────────────────────── │   owns the   │
│  DESIGN.md   │   entry (evidence-gated)   │   code       │
└──────────────┘                            └──────────────┘
        │              ▲          ▲                │
        └──────────────┴──────────┴────────────────┘
                  bin/duet — the relay:
    CLOSE needs EVIDENCE · you cannot SHIP over your own open item
    scope freezes after round 3 · hard round cap · deadlock → you
```

Neither model ever sees the other's reasoning. Only finished, evidence-backed
entries cross the bridge.

---

## What makes it different from "ask two models"

Every rule below is enforced by the relay in `bin/duet`, so a model cannot
comply-in-spirit and drift anyway:

| Guard | What it stops |
| --- | --- |
| **Owned items** — only whoever raised `OPEN-n` may close it | The other side "resolving" your objection by talking past it |
| **Evidence-gated concession** — `CLOSE` without an `EVIDENCE:` line bounces | "On reflection, you're right" as a substitute for a test log |
| **No shipping over your own objection** — `SHIP` while an item you raised is open bounces | Phantom agreement |
| **Banned filler** — "great point", "you're absolutely right", thanks, apologies are rejected | Mutual flattery replacing review |
| **Scope freeze** after round 3 — new items need `REGRESSION:` + `EVIDENCE:` | Late-arriving "one more thought" |
| **Round cap** (8) | Unbounded conversation. Hitting it is a *result*: "no convergence" |
| **`BLOCKED` is a valid verdict** | Two models splitting the difference on something only you can decide |
| **Territory** — designer never edits code, engineer never edits `DESIGN.md` | Either side quietly rewriting the other's work instead of arguing |

The full rationale, with the multi-agent research the rules are drawn from,
is in [PROTOCOL.md](PROTOCOL.md).

---

## Requirements

| | |
| --- | --- |
| **Claude Code** | Installed, with the `claude` CLI on your `PATH` |
| **Codex CLI** | `npm i -g @openai/codex` (≥ 0.144), signed into your OpenAI/ChatGPT account |
| **Python** | 3.9+ (stdlib only — no packages to install) |
| **OS** | macOS or Linux |

Both sides bill to your own subscriptions. duet adds no service and phones
nowhere; the relay is one local Python file.

---

## Install

```bash
git clone https://github.com/CL3364/duet.git ~/.claude/skills/duet
~/.claude/skills/duet/bin/duet init
~/.claude/skills/duet/bin/duet status     # expect: ready
```

`init` creates `~/.duet/codex-home` — an isolated Codex home — and copies your
Codex credentials into it. If `status` says `NO AUTH`, run the exact command it
prints: `duet init` when existing `~/.codex` credentials can be copied, or a
direct login against the isolated home when this machine has no Codex login:

```bash
CODEX_HOME=~/.duet/codex-home codex login
```

Update later with `git -C ~/.claude/skills/duet pull`. Uninstall by deleting
`~/.claude/skills/duet` and `~/.duet`.

Then start a Claude Code session and type `/duet`. Claude reads `SKILL.md`,
which tells it how to drive the relay — you never type a `duet` command
yourself.

> **Want to run it somewhere else?** Nothing depends on the install path except
> the paths written in `SKILL.md`. Clone anywhere and point Claude at it, or
> symlink: `ln -s /path/to/duet ~/.claude/skills/duet`.

---

## Three ways to run it

### 1. Interactive — you and Claude are the designer, live

The default, and the one worth learning. Claude does its design work in your
session where you can steer it, and hands each round to Codex in the
background.

```
You:  /duet — redesign the retry logic in the ingest worker
```

Claude then, on its own:

1. `duet start --mission "..." --repo .`
2. Writes `.duet/CONTEXT.md` — everything Codex can't see: your actual goal,
   constraints, decisions already made and why. A brief, never a transcript.
3. Writes `.duet/DESIGN.md` — the vision, interfaces, acceptance criteria.
4. Records its own review entry with `duet note`.
5. Runs `duet turn` in the background — Codex implements and replies — and
   relays *"Codex is on step 3 of 7"* into your chat while it works.
6. Reads the resulting diff itself, re-runs the evidence, writes the next
   entry. Loop.
7. `duet end` on dual SHIP — writes the section summary and wipes Codex's
   session.

### 2. Background — both sides headless

For work you want to walk away from. Claude launches it and reports the
outcome.

```
You:  /duet in background — get the flaky auth tests green, 6 rounds max
```

Terminates on dual SHIP, `BLOCKED`, or the round cap. Never runs unbounded.

### 3. One-shot adversarial review

No loop, no design phase — a single read-only Codex pass that steelmans your
design, then hunts for defects in behavior, correctness, cost, and security,
citing `file:line`. Its session is wiped afterwards.

```
You:  /duet review — have GPT check the migration I just wrote
```

This one earns its keep more often than you'd guess. Pointed at freshly
written code, it finds the author-blind-spot races that a test suite written
by the same author never covers.

### Watching it happen

Two optional terminal views, both `Ctrl-C` to stop:

```bash
~/.claude/skills/duet/bin/duet stream --repo .   # live: forwarded entries, $ commands, ✎ edits
~/.claude/skills/duet/bin/duet watch  --repo .   # just the REVIEW.md entry ledger
```

Codex's raw reasoning is not among them, by design — see
[Privacy](#privacy-and-what-lands-where).

---

## Getting your money's worth

The single biggest failure mode is Claude turning into a **progress bar**:
Codex does all the thinking and building while Claude forwards step numbers.
That is one senior model's output for two models' cost.

`SKILL.md` fights this ("a round whose only Claude output is forwarded
progress is a **failed round**"), but you're the one who notices. What good
rounds look like, and how to get them, is in
**[docs/PLAYBOOK.md](docs/PLAYBOOK.md)** — the CONTEXT.md brief, territory
rules, working the background turn, when to force `BLOCKED`, and the gotchas
that cost real time the first time you hit them.

The short version:

- **`.duet/CONTEXT.md` is the highest-leverage file in the repo.** Codex reads
  it cold and has none of your conversation. A thin CONTEXT.md is the cause of
  most bad first rounds.
- **Make Claude read the diff, not Codex's summary of it.** If a round's only
  Claude content is agreement, say so — "you didn't verify that."
- **Give the two sides real territory.** Tell Claude what Codex must not touch
  (your frontend, your commits) in the mission itself.
- **`BLOCKED` is the good outcome for a genuine tie.** Two VPs escalating to
  you beats two models splitting the difference.
- **Round cap 8 is deliberate.** Convergence normally lands in 3–6. Needing
  more usually means the mission was two missions.

---

## Command reference

You will rarely type these — Claude drives them — but this is the whole surface.

| Command | What it does |
| --- | --- |
| `duet init [--refresh-auth]` | Build the isolated codex home, copy credentials |
| `duet status [--repo D]` | Auth state, sessions awaiting wipe, section in flight |
| `duet start --mission M --repo D` | Open an interactive section |
| `duet note --file F \| --text T` | Record the live designer's entry (validated) |
| `duet turn --repo D` | Run one engineer turn |
| `duet run --mission M --repo D` | Autonomous section, both sides headless |
| `duet run --continue --repo D` | Resume a `BLOCKED` section after you answer |
| `duet review --repo D [--focus F]` | One-shot read-only adversarial review |
| `duet end --repo D` | Close the section: summary + privacy wipe |
| `duet stream --repo D [--all]` | Follow the live dialogue feed |
| `duet watch --repo D [--all]` | Follow the REVIEW.md ledger |
| `duet progress --repo D [--follow]` | Codex's step counter (plumbing for Claude) |
| `duet wipe` | Force a full sweep of the codex home now |

Useful flags on `run` / `start`: `--rounds N` (default 8), `--freeze N`
(default 3), `--claude-model`, `--codex-model`, `--codex-net` (let Codex reach
npm/pip), `--turn-timeout S` (default 0 = no time cap), `--no-wipe`.

### Files a section creates

```
<your repo>/.duet/
├── CONTEXT.md      designer-written brief for Codex — the project, cold
├── DESIGN.md       designer-owned: vision, interfaces, acceptance criteria
├── REVIEW.md       relay-owned, append-only: every entry, both sides
├── state.json      live section state (open items, round, verdicts)
├── logs/           evidence Codex cites in EVIDENCE: lines
└── sections/       one summary per finished section

~/.duet/
├── codex-home/     isolated CODEX_HOME (auth + config survive wipes)
└── logs/<section>/ live.txt, per-round turn logs, progress.jsonl
```

`.duet/` is worth committing — `REVIEW.md` is a genuinely good record of why
the code looks the way it does. Add `.duet/state.json` and `.duet/logs/` to
`.gitignore` if you'd rather not carry the churn.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DUET_HOME` | `~/.duet` | Where the codex home and logs live |
| `DUET_CODEX_HOME` | `$DUET_HOME/codex-home` | Isolated Codex home |
| `DUET_CODEX_MODEL` | from codex config | Engineer model |
| `DUET_CLAUDE_MODEL` | `fable` | Designer model when not passed explicitly |
| `DUET_CLAUDE_FALLBACK_MODEL` | `opus` | Designer model on quota exhaustion; empty to fail instead |
| `DUET_CLAUDE_EFFORT` | `max` | Designer reasoning effort |
| `DUET_CODEX_SANDBOX` | `workspace-write` | Codex sandbox level |
| `DUET_TURN_TIMEOUT` | `0` | Seconds per turn; 0 = no cap |
| `DUET_CODEX_BIN` / `DUET_CLAUDE_BIN` | `codex` / `claude` | Binary paths |

**On the designer model:** duet cannot detect which model your session is
running, so `SKILL.md` instructs Claude to pass `--claude-model` every time.
If your session is Opus and you see `fable` in the logs, Claude skipped it —
tell it to pass the flag. Engineer effort lives in
`~/.duet/codex-home/config.toml` (`model_reasoning_effort = "ultra"`); edit
that file to dial it back.

---

## Privacy, and what lands where

duet was built for a ChatGPT account shared with other people. The same
isolation keeps throwaway duet sections out of your real Codex history on a
solo account.

- **Codex runs in `~/.duet/codex-home`, never `~/.codex`.** Your live Codex
  state is never read except to copy credentials, and never written. The wipe
  refuses to run if the two ever resolve to the same path.
- **Exec-mode CLI only.** duet sessions do not appear in the ChatGPT web UI or
  the Codex cloud tasks page.
- **Sessions are wiped at every section end**, on any outcome including
  crashes — allowlist, not blocklist, so Codex's newer `memories_*.sqlite`,
  `logs_*.sqlite` and shell snapshots go too. Auth and config survive.
- **Codex's reasoning text is never viewable** — dropped from stdout, from the
  live feed, and from the debug logs. Only the step number (`3/7`) is
  extracted, and only so Claude can tell you where it's up to.
- **Neither model ever reads the other's reasoning.** Trace-level
  contamination propagates errors and anchors the downstream model; only final
  entries cross.
- **What cannot be hidden:** rate-limit consumption on a shared account, and
  whatever server-side retention OpenAI applies account-wide.

**The flip side:** the wipe is destructive on purpose. If you want the work to
stay resumable in your Codex history, duet is the wrong tool — talk to Codex
directly instead.

---

## Tests

No network, no Codex calls, no account, no cost:

```bash
tests/run_all.sh
```

Six suites covering step-counter fidelity across recorded turns, step-only
relay line shapes, reasoning/command/path leak checks, lossless burst delivery
to a late-armed monitor, section-scoped driver liveness, designer model
fallback, and every protocol guard. They replay hand-written fixtures in the
exact shape `codex exec --json` emits, so a fresh clone is green with nothing
installed but Python.

To replay your own traffic as well — how the original step-counter bugs were
found:

```bash
DUET_REPLAY_LOGS=~/.duet/logs tests/run_all.sh
```

---

## Troubleshooting

The failures worth knowing about — relay bounces, stale sessions, exit 137,
missing step counters, expired auth, sandbox and network limits, model knobs —
are in **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

---

## Repository map

| | |
| --- | --- |
| [SKILL.md](SKILL.md) | The skill itself — what Claude reads to drive the relay |
| [PROTOCOL.md](PROTOCOL.md) | Why the rules are shaped this way, with citations |
| [CONTEXT.md](CONTEXT.md) | Glossary. One term, one meaning |
| [docs/PLAYBOOK.md](docs/PLAYBOOK.md) | How to get real work out of the loop |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Every failure and its fix |
| [docs/adr/](docs/adr/) | Decisions that would otherwise look arbitrary |
| [references/trigger-tests.md](references/trigger-tests.md) | Phrases `/duet` must and must not fire on |
| `bin/duet` | The relay — one Python file, stdlib only |
| `prompts/` | The two role prompts, designer and engineer |
| `tests/` | Six suites; no account, no network, no cost |

---

## License

MIT — see [LICENSE](LICENSE).
