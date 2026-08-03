"""Priming rules: a monitor armed late must replay the in-flight turn in
full, and must never replay a turn that already ended."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

d = _duetpath.load_driver()

old = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 600))
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rec(status, step=None, rnd=1, ts=old, kind="step"):
    return {"status": status, "step": step, "total": 3, "round": rnd,
            "kind": kind, "updated": ts}


r1 = [rec("thinking", kind="status"), rec("working", 1), rec("working", 2),
      rec("working", 3), rec("turn-complete", kind="status")]
r2 = [rec("thinking", rnd=2, kind="status"), rec("working", 1, rnd=2),
      rec("working", 2, rnd=2)]

cases = [
    ("late arm, round 2 in flight after round 1 finished", r1 + r2, 3,
     ["thinking", "1", "2"]),
    ("everything already finished (stale section)", r1, 0, []),
    ("nothing has happened yet", [], 0, []),
    ("turn in flight from the very start", r2, 3, ["thinking", "1", "2"]),
]
ok = True
for name, recs, expect_n, expect in cases:
    got = d.prime_records(recs, time.time() - 20)
    tags = ["thinking" if r["status"] == "thinking" else str(r["step"])
            for r in got]
    good = len(got) == expect_n and tags == expect
    ok &= good
    print(f"{'ok ' if good else 'FAIL'} {name}: replayed {tags}")
print("PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
