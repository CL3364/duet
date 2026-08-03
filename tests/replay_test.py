"""Diagnostic, not a pass/fail test: replay one recorded codex turn through
duet's progress plumbing and print what the user would have seen — the raw plan
events on their own vs the transitions the relay actually delivers.

    python3 replay_test.py fixtures/01-burst-plan.log
    python3 replay_test.py ~/.duet/logs/<section>/r1-engineer.log

Reach for it when a step looks missing in a real section.
"""
import json, os, shutil, sys, tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

TMP = Path(tempfile.mkdtemp(prefix="duet-progress-test-"))
os.environ["DUET_HOME"] = str(TMP)   # read at import time — must precede it

duet = _duetpath.load_driver("duetmod")
duet.LIVE_FH = None

log = Path(sys.argv[1]) if len(sys.argv) > 1 \
    else _duetpath.FIXTURES / "01-burst-plan.log"
section = "testsec"
state = {"section": section, "round": 1, "repo": str(TMP), "mission": "t"}

# silence the dialogue feed; we only care about progress
duet.emit = lambda *a, **k: None
duet.emit_block = lambda *a, **k: None

duet.progress_reset(state)
duet.progress_update(state, kind="status", step=None, total=None,
                     status="thinking")

# --- old behaviour: snapshot sampled every 2s by the follower -------------
old_lines, old_prev = [], None
raw_plan = []
for line in log.open(errors="replace"):
    try:
        ev = json.loads(line)
    except Exception:
        continue
    if not isinstance(ev, dict):
        continue
    it = (ev.get("item") or {}) if isinstance(ev.get("item"), dict) else {}
    if it.get("type") == "todo_list":
        items = it.get("items") or []
        if items:
            done = sum(1 for i in items if i.get("completed"))
            raw_plan.append((min(done + 1, len(items)), len(items)))

# --- new behaviour --------------------------------------------------------
# fake clock: advance 3s per event so a replayed turn spans realistic time
CLOCK = [0.0]
duet.time.monotonic = lambda: CLOCK[0]
for line in log.open(errors="replace"):
    CLOCK[0] += 3.0
    duet.render_event(state, line)
duet.progress_update(state, status="turn-complete")

jl = TMP / "logs" / section / "progress.jsonl"
recs = [json.loads(l) for l in jl.read_text().splitlines() if l.strip()]

print(f"=== {log.name} ===")
print(f"raw plan events (old ceiling): "
      + (" → ".join(f"{s}/{t}" for s, t in raw_plan) or "none — user saw only 'thinking'"))
print(f"new transitions ({len(recs)}):")
for r in recs:
    print("   " + duet.progress_line(r))
shutil.rmtree(TMP, ignore_errors=True)
