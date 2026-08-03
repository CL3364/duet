"""Locate the skill under test, wherever the clone lives.

Every test imports `bin/duet` as a module (it is a script, not a package), so
they all need the same two facts: where the skill root is, and how to load the
driver. Resolved relative to this file — no absolute paths, so the suite runs
from a clone at any path, including `~/.claude/skills/duet` itself.

`DUET_SKILL_DIR` overrides, for testing an installed copy from elsewhere.
"""
import importlib.util
import os
from importlib.machinery import SourceFileLoader
from pathlib import Path

SKILL = Path(os.environ.get(
    "DUET_SKILL_DIR", str(Path(__file__).resolve().parent.parent)))
DUET = str(SKILL / "bin" / "duet")
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_driver(name="d"):
    """Import bin/duet as a module. Set DUET_HOME before calling: the module
    reads it at import time."""
    spec = importlib.util.spec_from_loader(name, SourceFileLoader(name, DUET))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def recorded_logs():
    """Real codex turn logs to replay, newest-format first.

    The bundled fixture always runs. Point `DUET_REPLAY_LOGS` at a directory of
    your own `~/.duet/logs` sections to replay real traffic as well — that is
    how the step-fidelity bugs were originally found, and it is opt-in because
    those logs are your own project's data.
    """
    logs = sorted(FIXTURES.glob("*.log"))
    extra = os.environ.get("DUET_REPLAY_LOGS", "").strip()
    if extra:
        logs += sorted(Path(extra).expanduser().glob("*/r*-engineer.log"))
    return logs
