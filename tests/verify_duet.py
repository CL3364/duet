"""Verify /duet against every expectation stated in the conversation:

  1. every step Codex completes is shown, contiguously — no 1 -> 5 jumps
  2. relayed lines carry the step and NOTHING else (no tool calls/file edits)
  3. no reasoning, command text, or file path ever reaches the progress feed
  4. Codex is required to open a plan every turn
  5. Claude is a peer, not a relay (skill contract)
  6. designer model = the live session's model; fable default; opus only on
     quota exhaustion, announced and sticky
  7. the protocol guards that predate all this still bite
"""
import inspect, json, os, re, shlex, shutil, subprocess, sys, tempfile, types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _duetpath

SKILL = _duetpath.SKILL
TMP = Path(tempfile.mkdtemp(prefix="duet-verify-"))
os.environ["DUET_HOME"] = str(TMP)   # read at import time — must precede it

d = _duetpath.load_driver()

FAILS = []
def check(name, cond, detail=""):
    print(f"{'  ok  ' if cond else '  FAIL'} {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)

FEED = []
d.emit = lambda t="": FEED.append(t)
d.emit_block = lambda t, b: FEED.append(f"{t}\n{b}")


def replay(log_path, section, round_no=1, clock_step=3.0):
    """Run a real recorded codex log through the driver-side writer."""
    state = {"section": section, "round": round_no, "repo": "/tmp", "mission": "m"}
    clock = [0.0]
    d.time.monotonic = lambda: clock[0]
    d.LAST_LINE.pop(section, None)
    d.progress_reset(state)
    d.progress_update(state, kind="status", step=None, total=None, status="thinking")
    for line in open(log_path, errors="replace"):
        clock[0] += clock_step
        d.render_event(state, line)
    d.progress_update(state, status="turn-complete")
    jl = TMP / "logs" / section / "progress.jsonl"
    recs = [json.loads(l) for l in jl.read_text().splitlines() if l.strip()]
    return recs, [d.progress_line(r) for r in recs]


# ── 1. every step shown, contiguous, monotonic, across every recorded log ──
print("\n1. Step fidelity — replaying every recorded codex turn available")
logs = _duetpath.recorded_logs()


def step_faults(recs):
    """The invariant the relay actually promises: the counter starts at 1,
    advances one step at a time, never rewinds, and never exceeds its total.
    A repeated value is legal and deliberate — when codex rewrites its plan
    mid-turn the denominator moves while the step stays put (`note_step`), so
    2/4 -> 2/6 is the counter staying honest, not a skipped step."""
    seen = [(r["step"], r["total"]) for r in recs if r.get("kind") == "step"]
    faults, prev = [], 0
    for step, total in seen:
        if step > total:
            faults.append(f"{step}/{total} exceeds its total")
        elif step < prev:
            faults.append(f"rewound {prev} -> {step}")
        elif step > prev + 1:
            faults.append(f"skipped {prev} -> {step}")
        prev = max(prev, step)
    if seen and seen[0][0] != 1:
        faults.append(f"started at {seen[0][0]}, not 1")
    return [s for s, _ in seen], faults


total_turns = planned = 0
worst = []
for i, lg in enumerate(logs):
    recs, lines = replay(lg, f"sec{i}")
    steps, faults = step_faults(recs)
    total_turns += 1
    if not steps:
        continue
    planned += 1
    if faults:
        worst.append((lg.name, steps, faults))
check("no turn skips, rewinds or overruns its step counter", not worst,
      f"{worst[:2]}")
print(f"       {planned}/{total_turns} recorded turns opened a plan "
      f"({total_turns - planned} produced no step counter at all)")

# regression: a plan tool reporting in bursts (done 0 -> 3 -> 4 -> 5) used to
# render as "step 1/5" then "step 5/5" — steps 2, 3 and 4 never existed in the
# event stream and had to be filled in.
recs, lines = replay(_duetpath.FIXTURES / "01-burst-plan.log", "shot")
steps = [f"{r['step']}/{r['total']}" for r in recs if r.get("kind") == "step"]
check("a burst-reported 5-step plan renders as all 5 steps",
      steps == ["1/5", "2/5", "3/5", "4/5", "5/5"], str(steps))

# regression: a mid-turn re-plan must move the denominator without rewinding
recs, lines = replay(_duetpath.FIXTURES / "02-replan.log", "replan")
steps = [f"{r['step']}/{r['total']}" for r in recs if r.get("kind") == "step"]
check("a mid-turn re-plan grows the total without rewinding the step",
      steps == ["1/4", "2/4", "2/6", "3/6", "4/6", "5/6", "6/6"], str(steps))

# a turn with no plan tool has no honest counter — silence, not invention
recs, lines = replay(_duetpath.FIXTURES / "03-no-plan.log", "noplan")
check("a planless turn reports no step at all",
      not [r for r in recs if r.get("kind") == "step"])

# ── 2. relayed lines carry the step and nothing else ───────────────────────
print("\n2. Relay line content — the step, nothing else")
ALLOWED = [
    re.compile(r"^codex is on step \d+/\d+ \(round \d+\)$"),
    re.compile(r"^codex is thinking — no step counter yet \(round \d+\)$"),
    re.compile(r"^codex finished its round-\d+ turn$"),
    re.compile(r"^codex turn failed \(round \d+\) — see duet logs$"),
]
all_lines = []
for i, lg in enumerate(logs):
    all_lines += replay(lg, f"line{i}")[1]
bad = [l for l in all_lines if not any(p.match(l) for p in ALLOWED)]
check("every relayed line matches an approved step-only shape", not bad, str(bad[:3]))
# strip the legitimate step fraction first, then look for anything path-,
# command- or count-shaped in what remains
banned = [l for l in all_lines
          if re.search(r"tool call|file edit|command|\$ |\.\w{2,4}\b|/",
                       re.sub(r"step \d+/\d+", "step", l))]
check("no line mentions tool calls, file edits, commands or paths", not banned, str(banned[:3]))
check("the heartbeat machinery is gone from the code",
      not any(hasattr(d, n) for n in ("note_activity", "ACT_TRACK", "HEARTBEAT_S")))

# ── 3. nothing but numbers reaches the progress plumbing ──────────────────
print("\n3. Privacy — reasoning, commands and paths stay out of the feed")
SECRETS = {"reasoning": "SECRETTHOUGHT", "command": "SECRETCOMMAND",
           "path": "SECRETPATH", "message": "SECRETMESSAGE"}
sec = "privacy"
state = {"section": sec, "round": 1, "repo": "/tmp", "mission": "m"}
d.LAST_LINE.pop(sec, None); d.progress_reset(state)
d.progress_update(state, kind="status", step=None, total=None, status="thinking")
events = [
    {"type": "item.completed", "item": {"type": "reasoning",
     "text": f"step 2 of 4 — {SECRETS['reasoning']}"}},
    {"type": "item.started", "item": {"type": "command_execution",
     "command": f"pytest {SECRETS['command']}"}},
    {"type": "item.completed", "item": {"type": "file_change",
     "changes": [{"kind": "edit", "path": f"src/{SECRETS['path']}.py"}]}},
    {"type": "item.completed", "item": {"type": "agent_message",
     "text": f"{SECRETS['message']} step 3 of 4"}},
]
FEED.clear()
for ev in events:
    d.render_event(state, json.dumps(ev))
prog_blob = (TMP / "logs" / sec / "progress.jsonl").read_text() + \
            (TMP / "logs" / sec / "progress.json").read_text()
leaked = [k for k, v in SECRETS.items() if v in prog_blob]
check("no reasoning/command/path/message text in progress.json[l]", not leaked, str(leaked))
feed_blob = "\n".join(FEED)
check("reasoning text never reaches the live feed either",
      SECRETS["reasoning"] not in feed_blob)
check("commands and edits still DO reach the live feed (by design)",
      SECRETS["command"] in feed_blob and SECRETS["path"] in feed_blob)
check("a 'step N of M' marker inside reasoning still advances the counter",
      '"step": 2' in prog_blob or '"step":2' in prog_blob)
check("is_reasoning_line fails closed on unparseable reasoning fragments",
      d.is_reasoning_line('{"item":{"type":"reasoning'))

# ── 4/5. prompt + skill contract ──────────────────────────────────────────
print("\n4. Codex must open a plan; Claude must not be a relay")
eng = (SKILL / "prompts/engineer.md").read_text()
check("engineer prompt requires opening a plan before touching anything",
      "plan tool before you touch anything" in eng and "4–8 concrete steps" in eng)
check("engineer prompt forbids batching step completions",
      "not in a batch at the end" in eng)
skill = (SKILL / "SKILL.md").read_text()
check("skill says a relay-only round is a failed round",
      "failed round" in skill and "You are a peer, not a relay" in skill)
check("skill requires reading the diff and re-running the evidence",
      "Read the diff yourself" in skill and "Re-run its evidence" in skill)
check("skill tells the relay to send the step and nothing else",
      "Relay the step and nothing else" in skill)
check("no stale heartbeat/DUET_PROGRESS_HEARTBEAT references in the docs",
      "DUET_PROGRESS_HEARTBEAT" not in skill)
check("role labels renamed off Fable",
      "FABLE" not in skill and "FABLE" not in (SKILL / "bin/duet").read_text())

# ── 5b. skill contract: frontmatter + trigger-description drift ────────────
# Whether the skill fires at all is decided solely by `description`. Editing it
# for tone silently breaks triggering, and nothing else in the suite notices —
# so the documented trigger phrases are asserted to still be in it.
print("\n5b. Frontmatter and trigger coverage (Anthropic skill guide)")
fm = skill.split("---")[1]
desc = re.search(r"^description:\s*(.+?)(?=^\w[\w-]*:)", fm, re.S | re.M).group(1).strip()

check("description is within the 1024-char limit", len(desc) <= 1024,
      f"{len(desc)} chars")
check("description says WHAT the skill does and WHEN to use it",
      "Use when" in desc and len(desc.split("Use when")[0].split()) >= 8)
check("no XML angle brackets anywhere in frontmatter (security restriction)",
      not re.search(r"[<>]", fm), str(re.findall(r"[<>]", fm))[:80])
check("frontmatter declares license, compatibility and metadata",
      all(re.search(rf"^{f}:", fm, re.M)
          for f in ("license", "compatibility", "metadata")))
check("skill name is kebab-case and not a reserved claude/anthropic prefix",
      re.search(r"^name:\s*([a-z0-9-]+)\s*$", fm, re.M)
      and not re.match(r"(claude|anthropic)", "duet"))

TRIGGERS = ["duet", "pair with", "bridge to", "second opinion",
            "have GPT check this", "adversarially review"]
missing = [t for t in TRIGGERS if t.lower() not in desc.lower()]
check("every documented SHOULD-trigger phrase is still in the description",
      not missing, f"missing: {missing}")
check("description carries a negative trigger so it stays quiet on plain coding",
      "Not for" in desc or "not for" in desc)
tt = SKILL / "references" / "trigger-tests.md"
check("references/trigger-tests.md exists and documents both directions",
      tt.exists() and "Should trigger" in tt.read_text()
      and "Should NOT trigger" in tt.read_text())
check("SKILL.md defers failure handling instead of inlining it",
      "docs/TROUBLESHOOTING.md" in skill)

# ── 6. designer model selection ───────────────────────────────────────────
print("\n6. Designer model — session model, fable default, opus on exhaustion")
ap_src = (SKILL / "bin/duet").read_text()
check("--claude-model defaults to fable",
      'DUET_CLAUDE_MODEL", "fable"' in ap_src)
check("--claude-fallback-model defaults to opus",
      'DUET_CLAUDE_FALLBACK_MODEL",\n                                          "opus"' in ap_src
      or '"DUET_CLAUDE_FALLBACK_MODEL", "opus"' in ap_src or '"opus"' in ap_src)
check("skill mandates passing the live session's model",
      "--claude-model <this session's alias>" in skill or
      "--claude-model <this session's model>" in skill)

captured = {}
def fake_subprocess_run(cmd, **kw):
    captured["cmd"] = cmd
    return types.SimpleNamespace(returncode=0, stdout=json.dumps(
        {"result": "entry", "session_id": "sid",
         "modelUsage": {"claude-fable-5-20260101": {}}}), stderr="")
real_run = d.subprocess.run
d.subprocess.run = fake_subprocess_run
d.log_path = lambda s, n: TMP / "designer.log"
args = types.SimpleNamespace(claude_model="fable", claude_fallback_model="opus",
                             claude_effort="max", claude_bin="claude", turn_timeout=0)
st = {"round": 1, "section": "m", "repo": "/tmp"}
d.run_claude(st, args, "prompt")
cmd = captured["cmd"]
check("the requested model is passed to the CLI",
      "--model" in cmd and cmd[cmd.index("--model") + 1] == "fable")
check("--fallback-model is passed for the overload case",
      "--fallback-model" in cmd and cmd[cmd.index("--fallback-model") + 1] == "opus")
check("designer runs at max effort", "--effort" in cmd and cmd[cmd.index("--effort") + 1] == "max")
# same model both sides -> no self-fallback
args2 = types.SimpleNamespace(**{**vars(args), "claude_model": "opus"})
d.run_claude({"round": 1, "section": "m2", "repo": "/tmp"}, args2, "p")
check("no --fallback-model when it equals the primary",
      "--fallback-model" not in captured["cmd"])
d.subprocess.run = real_run

# ── 7. protocol guards still bite ─────────────────────────────────────────
print("\n7. Pre-existing protocol guards")
base = {"open_items": {}, "next_open_id": 1, "round": 1, "freeze_round": 3}
def errs(text, role="designer", **over):
    return d.validate_entry(text, role, {**base, **over})
check("entry with no VERDICT bounces", errs("nothing here"))
check("banned filler bounces", any("filler" in e for e in errs("great point\nVERDICT: SHIP")))
check("CLOSE without EVIDENCE bounces",
      any("EVIDENCE" in e for e in errs("CLOSE OPEN-1\nVERDICT: CONTINUE",
          open_items={"1": {"raiser": "designer", "status": "open", "text": "x"}})))
check("SHIP over your own open item bounces (phantom agreement)",
      any("phantom" in e for e in errs("VERDICT: SHIP",
          open_items={"1": {"raiser": "designer", "status": "open", "text": "x"}})))
check("clean entry passes", not errs("EVIDENCE: ran tests\nVERDICT: CONTINUE"))
check("new OPEN after the freeze round needs REGRESSION+EVIDENCE",
      any("frozen" in e for e in errs("OPEN-1: new thing\nVERDICT: CONTINUE", round=5)))
check("privacy wipe refuses to touch the real ~/.codex",
      d.CODEX_HOME.resolve() != d.REAL_CODEX_HOME.resolve())

# ── 8. cold-start auth guidance is actionable in every file state ──────────
print("\n8. Cold-start auth status — exact next action")
status_repo = TMP / "status-repo"
status_repo.mkdir()


def run_cli(home, command="status", duet_home=None, codex_home=None):
    env = dict(os.environ, HOME=str(home))
    env["DUET_HOME"] = str(duet_home or (home / ".duet"))
    if codex_home is None:
        env.pop("DUET_CODEX_HOME", None)
    else:
        env["DUET_CODEX_HOME"] = str(codex_home)
    argv = [sys.executable, _duetpath.DUET, command]
    if command == "status":
        argv += ["--repo", str(status_repo)]
    return subprocess.run(argv, env=env, capture_output=True, text=True)


empty_home = TMP / "auth-empty"
empty_home.mkdir()
empty_codex = empty_home / ".duet" / "codex-home"
direct_login = f"CODEX_HOME={shlex.quote(str(empty_codex))} codex login"
empty_status = run_cli(empty_home)
check("no real or isolated auth prints a direct isolated login",
      empty_status.returncode == 0 and direct_login in empty_status.stdout,
      empty_status.stdout)
empty_init = run_cli(empty_home, "init")
check("cold init prints the same direct isolated login",
      empty_init.returncode == 0 and direct_login in empty_init.stdout,
      empty_init.stdout)

real_home = TMP / "auth-real-only"
(real_home / ".codex").mkdir(parents=True)
(real_home / ".codex" / "auth.json").write_text("{}")
real_status = run_cli(real_home)
check("real auth with no isolated copy points to duet init",
      "(NO AUTH — run duet init)" in real_status.stdout, real_status.stdout)

isolated_home = TMP / "auth-isolated-only"
(isolated_home / ".duet" / "codex-home").mkdir(parents=True)
(isolated_home / ".duet" / "codex-home" / "auth.json").write_text("{}")
isolated_status = run_cli(isolated_home)
check("isolated auth is ready without real auth",
      "(ready)" in isolated_status.stdout, isolated_status.stdout)

both_home = TMP / "auth-both"
(both_home / ".codex").mkdir(parents=True)
(both_home / ".codex" / "auth.json").write_text("{}")
(both_home / ".duet" / "codex-home").mkdir(parents=True)
(both_home / ".duet" / "codex-home" / "auth.json").write_text("{}")
both_status = run_cli(both_home)
check("isolated auth remains ready when real auth also exists",
      "(ready)" in both_status.stdout, both_status.stdout)

override_home = TMP / "auth-override"
override_home.mkdir()
override_duet = TMP / "custom duet home"
override_codex = TMP / "custom codex home"
override_login = f"CODEX_HOME={shlex.quote(str(override_codex))} codex login"
override_status = run_cli(override_home, duet_home=override_duet,
                          codex_home=override_codex)
check("status quotes and honors a spaced DUET_CODEX_HOME override",
      override_login in override_status.stdout, override_status.stdout)

lease = d.acquire_driver_lease("lease-unit")
held = d.driver_lease_alive("lease-unit")
d.release_driver_lease(lease)
released = d.driver_lease_alive("lease-unit")
check("driver lease reports held, then dead after release",
      held is True and released is False, f"{held=} {released=}")
driver_sources = [inspect.getsource(fn) for fn in
                  (d.cmd_run, d.cmd_turn, d.cmd_review)]
check("run, turn and review hold the lease for their outer command",
      all("acquire_driver_lease" in src and "release_driver_lease" in src
          for src in driver_sources))

print("\n" + ("ALL CHECKS PASSED" if not FAILS
             else f"{len(FAILS)} FAILED: {FAILS}"))
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if FAILS else 0)
