"""Full path: the real driver-side writer (render_event) replaying a recorded
codex turn, tailed live by the real `duet progress --follow`.

The driver's clock is compressed so a ~20-minute turn replays in seconds —
which also means transitions arrive far faster than the follower's 2s poll,
i.e. the exact condition that used to drop steps.

Defaults to the burst-plan fixture (5 steps reported as 0 -> 3 -> 4 -> 5);
pass a path to replay one of your own `~/.duet/logs/*/r*-engineer.log` turns.
"""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

DUET = _duetpath.DUET
LOG = sys.argv[1] if len(sys.argv) > 1 else \
    str(_duetpath.FIXTURES / "01-burst-plan.log")
TMP = Path(tempfile.mkdtemp(prefix="duet-int-test-"))
SEC = "s-int"
env = dict(os.environ, DUET_HOME=str(TMP))
deny_bin = TMP / "deny-bin"
deny_bin.mkdir()
denied_ps = deny_bin / "ps"
denied_ps.write_text("#!/bin/sh\nexit 126\n")
denied_ps.chmod(0o600)  # present but not executable: subprocess raises EACCES
follower_env = dict(env, PATH=str(deny_bin))
try:
    subprocess.run(["ps"], env=follower_env, check=False)
    ps_denied = False
except PermissionError:
    ps_denied = True

driver_src = f'''
import importlib.util, time
from importlib.machinery import SourceFileLoader
spec = importlib.util.spec_from_loader("d", SourceFileLoader("d", {DUET!r}))
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
d.emit = lambda *a, **k: None
d.emit_block = lambda *a, **k: None
CLOCK = [0.0]
d.time.monotonic = lambda: CLOCK[0]          # compressed turn clock
state = {{"section": {SEC!r}, "round": 4, "repo": "/tmp", "mission": "t"}}
LEASE = d.acquire_driver_lease({SEC!r})     # held until process exit, not reap
state["round"] = 3
d.progress_reset(state)
d.progress_update(state, kind="status", step=None, total=None,
                  status="thinking")
d.progress_update(state, status="turn-complete")
state["round"] = 4
time.sleep(4)                                 # quiet longer than --startup
d.progress_reset(state)
d.progress_update(state, kind="status", step=None, total=None,
                  status="thinking")
for line in open({LOG!r}, errors="replace"):
    CLOCK[0] += 3.0
    d.render_event(state, line)
d.progress_update(state, status="turn-complete")
time.sleep(1)
'''

driver = subprocess.Popen([sys.executable, "-c", driver_src], env=env)
time.sleep(1.5)
started = time.monotonic()
follower = subprocess.Popen([sys.executable, DUET, "progress", "--follow",
                            "--section", SEC, "--startup", "2"], env=follower_env,
                           text=True, stdout=subprocess.PIPE)
out = follower.communicate(timeout=20)[0]
elapsed = time.monotonic() - started
driver.wait()

lines = [l for l in out.splitlines() if l.strip()]
print("--- what the user would be told, in order ---")
for l in lines:
    print("  " + l)

steps = [l for l in lines if "on step" in l and "still" not in l]
seen = [l.split("step ")[1].split(" ")[0] for l in steps]
print(f"\nstep lines: {seen}")
lease_ok = (ps_denied and elapsed < 20
            and any("finished its round-3 turn" in l for l in lines)
            and seen == [f"{i}/5" for i in range(1, 6)]
            and lines[-1].startswith("[duet] follow ended"))

# Legacy logs have no lease. If both ps and pgrep are inaccessible, unknown
# liveness is finite rather than an infinite wait on an unreaped zombie.
legacy_sec = "s-legacy"
legacy_dir = TMP / "logs" / legacy_sec
legacy_dir.mkdir(parents=True)
legacy_driver = subprocess.Popen([sys.executable, "-c", "pass"])
time.sleep(0.5)  # exited but deliberately unreaped until the follower returns
stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
legacy_records = [
    {"status": "thinking", "kind": "status", "round": 1,
     "driver_pid": legacy_driver.pid, "updated": stamp},
    {"status": "turn-complete", "kind": "status", "round": 1,
     "driver_pid": legacy_driver.pid, "updated": stamp},
]
(legacy_dir / "progress.jsonl").write_text(
    "".join(json.dumps(r) + "\n" for r in legacy_records))
legacy_started = time.monotonic()
legacy_follower = subprocess.Popen(
    [sys.executable, DUET, "progress", "--follow", "--section", legacy_sec,
     "--startup", "1"], env=follower_env, text=True, stdout=subprocess.PIPE)
legacy_out = legacy_follower.communicate(timeout=8)[0]
legacy_elapsed = time.monotonic() - legacy_started
legacy_driver.wait()
legacy_ok = (legacy_elapsed < 8
             and legacy_out.splitlines()[-1].startswith("[duet] follow ended"))

ok = lease_ok and legacy_ok
print("PASS — no-ps lease spans quiet rounds; legacy unknown is bounded" if ok
      else f"FAIL — lease={lease_ok}, legacy={legacy_ok}, steps={seen}, "
           f"elapsed={elapsed:.1f}/{legacy_elapsed:.1f}s, ps_denied={ps_denied}")
import shutil; shutil.rmtree(TMP, ignore_errors=True)
sys.exit(0 if ok else 1)
