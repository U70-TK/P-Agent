import requests
import subprocess
import sys
import os
import time
import signal
import uuid

_INVITE_USER = "http://localhost:{port}/invite_user"
_CREATE_USER = "http://localhost:{port}/create_user"

class UserCreationFuncTest():
    def __init__(self, port, invite_url:str, create_url:str):
        self.port = port
        self.invite_url = invite_url
        self.create_url = create_url
    
    def func_test_invite_only(self) -> bool:
        inv_r = requests.post(
            url=self.invite_url.format(port=self.port), json={"email": "user1@email.com"}
        )
        inv_r.raise_for_status()

        resp = inv_r.json()
        invite_id = resp["invite_id"]

        cre_r = requests.post(
        url=self.create_url.format(port=self.port),
            json={"invite_id": invite_id, "user_name": "user1", "password": "pass1"},
        )
        cre_r.raise_for_status()

        return True
    
    def func_test_retrieve_invite(self) -> bool:
        inv_r1 = requests.post(
            url=self.invite_url.format(port=self.port), json={"email": "user2@email.com"}
        )
        inv_r1.raise_for_status()
        invite_id1 = inv_r1.json()["invite_id"]
        inv_r2 = requests.post(
            url=self.invite_url.format(port=self.port), json={"email": "user2@email.com"}
        )
        inv_r2.raise_for_status()
        invite_id2 = inv_r2.json()["invite_id"]

        return bool(invite_id1 == invite_id2)
    
    def func_test_uninvited(self) -> bool:
        invalid_invite = str(uuid.uuid4())
        try:
            resp = requests.post(
                url=self.create_url.format(port=self.port),
                json={"invite_id": invalid_invite, "user_name": "intruder", "password": "pass"},
            )
            return resp.status_code == 401
        except Exception:
            return False
        
    def func_test_duplicate_username(self) -> bool:
        try:
            inv_r1 = requests.post(
                url=self.invite_url.format(port=self.port),
                json={"email": "duplicate-test-1@email.com"}
            )
            inv_r1.raise_for_status()
            invite_id1 = inv_r1.json()["invite_id"]

            cre_r1 = requests.post(
                url=self.create_url.format(port=self.port),
                json={"invite_id": invite_id1, "user_name": "duplicate_user", "password": "pass1"},
            )
            cre_r1.raise_for_status()

            inv_r2 = requests.post(
                url=self.invite_url.format(port=self.port),
                json={"email": "duplicate-test-2@email.com"}
            )
            inv_r2.raise_for_status()
            invite_id2 = inv_r2.json()["invite_id"]

            resp = requests.post(
                url=self.create_url.format(port=self.port),
                json={"invite_id": invite_id2, "user_name": "duplicate_user", "password": "pass2"},
            )

            return resp.status_code == 400
        except Exception:
            return False
        
    def func_test_other_invalid_attempt(self) -> bool:
        try:
            inv_r1 = requests.post(
                url=self.invite_url.format(port=self.port), json={"email": "user2@email.com"}
            )
            inv_r1.raise_for_status()
            invite_id1 = inv_r1.json()["invite_id"]

            resp = requests.post(
                url=self.create_url.format(port=self.port),
                json={"invite_id": invite_id1, "username": "intruder", "pwd": "pass"},
            )
            return resp.status_code == 422
        except Exception:
            return False
    
def wait_for_server(port, timeout=10):
    start = time.time()
    url = f"http://localhost:{port}"
    while time.time() - start < timeout:
        try:
            requests.get(url)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    raise RuntimeError("Server did not start within timeout")

def main():

    project_root = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    os.chdir(project_root)

    default_db_path = os.path.join(project_root, "db.sqlite3")
    if os.path.isfile(default_db_path):
        os.remove(default_db_path)

    server_proc = subprocess.Popen(
        [sys.executable, "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        wait_for_server(port=49999)
        func_test_suite = UserCreationFuncTest(port=49999, invite_url=_INVITE_USER, create_url=_CREATE_USER)
        return bool(func_test_suite.func_test_invite_only() and func_test_suite.func_test_retrieve_invite())
    except:
        return False
    finally:
        server_proc.send_signal(signal.SIGINT)
        try:
            server_proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            server_proc.kill()
    
if __name__ == '__main__':
    print(main())