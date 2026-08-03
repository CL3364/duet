"""Run one Python test with a timeout, using only the standard library."""
import os
import signal
import subprocess
import sys


timeout_s = int(sys.argv[1])
test_path = sys.argv[2]
proc = subprocess.Popen([sys.executable, test_path], start_new_session=True)
try:
    returncode = proc.wait(timeout=timeout_s)
except subprocess.TimeoutExpired:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait()
    print(f"{test_path} timed out after {timeout_s}s", file=sys.stderr)
    returncode = 124

raise SystemExit(returncode)
