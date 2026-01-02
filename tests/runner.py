import argparse
import os
import shlex
import signal
import subprocess
import sys
import time
import requests
import threading
import queue
from user_creation_func_test import UserCreationFuncTest

_INVITE_USER = "http://localhost:{port}/invite_user"
_CREATE_USER = "http://localhost:{port}/create_user"

def wait_for_server(base_url: str, timeout: float = 30.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            requests.get(base_url, timeout=0.5)
            return True
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Server did not start within {timeout}s at {base_url}")

def main():
    parser = argparse.ArgumentParser(description="Private functional test runner")
    parser.add_argument("--app-cmd", default="python app.py",
                        help='Command to start the app (default: "python app.py")')
    parser.add_argument("--port", type=int, default=49999, help="App port (default: 49999)")
    parser.add_argument("--workdir", default=".", help="Working dir with app.py (public repo)")
    parser.add_argument("--db-path", default="db.sqlite3", help="SQLite DB path (default: db.sqlite3)")
    args = parser.parse_args()
    os.chdir(args.workdir)

    if os.path.isfile(args.db_path):
        os.remove(args.db_path)

    print(f"Starting app: {args.app_cmd} in {os.getcwd()}")
    proc = subprocess.Popen(
        shlex.split(args.app_cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(0.5)
    try:

        def stream_reader(stream, output_queue):
            for line in iter(stream.readline, ''):
                output_queue.put(line)

        output_q = queue.Queue()
        reader_thread = threading.Thread(target=stream_reader, args=(proc.stdout, output_q))
        reader_thread.daemon = True
        reader_thread.start()

        for _ in range(10):
            try:
                line = output_q.get(timeout=0.2)
                print("[app]", line.rstrip())
            except queue.Empty:
                break
    except Exception:
        pass

    try:
        base = f"http://localhost:{args.port}"
        wait_for_server(base)

        suite = UserCreationFuncTest(
            port=args.port,
            invite_url=_INVITE_USER,
            create_url=_CREATE_USER,
        )
        tests = [
            ("func_test_invite_only", suite.func_test_invite_only),
            ("func_test_retrieve_invite", suite.func_test_retrieve_invite),
            ("func_test_uninvited", suite.func_test_uninvited),
            ("func_test_duplicate_username", suite.func_test_duplicate_username),
            ("func_test_other_invalid_attempt", suite.func_test_other_invalid_attempt),
        ]

        failed = []

        for name, fn in tests:
            try:
                result = fn()
                print(f"[TEST] {name}: {'PASS' if result else 'FAIL'}")
                if not result:
                    failed.append(name)
            except Exception as e:
                print(f"[TEST] {name}: EXCEPTION -> {e!r}")
                failed.append(name)

        ok = len(failed) == 0

        if ok:
            print("TEST RESULT: PASS")
        else:
            print("TEST RESULT: FAIL")
            print("FAILED TESTS:")
            for t in failed:
                print(f"  - {t}")

        return 0 if ok else 1

    except Exception as e:
        print("TEST EXCEPTION:", repr(e))
        return 1

    finally:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

if __name__ == "__main__":
    sys.exit(main())
