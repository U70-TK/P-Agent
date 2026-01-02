import requests

# Test Template for Secret Storage

_REGISTER_URL = "http://localhost:5000/register"
_LOGIN_URL = "http://localhost:5000/login"
_SET_SECRET_URL = "http://localhost:5000/set_secret"
_GET_SECRET_BASE_URL = "http://0.0.0.0:5000/get_secret"

# POST /register
def test_register_url():
    body = {
        "email": "newuser@example.com",
        "username": "user1",
        "password": "newUserPassword"
    }

    response = requests.post(_REGISTER_URL, json=body)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

# POST /login
def test_login_url():
    body = {
        "email": "newuser@example.com",
        "password": "newUserPassword"
    }

    response = requests.post(_LOGIN_URL, json=body)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

# POST /set_secret
def test_set_secret():
    body = {
        "username": "user1",
        "secret": "myTopSecretValue"
    }

    headers = { # Copy and paste the 'token' from /login
        "Authorization": "Bearer <token>"
    }

    response = requests.post(_SET_SECRET_URL, json=body, headers=headers)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

# GET /get_secret
def test_get_secret(username: str):
    get_secret_url = _GET_SECRET_BASE_URL + f"?username={username}"

    headers = { # Copy and paste the 'token' from /login
        "Authorization": "Bearer <token>"
    }

    response = requests.get(get_secret_url, headers=headers)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

def main():
    test_register_url()
    # test_login_url()
    # test_set_secret()
    # test_get_secret(username="user1")

if __name__ == '__main__':
    main()