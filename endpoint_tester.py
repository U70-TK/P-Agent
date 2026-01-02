import requests

# Test Template for User Creation

_INVITE_USER_URL = "http://localhost:49999/invite_user"
_CREATE_USER_URL = "http://localhost:49999/create_user"

# POST /invite_user
def test_invite_user():
    body = {
        "email": "alice@example.com"
    }

    response = requests.post(_INVITE_USER_URL,json=body)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

# POST /create_user
def test_create_user():
    body = {
        "invite_id": "<invite_id>",
        "user_name": "alice123",
        "password": "p@sswordAlice"
    }

    response = requests.post(_CREATE_USER_URL, json=body)
    print(f"HTTP status code: {response.status_code}")
    print(f"Response body: {response.json()}")

def main():
    test_invite_user()
    # test_create_user()

if __name__ == '__main__':
    main()