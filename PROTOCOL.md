# The duet protocol

Why this exists: two frontier models left alone will (a) keep talking after
the work is done, and (b) cave to each other's pushback to seem agreeable.
Both failure modes are handled mechanically by the relay, not by asking the
models to behave.

## Structure

- One **section** = one mission = one bounded piece of work.
- Rounds alternate designer → engineer. Every turn ends in exactly one
  review entry appended to `.duet/REVIEW.md` by the relay (never by the
  models directly), so the transcript format never drifts.
- `DESIGN.md` is designer-owned; implementation files are engineer-owned.
  Neither touches the other's territory — cross-territory requests travel
  as OPEN items.

## Entry grammar (enforced)

```text
<prose: conclusion first, evidence, caveat, next action — no length cap,
 density is the rule; file:line refs instead of pasted code>
OPEN-<n>: <new contention>            # numbered, relay-assigned next id
CLOSE OPEN-<n>                        # only your own items
EVIDENCE: <test log path / measurement / spec cite>
REGRESSION: <justification>           # required for new items after freeze
NITS: <non-blocking; can never block SHIP>
VERDICT: SHIP | CONTINUE | BLOCKED: <reason>
```

## Anti-over-conversation

There is deliberately **no hard word cap**. Both vendors' current guidance
says blunt length limits degrade output on this model class (Anthropic:
over-prescriptive instructions reduce Fable 5 quality; OpenAI: stacked
brevity rules make GPT-5.6 over-correct). Length is steered instead:

- **Density decision rules, not caps**: lead with the conclusion; include
  only what changes what the other side does next; cut introductions,
  restatements, generic reassurance. Settled points are never re-affirmed —
  silence is agreement.
- **API-level verbosity**: the engineer runs with `model_verbosity = "low"`
  (GPT-5.6's final-answer length control; reasoning is unaffected, so ultra
  thinking + terse entries coexist).
- **SHIP by default**: if nothing you'd raise changes behavior, correctness,
  cost, or security — SHIP. Style points go to NITS and cannot block.
- **Scope freeze**: after round 3 (default), new OPEN items need
  REGRESSION + EVIDENCE. No late-arriving "one more thought".
- **Round cap**: 8 (default). Hitting it is a result ("no convergence"),
  reported to the human — not a license to keep going.
- **Termination**: both sides SHIP with zero open items → section over,
  summary written, Codex context wiped.

## Anti-phantom-agreement

- **Items are owned**: only the raiser of OPEN-n can close it. The other
  side cannot "resolve" your objection by talking past it.
- **Evidence-gated concession**: CLOSE without an EVIDENCE line bounces.
  "On reflection you're right" is not evidence; a test log path, a
  measurement, or a spec/file:line is.
- **No shipping over your own objections**: SHIP while any item you raised
  is still open bounces with the reason spelled out.
- **Deadlock is a feature**: if evidence can't settle it, the verdict is
  BLOCKED and the human decides. Two VPs escalating beats two models
  splitting the difference.

## Tone

Senior executive to a peer: direct, concrete, zero flattery, zero
acknowledgment padding. Banned phrases ("great point", "you're absolutely
right", thanks, apologies) are rejected by the relay, not just discouraged.

## Research notes (why the rules are shaped this way)

- **Independent position formation**: each side is told to form its position
  from the files *before* reading the other's latest entry. "The Deliberative
  Illusion" (arXiv 2606.03032, 2026) found stance homogenization and factual
  attrition accelerate when agents absorb peer output before anchoring their
  own view; "Hidden Anchors" (arXiv 2606.19494) shows early statements anchor
  later deliberation.
- **Evidence-gated concession + owned items**: CONSENSAGENT (ACL Findings
  2025) showed agents reinforce rather than critique each other; requiring
  citations for every CLOSE, and letting only the raiser close an item,
  keeps epistemic tension alive (role asymmetry per 2606.03032).
- **Judge content, not author**: identity-bias work (arXiv 2510.07517) found
  sycophancy and self-bias are two faces of the same failure; entries
  instruct judging claims on content and evidence, not confidence or source.
- **Density over caps**: Anthropic's Fable 5 prompting guide (short
  principle beats enumerated rules; over-prescription degrades output) and
  OpenAI's GPT-5.6 guidance (conclusion-first structure; `text.verbosity`
  for length; avoid redundant brevity commands) both steer via principles +
  API knobs rather than truncation.
- **Thinking stays internal; conclusions cross the bridge**: reasoning
  traces are never passed between the models — trace-level contamination
  work (arXiv 2604.27586) shows intermediate reasoning propagates errors and
  anchors downstream agents, and Anthropic's Fable 5 guide warns that
  prompts asking the model to reproduce its reasoning trigger
  `reasoning_extraction` refusals. Instead, each side thinks at maximum
  internal effort (Codex: `model_reasoning_effort = "ultra"`; Fable:
  adaptive thinking) and exchanges only evidence-backed entries. GPT-5.6's
  reasoning summaries (`model_reasoning_summary = "detailed"`) are consumed
  by the relay solely to extract step-progress markers ("3/7") for
  `duet progress`; the text is displayed to no one — not the human, not
  Fable — and is filtered out of the debug logs.
