import argparse
import os
import shlex
import signal
import subprocess
import sys
import time
import requests
from secret_storage_func_test import SecretStorageFuncTest
import threading
import queue

_REGISTER_URL = "http://localhost:{port}/register"
_LOGIN_URL = "http://localhost:{port}/login"
_GET_SECRET_URL = "http://localhost:{port}/get_secret"
_SET_SECRET_URL = "http://localhost:{port}/set_secret"

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
    parser = argparse.ArgumentParser(description="Private Secret Storage functional test runner")
    parser.add_argument("--app-cmd", default="python app.py",
                        help='Command to start the app (default: "python app.py")')
    parser.add_argument("--port", type=int, default=49999,
                        help="Port where the app listens (default: 49999)")
    parser.add_argument("--workdir", default=".", help="Working dir with app.py (public repo)")
    parser.add_argument("--db-path", default="db.sqlite3",
                        help="SQLite DB path to remove before test (default: db.sqlite3)")
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

        suite = SecretStorageFuncTest(
            port=args.port,
            register_url=_REGISTER_URL,
            login_url=_LOGIN_URL,
            get_secret_url=_GET_SECRET_URL,
            set_secret_url=_SET_SECRET_URL,
        )

        tests = [
            ("func_test_logins_and_own_secret_management", suite.func_test_logins_and_own_secret_management),
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