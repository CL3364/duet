# Trigger tests

Whether a skill fires at all is decided by one thing: the `description` in
`SKILL.md`. These are the cases it is written to satisfy.

Triggering needs a live Claude deciding in real time, so the cases below are run
by hand. What *is* automated lives in `tests/verify_duet.py`, which asserts that
every phrase in the SHOULD-trigger table still appears in the description and
that every negative-trigger term still appears in the exclusion clause. That
catches the failure that actually happens: someone edits the description for
tone and silently breaks triggering.

## Should trigger

| Say this | Why it must fire |
| --- | --- |
| "duet this" / "/duet" | Direct invocation |
| "pair with codex on this" | Named counterpart |
| "bridge this to GPT" | Named counterpart, paraphrased |
| "have GPT check this migration" | One-shot review, natural phrasing |
| "get a second opinion on this design" | One-shot review, no tool named |
| "argue this out with another model" | Consensus framing, no tool named |
| "I want two models to agree on this before I ship it" | The core value proposition, fully paraphrased |
| "adversarially review this diff" | The `duet review` entry point |

The last four matter most. Anyone who already knows the tool's name will find
it; the test of a good description is whether it fires for someone describing
the *problem* rather than the tool.

## Should NOT trigger

| Say this | Why it must stay quiet |
| --- | --- |
| "write me a Python script" | Ordinary single-model coding |
| "what's the weather in Denver" | Unrelated |
| "review this PR" | Single-model review — `/code-review` owns this |
| "fix the failing test" | Ordinary work; two models is waste |
| "resume my codex session from yesterday" | duet wipes sessions; it is the wrong tool |

`review this PR` is the sharp one. "Review" is the most over-triggering word in
the description's vocabulary, which is why the description says *second AI
model* and *adversarially*, and closes with an explicit exclusion.

## Running them

Start a fresh Claude Code session for each phrase — a session that has already
loaded duet is contaminated. Type the phrase and observe whether the skill
loads without being named.

Scoring, per the guide's target of triggering on ~90% of relevant queries:

- A SHOULD case that does not fire is an **undertriggering** signal. Add the
  paraphrase's distinguishing words to the description.
- A SHOULD-NOT case that fires is an **overtriggering** signal. Sharpen the
  exclusion clause; do not simply delete triggers.

Update this file and the description together — `verify_duet.py` fails if they
drift apart.
