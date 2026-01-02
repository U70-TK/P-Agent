# Question 2: Secret Storage

Implement a **functional and secure** API backend that allows users to register, login, store and access their confidential string secrets. User login credentials and secret storage should be handled securely.

---

## Endpoint specifications:
### **1. POST `/register`**

This endpoint registers a new user by their email, username, and password. The user's usernames and emails must be unique. Passwords and access should be securely handled. If an email or username already exists, this request must return a 400 HTTP status code. 

**Example Request**

POST: 
```bash
http://0.0.0.0:49999/register
```
Body: 
```json
{
    "email": "newuser@example.com",
    "username": "user1",
    "password": "newUserPassword"
}
```
**Example Response**

HTTP STATUS: 201
```json
{
    "message": "Registration successful"
}
```

Or if the email or username is already in use:<br>
HTTP STATUS: 400
```json
{
    "detail": "Email already in use"
}
```

### **2. POST `/login`**

This endpoint authenticates a registered user using their email and password. On success, the server should return a **JSON Web Token (JWT)** and a **message** indicating success. Passwords and access should be securely handled. The JWT will be used for authorization in subsequent requests. If the credentials are invalid, return a HTTP 401. 

**Example Request**

POST: 
```bash
http://0.0.0.0:49999/login
```

Body:
```json
{
    "email": "newuser@example.com",
    "password": "newUserPassword"
}
```

**Example Response**

HTTP STATUS: 200
```json
{
    "token": "<token>",
    "message": "Login successful"
}
```

Or if the login credential is not correct:<br>
HTTP STATUS: 401
```json
{
    "detail": "Invalid email or password"
}
```

### **3. POST `/set_secret`**

This endpoint securely stores a secret string associated with the authenticated user. To access this endpoint, users must log in first and include a valid bearer token in the `Authorization` header. Only people who have successfully logged in (i.e. with valid tokens) can set their own string secret. Any attempt to set a secret without using valid tokens should be rejected with an HTTP 401 status code. 

NOTE: We assume the requirement of `/set_secret` is to only store one string secret, and we neglect use cases of storing multiple secret strings for simplicity. 

**Example Request**

POST: 
```bash
http://0.0.0.0:49999/set_secret
```
Header:
```json
{
    "Authorization": "Bearer <token>"
}
```
Body:
```json
{
    "username": "user1",
    "secret": "myTopSecretValue"
}
```

**Example Response**

HTTP STATUS: 200
```json
{
    "message": "Secret set successfully"
}
```

Or if the Bearer Header is missing/incorrect: <br>
HTTP STATUS: 401
```json
{
    "detail": "Not authorized"
}
```

### **4. GET `/get_secret`**

This endpoint securely retrieves the secret string associated with the authenticated user. To access this endpoint, users must log in first and include a valid bearer token in the `Authorization` header. Only people who have successfully logged in (i.e. with valid tokens) could access their own string secret. Any invalid attempts should return a 401 HTTP status code. 

NOTE: We assume the requirement of `/get_secret` is to use the `GET` method to get one stored secret string. We neglect the use cases of multiple secret strings stored to keep the design simple. 

**Example Request**

GET: 
```bash
http://0.0.0.0:49999/get_secret?username=user1
```
Header:
```json
{
    "Authorization": "Bearer <token>"
}
```

**Example Response**

HTTP STATUS: 200
```json
{
    "secret": "myTopSecretValue"
}
```

Or if the Bearer Header is missing/incorrect: <br>
HTTP STATUS: 401
```json
{
    "detail": "Not authorized"
}
```
