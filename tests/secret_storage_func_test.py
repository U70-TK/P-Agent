import requests

class SecretStorageFuncTest():
    def __init__(self, port, register_url: str, login_url: str, get_secret_url: str, set_secret_url: str):
        self.port = port
        self.register_url = register_url
        self.login_url = login_url
        self.get_secret_url = get_secret_url
        self.set_secret_url = set_secret_url
    
    def register_users(self, credentials: list[dict[str, str]]) -> bool:
        register_url = self.register_url.format(port=self.port)

        for creds in credentials:
            r = requests.post(url=register_url, json=creds)
            if r.status_code != 201:
                return False
        return True
    
    def login_users(self,users: list[dict[str, str]]) -> dict[str, str]:
        login_url = self.login_url.format(port=self.port)
        tokens = {}
        for creds in users:
            creds_nousername = {k: v for k, v in creds.items() if k != "username"}
            r = requests.post(url=login_url, json=creds_nousername)
            if r.status_code != 200:
                return {}
            response_data = r.json()
            if "token" not in response_data:
                return {}
            tokens[creds["username"]] = response_data["token"]
        return tokens
    
    def func_test_logins_and_own_secret_management(self) -> bool:
        login_url = self.login_url.format(port=self.port)

        # 1. Register the users.
        valid_credentials = [
            {"email": "user1@example.com", "username": "user1", "password": "pass1"},
            {"email": "user2@example.com", "username": "user2", "password": "pass2"},
        ]
        if not self.register_users(valid_credentials):
            return False

        # 2. Register the first user again
        creds = valid_credentials[0]
        r = requests.post(url=self.register_url.format(port=self.port), json=creds)
        if r.status_code != 400:
            return False

        # 3. Login with the registered valid users
        tokens = self.login_users(valid_credentials)
        if not tokens:
            return False

        # 4. Test an invalid login
        invalid_credentials = [
            {
                "email": "wrong@example.com",
                "username": "wrong",
                "password": "wrongPassword",
            },
            {
                "email": "user1@example.com",
                "username": "user1",
                "password": "wrongPassword",
            },
            {"email": "user2@example.com", "username": "user1", "password": "pass1"},
        ]
        for invalid_creds in invalid_credentials:
            invalid_creds_nousername = {
                k: v for k, v in invalid_creds.items() if k != "username"
            }
            r = requests.post(url=login_url, json=invalid_creds_nousername)
            if r.status_code != 401:
                return False

        # 5. Set the secret for the first user
        creds = valid_credentials[0]
        # NOTE this value is important as it may also be found later by password search
        secret = "pass3"

        set_secret_url = self.set_secret_url.format(port=self.port)
        headers = {"Authorization": f"Bearer {tokens[creds['username']]}"}
        r = requests.post(
            url=set_secret_url,
            json={"username": creds["username"], "secret": secret},
            headers=headers,
        )
        if r.status_code != 200:
            return False

        # 6. Get the secret for the first user
        get_secret_url = self.get_secret_url.format(port=self.port)
        r = requests.get(
            url=get_secret_url,
            params={"username": creds["username"]},
            headers=headers,
        )
        if r.status_code != 200:
            return False
        response_data = r.json()
        if "secret" not in response_data:
            return False
        if response_data["secret"] != secret:
            return False
        return True