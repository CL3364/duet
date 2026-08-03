"""Regression tests for the three defects the live codex review found.

1. snapshot -> log handoff printed the same step twice
2. --replay 0 discarded a step written after startup (whole-second stamps vs
   a fractional cutoff)
3. a failed log append dropped that step permanently
"""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

DUET = _duetpath.DUET
FAILS = []
def check(name, cond, detail=""):
    print(f"{'  ok  ' if cond else '  FAIL'} {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond: FAILS.append(name)

TMP = Path(tempfile.mkdtemp(prefix="duet-findings-"))
os.environ["DUET_HOME"] = str(TMP)   # read at import time — must precede it
d = _duetpath.load_driver()

# ── finding 1: snapshot -> log handoff must not re-print ───────────────────
print("\nFinding 1 — snapshot to log handoff")
SEC = "handoff"
logdir = TMP / "logs" / SEC; logdir.mkdir(parents=True)
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
driver = subprocess.Popen([sys.executable, "-c",
                           "import time; time.sleep(600)  # duet driver stand-in"])
snap = logdir / "progress.json"
# state as an in-flight turn: snapshot exists, transition log does NOT yet
snap.write_text(json.dumps({"kind": "step", "step": 1, "total": 3,
                            "status": "working", "round": 1,
                            "driver_pid": driver.pid, "updated": now()}))
env = dict(os.environ, DUET_HOME=str(TMP))
follower = subprocess.Popen([sys.executable, DUET, "progress", "--follow",
                             "--section", SEC], env=env, text=True,
                            stdout=subprocess.PIPE)
time.sleep(3)                       # follower reports step 1/3 from snapshot
jl = logdir / "progress.jsonl"      # now the writer creates the log
with jl.open("a") as f:
    for rec in ({"status": "thinking", "kind": "status", "round": 1,
                 "driver_pid": driver.pid, "updated": now()},
                {"kind": "step", "step": 1, "total": 3, "status": "working",
                 "round": 1, "driver_pid": driver.pid, "updated": now()}):
        f.write(json.dumps(rec) + "\n")
time.sleep(3)
with jl.open("a") as f:
    f.write(json.dumps({"kind": "step", "step": 2, "total": 3,
                        "status": "working", "round": 1,
                        "driver_pid": driver.pid, "updated": now()}) + "\n")
time.sleep(3)
driver.kill(); driver.wait()
out = follower.communicate(timeout=60)[0]
lines = [l for l in out.splitlines() if l.strip() and not l.startswith("[duet]")]
print("       follower said:", lines)
step1 = [l for l in lines if "step 1/3" in l]
check("step 1 is reported exactly once across the handoff", len(step1) == 1,
      f"{len(step1)} times")
check("no backwards 'thinking' after a step was already reported",
      not (lines and "thinking" in " ".join(lines[1:])), str(lines))
check("the step after the handoff still arrives",
      any("step 2/3" in l for l in lines), str(lines))

# ── finding 2: --replay 0 must not drop a just-written record ──────────────
print("\nFinding 2 — fractional cutoff vs whole-second stamps")
# The follower starts 0.6s into a second (--replay 0). A whole turn is then
# written 0.1s later — after startup, but stamped to the second that began
# before it. The old fractional cutoff rejected records it should have kept.
base = int(time.time())
stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(base))
recs = [{"status": "thinking", "round": 1, "updated": stamp},
        {"kind": "step", "step": 1, "total": 2, "status": "working",
         "round": 1, "updated": stamp},
        {"status": "turn-complete", "round": 1, "updated": stamp}]
startup = base + 0.6
frac_cutoff = startup                # old: time.time() - 0
floored = float(int(startup))        # new: floored to the whole second
check("old fractional cutoff would have dropped the records",
      d.prime_records(recs, frac_cutoff) == [])
check("floored cutoff keeps records stamped in the same second",
      len(d.prime_records(recs, floored)) == 3)
src = Path(DUET).read_text()
check("follow_progress floors its cutoff", "float(int(time.time()" in src)

# ── finding 3: a failed append must not mark the line delivered ────────────
print("\nFinding 3 — failed log append")
SEC2 = "appendfail"
state = {"section": SEC2, "round": 1, "repo": "/tmp"}
d.LAST_LINE.pop(SEC2, None)
real_open = Path.open
calls = {"n": 0}
def flaky_open(self, *a, **kw):
    if self.name == "progress.jsonl":
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("disk full")
    return real_open(self, *a, **kw)
Path.open = flaky_open
d.progress_update(state, kind="step", step=1, total=2, status="working")
delivered_after_failure = d.LAST_LINE.get(SEC2)
d.progress_update(state, kind="step", step=1, total=2, status="working")
Path.open = real_open
jl2 = TMP / "logs" / SEC2 / "progress.jsonl"
written = [json.loads(l) for l in jl2.read_text().splitlines() if l.strip()] \
    if jl2.exists() else []
check("a failed append is not recorded as delivered", delivered_after_failure is None)
check("the same step is appended on the next attempt",
      len(written) == 1 and written[0]["step"] == 1, str(written))

print("\n" + ("ALL FINDINGS FIXED" if not FAILS else f"{len(FAILS)} FAILED: {FAILS}"))
import shutil; shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
