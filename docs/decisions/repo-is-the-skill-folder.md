## The repository is the skill folder

Date: 2026-08-03

### Status

Accepted

### Context

Anthropic's *Complete Guide to Building Skills for Claude* states two things
that pull in opposite directions for an open-source skill:

- A skill folder **must not contain a `README.md`**. All documentation belongs
  in `SKILL.md` or `references/`.
- When distributing on GitHub, you **do** want a repo-level `README.md` for
  human visitors — and the guide's own recommended layout puts the skill in a
  subdirectory beneath it.

duet is distributed as a git clone placed directly at
`~/.claude/skills/duet`. That makes the repository root and the skill folder
the same directory, so a repo README and the no-README rule cannot both be
satisfied by placement alone.

The alternative layout — `skills/duet/` inside the repo — is what the guide
describes, but it costs a two-step install (clone somewhere, then symlink or
copy the subdirectory into the skills directory) and it changes an install
command that is already published.

### Decision

The repository root is the skill folder. `README.md` sits beside `SKILL.md`.

Installation stays one command:

```bash
git clone https://github.com/CL3364/duet.git ~/.claude/skills/duet
```

### Consequences

**What this buys.** One command to install, `git pull` to update, and a single
directory that is simultaneously the repo, the skill, and — via symlink — the
user's live installation. There is no build step and no copy that can drift
from its source.

**What it costs.** The layout is not what the guide describes. The rule exists
for the Claude.ai upload path, where a skill folder is zipped and uploaded; a
zip of this repo would carry a `README.md`, `docs/`, `tests/` and `.git/` that
that path does not want. Anyone packaging duet for Claude.ai will need to strip
those first.

**Why the cost is acceptable.** Claude Code reads `SKILL.md` and nothing else
from a skill directory. A sibling `README.md` is inert there — it is never
loaded into context and cannot affect triggering or behavior. The rule protects
against a packaging concern that duet's actual distribution channel does not
have.

**Reversal.** Moving to `skills/duet/` later is mechanical, but it breaks every
published install command and every existing symlink. That is why this is
recorded rather than left implicit.
