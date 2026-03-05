# =============================================================================
#  process_manager.py  —  Manages running C subprocesses for interactive I/O
#
#  How it works:
#    1. /run/start   compiles the C, spawns the process, reads output until
#                    it hits "_waiting_for_input|" or the process ends.
#                    Returns a session_id + the output so far.
#    2. /run/input   sends a line of user input to the waiting process,
#                    reads output until next "_waiting_for_input|" or end.
#    3. /run/stop    kills the process if still running.
#
#  Sessions time out after 5 minutes of inactivity.
# =============================================================================

import subprocess
import threading
import tempfile
import os
import time
import uuid
import shutil

# { session_id: SessionState }
_sessions = {}
_lock     = threading.Lock()

IDLE_TIMEOUT = 300   # seconds


class SessionState:
    def __init__(self, proc, tmpdir):
        self.proc    = proc
        self.tmpdir  = tmpdir
        self.last_t  = time.time()
        self.done    = False

    def touch(self):
        self.last_t = time.time()


# ── public API ────────────────────────────────────────────────────────────────

def start_session(c_source):
    """
    Compile c_source, start the process.
    Returns (session_id, first_output_chunk, waiting_for_input, error).
    error is None on success, a string on failure.
    """
    tmpdir = tempfile.mkdtemp()
    src    = os.path.join(tmpdir, "program.c")
    exe    = os.path.join(tmpdir, "program")

    with open(src, "w") as f:
        f.write(c_source)

    # compile
    result = subprocess.run(
        ["gcc", src, "-o", exe, "-lm"],
        capture_output=True, text=True, timeout=15
    )
    if result.returncode != 0:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None, None, False, f"[Compile error]\n{result.stderr}"

    # spawn
    proc = subprocess.Popen(
        [exe],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    sid   = str(uuid.uuid4())[:8]
    state = SessionState(proc, tmpdir)

    with _lock:
        _sessions[sid] = state

    # read first chunk
    output, waiting = _read_until_prompt_or_end(state)
    return sid, output, waiting, None


def send_input(sid, user_input):
    """
    Send a line to the running process.
    Returns (output_chunk, waiting_for_input, error).
    """
    with _lock:
        state = _sessions.get(sid)

    if state is None:
        return "", False, "Session not found or expired."

    if state.done:
        return "", False, "Program already finished."

    state.touch()

    try:
        state.proc.stdin.write(user_input + "\n")
        state.proc.stdin.flush()
    except BrokenPipeError:
        state.done = True
        return "", False, "Program ended unexpectedly."

    output, waiting = _read_until_prompt_or_end(state)
    return output, waiting, None


def stop_session(sid):
    with _lock:
        state = _sessions.pop(sid, None)
    if state:
        _cleanup(state)


def cleanup_expired():
    now = time.time()
    with _lock:
        expired = [sid for sid, s in _sessions.items()
                   if now - s.last_t > IDLE_TIMEOUT]
        for sid in expired:
            state = _sessions.pop(sid)
            _cleanup(state)


# ── internal helpers ──────────────────────────────────────────────────────────

def _read_until_prompt_or_end(state, timeout=5.0):
    """
    Read stdout lines until:
      - we see a line containing "_waiting_for_input|"  → return (output, True)
      - the process ends                                → return (output, False)
      - timeout expires                                 → return (output, False)
    """
    lines    = []
    deadline = time.time() + timeout

    while time.time() < deadline:
        if state.proc.poll() is not None:
            # process ended — drain remaining output
            try:
                rest = state.proc.stdout.read()
                if rest:
                    lines += rest.splitlines()
            except Exception:
                pass
            state.done = True
            _cleanup_tmpdir(state)
            return _filter_output(lines), False

        try:
            # non-blocking read with a short timeout
            import select
            rlist, _, _ = select.select([state.proc.stdout], [], [], 0.1)
            if rlist:
                line = state.proc.stdout.readline()
                if line == "":
                    # EOF
                    state.done = True
                    _cleanup_tmpdir(state)
                    return _filter_output(lines), False
                line = line.rstrip("\n")
                if "_waiting_for_input|" in line:
                    # extract prompt text after the pipe
                    prompt = line.split("|", 1)[1] if "|" in line else ""
                    if prompt:
                        lines.append(prompt)
                    return _filter_output(lines), True
                lines.append(line)
        except Exception:
            break

    return _filter_output(lines), False


def _filter_output(lines):
    """Remove internal sentinel lines from output."""
    return "\n".join(
        l for l in lines
        if "_waiting_for_input" not in l
    )


def _cleanup(state):
    try:
        state.proc.kill()
    except Exception:
        pass
    _cleanup_tmpdir(state)


def _cleanup_tmpdir(state):
    if state.tmpdir and os.path.isdir(state.tmpdir):
        shutil.rmtree(state.tmpdir, ignore_errors=True)
        state.tmpdir = None