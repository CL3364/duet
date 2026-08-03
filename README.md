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

Two of these are the same conversation and differ in exactly one thing —
**who plays the designer.** The third is not a conversation at all.

| | Designer is | Loop runs | Designer knows |
| --- | --- | --- | --- |
| **Interactive** | **your live Claude session** | one round at a time, gated on you | your whole conversation |
| **Background** | **a second, headless Claude** | start to finish, unattended | only `.duet/CONTEXT.md` + `DESIGN.md` |
| **`review`** | nobody — a single Codex pass | no rounds at all | the repo, read-only |

The middle column is the ergonomic difference. The right-hand column is the one
that decides whether the result is any good.

### 1. Interactive — your live session is the designer

The default, and the one worth learning. Claude does its design work in your
session where you can steer it, and hands each round to Codex in the
background.

```text
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

The loop **stalls between every round** until Claude writes the next entry, so
the section moves at the speed of your attention. In exchange, the designer is
the Claude that has heard everything you said, and you can redirect it after
any round.

### 2. Background — a second, headless Claude is the designer

```text
You:  /duet in background — get the flaky auth tests green, 6 rounds max
```

`duet run` spawns its own Claude to argue with Codex. Your session launches it,
relays step numbers, and reports the outcome; the loop never waits on you, so
the rest of the conversation stays free for other work. It terminates on dual
SHIP, `BLOCKED`, or the round cap — never unbounded.

**What you give up is context, and it is the whole ballgame.** That designer is
a *separate conversation*. It cannot see yours. It starts cold and knows only
what is written in `.duet/CONTEXT.md` and `DESIGN.md` at launch — and anything
you say in your own session while it runs is invisible to it.

In interactive mode a thin CONTEXT.md is survivable, because the designer fills
the gaps from memory. In background mode a thin CONTEXT.md **is the entire
brief**, and the designer will confidently guess at whatever you left out.

Two more things worth knowing before choosing it:

- **It costs more Claude, not less.** You pay for two Claude conversations at
  once — your session plus the headless designer at max effort every round — on
  top of Codex. Interactive is the economical mode; background buys walk-away
  convenience with quota. duet ships a sticky fallback model for exactly this
  reason.
- **You cannot close the laptop.** Sleep drops the API connections mid-turn and
  the section lands as `BLOCKED`. `caffeinate` does not prevent lid-close sleep;
  only clamshell mode does. Nothing is lost — `duet run --continue` resumes from
  `state.json` — but it will not finish while you are away.

**Choose background when the mission is already fully specified** — when you can
write down everything that matters before it starts. **Choose interactive when
the thinking is still live**, because then the designer needs to be the Claude
that is hearing it.

### 3. One-shot adversarial review — no designer at all

No loop, no design phase, no consensus — a single read-only Codex pass that
steelmans your design, then hunts for defects in behavior, correctness, cost,
and security, citing `file:line`. Its session is wiped afterwards.

```text
You:  /duet review — have GPT check the migration I just wrote
```

Cheapest of the three on Claude, since no designer turn ever runs — but nobody
argues back, so there is no convergence and no agreed conclusion, only findings.

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
| [docs/adr/](docs/adr/README.md) | Decisions that would otherwise look arbitrary |
| [references/trigger-tests.md](references/trigger-tests.md) | Phrases `/duet` must and must not fire on |
| `bin/duet` | The relay — one Python file, stdlib only |
| `prompts/` | The two role prompts, designer and engineer |
| `tests/` | Six suites; no account, no network, no cost |

---

## License

MIT — see [LICENSE](LICENSE).
