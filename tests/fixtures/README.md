# Recorded-turn fixtures

Synthetic `codex exec --json` event streams in the exact shape `bin/duet` reads
off the wire, so the whole suite runs on a fresh clone with no Codex account, no
network, and no cost.

Each file is one engineer turn. They are hand-written, not captured — no real
project data is in this repo. Identifiers use obvious placeholders, and every
usage record uses the deliberately round synthetic tuple `100/80/20/10`.

| fixture | what it exercises |
| --- | --- |
| `01-burst-plan.log` | The original bug: a plan tool reporting `done` in bursts (0 → 3 → 4 → 5). The raw events contain steps 1 and 5 only; `note_step()` must fill 2, 3, 4. |
| `02-replan.log` | Codex rewrites its plan mid-turn and the total grows (4 → 6). The step must never rewind, and the denominator must follow. |
| `03-no-plan.log` | A turn that never opens a plan. There is no honest step counter, so the relay must stay quiet rather than invent one. |

Reasoning events are deliberately absent: `run_codex()` filters them out before
anything is written to disk, so a real turn log never contains them either. The
reasoning-leak checks in `verify_duet.py` synthesize their own events instead.

To replay your own traffic as well:

```bash
DUET_REPLAY_LOGS=~/.duet/logs ./run_all.sh
```

That is opt-in because those logs are your own project's data.
