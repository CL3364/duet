"""Designer model fallback: fable until its usage is exhausted, then opus —
announced, sticky for the section, and never triggered by other failures."""
import json, sys, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

d = _duetpath.load_driver()

EMITTED = []
d.emit = lambda t="": EMITTED.append(t)
d.log_path = lambda state, name: __import__("pathlib").Path("/dev/null")

args = types.SimpleNamespace(claude_model="fable", claude_fallback_model="opus",
                             claude_effort="max", claude_bin="claude",
                             turn_timeout=0)

USAGE_ERR = ('{"type":"result","is_error":true,'
             '"result":"Claude AI usage limit reached|SYNTHETIC_RESET_EPOCH"}')
OTHER_ERR = '{"type":"result","is_error":true,"result":"tool permission denied"}'


def fake_run(script):
    """script: list of (expected_model, stdout) for successive calls."""
    calls = []

    def _once(state, a, prompt, model):
        want_model, out = script[len(calls)]
        calls.append(model)
        assert model == want_model, f"call {len(calls)}: {model} != {want_model}"
        if "is_error\":true" in out:
            return None, out
        data = json.loads(out)
        return data.get("result", ""), None
    return _once, calls


ok = True

# 1. happy path: stays on fable, no fallback flag needed
d.claude_once, calls = fake_run([("fable", '{"result":"entry A"}')])
state = {"round": 1, "section": "s", "repo": "/tmp"}
got = d.run_claude(state, args, "p")
good = got == "entry A" and calls == ["fable"] and state.get("claude_model") is None
print(f"{'ok  ' if good else 'FAIL'} healthy fable turn stays on fable: {calls}")
ok &= good

# 2. fable exhausted -> announced, retried on opus, sticky
EMITTED.clear()
d.claude_once, calls = fake_run([("fable", USAGE_ERR),
                                 ("opus", '{"result":"entry B"}')])
state = {"round": 1, "section": "s", "repo": "/tmp"}
got = d.run_claude(state, args, "p")
announced = any("usage is exhausted" in e and "opus" in e for e in EMITTED)
good = (got == "entry B" and calls == ["fable", "opus"]
        and state["claude_model"] == "opus" and announced)
print(f"{'ok  ' if good else 'FAIL'} exhausted fable -> opus, announced={announced}, "
      f"sticky={state.get('claude_model')}")
ok &= good

# 3. sticky holds: the next round starts on opus, never re-hits fable
d.claude_once, calls = fake_run([("opus", '{"result":"entry C"}')])
state["round"] = 2
got = d.run_claude(state, args, "p")
good = got == "entry C" and calls == ["opus"]
print(f"{'ok  ' if good else 'FAIL'} next round starts on the fallback: {calls}")
ok &= good

# 4. a non-quota failure must NOT switch models
d.claude_once, calls = fake_run([("fable", OTHER_ERR)])
state = {"round": 1, "section": "s", "repo": "/tmp"}
try:
    d.run_claude(state, args, "p")
    good = False
except d.TurnError as e:
    good = "exhausted" not in str(e) and state.get("claude_model") is None
print(f"{'ok  ' if good else 'FAIL'} ordinary failure does not switch models")
ok &= good

# 5. fallback disabled -> fail loudly instead of switching
noflip = types.SimpleNamespace(**{**vars(args), "claude_fallback_model": ""})
d.claude_once, calls = fake_run([("fable", USAGE_ERR)])
state = {"round": 1, "section": "s", "repo": "/tmp"}
try:
    d.run_claude(state, noflip, "p")
    good = False
except d.TurnError as e:
    good = "exhausted" in str(e) and calls == ["fable"]
print(f"{'ok  ' if good else 'FAIL'} empty fallback fails instead of switching")
ok &= good

# 6. served-model mismatch detection
good = (d.model_served("fable", ["claude-fable-5-20260101"])
        and not d.model_served("fable", ["claude-opus-5-20260101"])
        and d.model_served("opus", ["claude-opus-5[1m]"]))
print(f"{'ok  ' if good else 'FAIL'} detects which model actually served a turn")
ok &= good

print("PASS" if ok else "FAILURES ABOVE")
sys.exit(0 if ok else 1)
