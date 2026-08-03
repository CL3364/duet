"""End-to-end: does `duet progress --follow` deliver every transition when
they arrive faster than its poll interval?"""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

DUET = _duetpath.DUET
TMP = Path(tempfile.mkdtemp(prefix="duet-follow-test-"))
SEC = "s-test"
logdir = TMP / "logs" / SEC
logdir.mkdir(parents=True)
env = dict(os.environ, DUET_HOME=str(TMP))

# a stale record from an "earlier round", 10 minutes old — must NOT be replayed
old = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 600))
jl = logdir / "progress.jsonl"
jl.write_text(json.dumps({"kind": "step", "step": 9, "total": 9,
                          "status": "working", "round": 1,
                          "updated": old}) + "\n")

# stand-in for the section's own driver process, so the test is isolated from
# any real duet turn running on this machine. Its command line must contain
# "duet" — the follower rejects a pid that is no longer a duet process.
DRIVER = subprocess.Popen([sys.executable, "-c",
                           "import time; time.sleep(600)  # duet driver stand-in"])

proc = subprocess.Popen([sys.executable, DUET, "progress", "--follow",
                         "--section", SEC, "--startup", "12"],
                        env=env, text=True, stdout=subprocess.PIPE)
time.sleep(3)  # let it prime

# burst: 5 transitions inside one poll window (the old sampler saw only the last)
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
with jl.open("a") as f:
    for s in range(1, 6):
        f.write(json.dumps({"kind": "step", "step": s, "total": 5,
                            "status": "working", "round": 2,
                            "driver_pid": DRIVER.pid,
                            "updated": now()}) + "\n")
        f.flush()
        time.sleep(0.05)
time.sleep(3)
with jl.open("a") as f:
    f.write(json.dumps({"kind": "activity", "acts": 12, "edits": 3,
                        "step": 5, "total": 5, "status": "working",
                        "round": 2, "driver_pid": DRIVER.pid,
                        "updated": now()}) + "\n")
    f.write(json.dumps({"status": "turn-complete", "kind": "status",
                        "round": 2, "driver_pid": DRIVER.pid,
                        "updated": now()}) + "\n")

DRIVER.kill(); DRIVER.wait()  # driver exits — follower must notice and stop
out = proc.communicate(timeout=60)[0]
lines = [l for l in out.splitlines() if l.strip()]
print("--- follower output ---")
for l in lines:
    print("  " + l)

steps = [l for l in lines if "on step" in l and "still" not in l]
ok = True
if any("9/9" in l for l in lines):
    print("FAIL: replayed a stale record from an earlier round"); ok = False
if len(steps) != 5:
    print(f"FAIL: expected 5 step lines, got {len(steps)}"); ok = False
for i, l in enumerate(steps, 1):
    if f"step {i}/5" not in l:
        print(f"FAIL: step line {i} is {l!r}"); ok = False
if any("tool call" in l or "file edit" in l for l in lines):
    print("FAIL: a count line reached the relay"); ok = False
# a legacy activity record written by an older driver must degrade to a plain
# step line rather than resurrecting the counts
if not any(l.startswith("codex is on step 5/5") for l in lines):
    print("FAIL: legacy activity record did not degrade to a step line"); ok = False
if not any("finished its round-2 turn" in l for l in lines):
    print("FAIL: completion missing"); ok = False
if not lines[-1].startswith("[duet] follow ended"):
    print("FAIL: did not exit cleanly"); ok = False
print("PASS — every transition delivered, none replayed" if ok else "FAILURES ABOVE")
import shutil; shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if ok else 1)
