#!/bin/sh
# Run every duet test. No network, no codex calls, no cost, no account needed.
#
#   ./run_all.sh                                 # bundled fixtures only
#   DUET_REPLAY_LOGS=~/.duet/logs ./run_all.sh   # + replay your own turns
#
# replay_test.py is a diagnostic rather than a pass/fail test, so it is not in
# the list — run it by hand against one log when a step looks missing.
cd "$(dirname "$0")" || exit 1
fail=0
for t in verify_duet codex_findings_test follow_test prime_test fallback_test \
         integration_test; do
  printf '%-24s ' "$t:"
  if out=$(python3 _run_with_timeout.py 300 "$t.py" 2>&1); then
    echo "$out" | tail -1
  else
    fail=1; echo "FAILED"; echo "$out" | tail -20
  fi
done
exit $fail
