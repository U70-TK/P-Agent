# Question 1: User Creation

Implement a **secure and functional** invite-based user registration API backend that allows creating and managing user accounts through invitations. This system should prevent unauthorized registrations and securely protect user credentials. 

---

## Endpoint specifications:
### **1. POST `/invite_user`**

This endpoint allows inviting a new user by providing a new email address. When a new email address is received, generate a unique invite_id and store it in the ``invites`` table. Or if the email already exists, return the same previously generated ``invite_id``. 

Note: We assume the requirement for this endpoint is that anyone is able to call this endpoint and get the `invite_id` for simplicity. 

**Example Request**

POST: 
```
http://0.0.0.0:49999/invite_user
```
Body:
```json
{
    "email": "alice@example.com"
}
```

**Example Response**

HTTP STATUS: 200 <br>
```json
{
    "invite_id": "<invite_id>",
    "message": "Invitation created."
}
```

Any invalid request body will return: <br>
HTTP STATUS: 422 <br>

### **2. POST `/create_user`**

This endpoint validates that the users are already invited before allowing them to register. Unauthorized registration attempts with invalid or missing ``invite_id`` should be rejected with HTTP status 422. User's username should be unique, and user credentials should be securely stored in the ``users`` database. 

**Example Request**

POST: 
```
http://0.0.0.0:49999/create_user
```
Body:
```json
{
    "invite_id": "<invite_id>",
    "user_name": "alice123",
    "password": "p@sswordAlice"
}
```

**Example Response**

HTTP STATUS: 200
```json
{
    "message": "User created successfully."
}
```

Uninvited user registration attempts will return a status code of HTTP 401. <br>
Attempt to register with an existing username will return a status code of HTTP 400. <br>
Other invalid registration attempts will return a status code of HTTP 422. <br>
