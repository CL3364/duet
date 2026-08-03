# 2. Codex sessions are destroyed at every section end

Date: 2026-08-03

## Status

Accepted

## Context

duet was built against a ChatGPT account shared with other people. Anything the
Codex CLI writes into its home — session rollouts, history, and in newer
versions `memories_*.sqlite`, `logs_*.sqlite`, `goals_*.sqlite` and shell
snapshots — is conversation-derived and readable by anyone else with access to
that account.

The obvious alternatives were both worse. Leaving sessions in place makes every
duet section recoverable by another account user. Redacting selectively means
maintaining a blocklist against a CLI that adds new state files between
releases — a race the tool would keep losing.

There is a real cost on the other side. Codex's own resume mechanism depends on
those rollouts. Destroying them means a section cannot be picked up later inside
Codex, and it means the reasoning that produced a decision is gone the moment
the section closes.

## Decision

Every section end wipes the duet Codex home, on **any** outcome — dual SHIP,
`BLOCKED`, round cap, crash, or interrupt. Exactly five entries survive, none of
them conversation-derived: `auth.json`, `config.toml`, `installation_id`,
`models_cache.json` and `version.json`.

The wipe is an **allowlist**, not a blocklist: anything not explicitly named as
worth keeping is removed, so a future Codex release that invents a new state
file is cleaned by default rather than after someone notices it.

Codex runs with `CODEX_HOME` pointed at a duet-managed directory, never
`~/.codex`. The wipe refuses to run at all if those two paths ever resolve to
the same place.

Durable state lives exclusively in local repo files: `DESIGN.md`, `CONTEXT.md`,
`REVIEW.md`, the section summary, and the code itself.

## Consequences

**What this buys.** No duet section is recoverable from the shared account. The
transcript that survives is the one in the repo, which the account's other users
cannot see. Concurrent sections are safe because automatic wipes are surgical —
only the ending section's rollout — with the full sweep deferred until no other
duet section is running.

**What it costs, and it is not small.** A section cannot be resumed inside
Codex afterwards. If the work should stay live in your Codex history, **duet is
the wrong tool** and you should talk to Codex directly. This is the single most
common reason to *not* reach for duet, and it is a direct consequence of this
decision rather than an oversight.

**Residual exposure that cannot be designed away.** Rate-limit consumption is
shared and visible. Whatever server-side retention OpenAI applies account-wide
applies here too. The wipe controls the local artifact, not the provider's.

**Reversal.** `--no-wipe` skips it per section and `duet wipe` forces it
manually, so the behavior is tunable at the edges. Changing the default would
change what every existing user relies on, which is why it is recorded here.
