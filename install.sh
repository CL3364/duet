#!/bin/sh
# duet installer — clone or update ~/.claude/skills/duet, then set up the
# isolated Codex home.
#
#   curl -fsSL https://raw.githubusercontent.com/CL3364/duet/main/install.sh | sh
#
# Or, if you already cloned the repo, just run ./install.sh from inside it.
# Idempotent: safe to re-run to update.
set -eu

REPO="${DUET_REPO:-https://github.com/CL3364/duet.git}"
DEST="${DUET_SKILL_DIR:-$HOME/.claude/skills/duet}"
STATE_ROOT="${DUET_HOME:-$HOME/.duet}"
ISOLATED_CODEX_HOME="${DUET_CODEX_HOME:-$STATE_ROOT/codex-home}"

say() { printf '%s\n' "$*"; }
die() { printf 'install: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null 2>&1 || die "python3 is required"

# Running from inside an existing clone? Install that, don't re-fetch.
# Piped through `curl | sh`, $0 is not a path — that check has to fail closed.
here=""
case "$0" in
  */install.sh|install.sh)
    [ -f "$0" ] && here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) ;;
esac

if [ -n "$here" ] && [ -f "$here/SKILL.md" ] && [ -x "$here/bin/duet" ] \
   && [ "$here" != "$DEST" ]; then
  say "==> installing from $here"
  mkdir -p "$(dirname "$DEST")"
  if [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
    die "$DEST already exists — remove it, or symlink it to $here yourself"
  fi
  rm -f "$DEST"
  ln -s "$here" "$DEST"
  say "    symlinked $DEST -> $here"
elif [ -d "$DEST/.git" ]; then
  say "==> updating $DEST"
  git -C "$DEST" pull --ff-only
else
  command -v git >/dev/null 2>&1 || die "git is required"
  [ -e "$DEST" ] && die "$DEST already exists but is not a git clone — move it first"
  say "==> cloning into $DEST"
  mkdir -p "$(dirname "$DEST")"
  git clone --depth 1 "$REPO" "$DEST"
fi

chmod +x "$DEST/bin/duet" "$DEST/tests/run_all.sh" 2>/dev/null || true

say ""
say "==> setting up the isolated Codex home"
"$DEST/bin/duet" init

say ""
"$DEST/bin/duet" status || true

say ""
if [ -f "$ISOLATED_CODEX_HOME/auth.json" ]; then
  say "Ready. Start a Claude Code session and type /duet."
else
  say "One step left — sign the Codex CLI into your OpenAI account:"
  say ""
  say "    codex login"
  say "    $DEST/bin/duet init --refresh-auth"
  say ""
  say "Then start a Claude Code session and type /duet."
fi
