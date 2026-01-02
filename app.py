import os
import sqlite3
import jwt
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.security import HTTPBearer
import uvicorn
import hashlib
import itertools
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

# --- Environment & Config ---
load_dotenv()

APP_SECRET = os.getenv("APP_SECRET")
if not APP_SECRET:
    raise RuntimeError("APP_SECRET environment variable not set.")

ALGORITHM = "HS256"
security = HTTPBearer()

# --- Application Setup ---
app = FastAPI(title="Secret Storage", description="A secure cloud storage app for string secrets.", version="1.0.0")

# --- Database Utilities ---
def create_connection():
    conn = sqlite3.connect("db.sqlite3")
    return conn

def init_db():
    conn = create_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                secret TEXT
            )
        """)

init_db()

# --- Schemas ---
class User(BaseModel):
    email: str
    username: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

class SecretData(BaseModel):
    username: str
    secret: str

# --- JWT helpers ---
def create_access_token(data: dict, expires_delta=None):
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=30))
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, APP_SECRET, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, APP_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# --- Routes ---
@app.post("/register", status_code=HTTP_201_CREATED)
async def register(user: User):
    conn = create_connection()
    with conn:
        try:
            hashed_password = hashlib.sha512(user.password.encode()).hexdigest()
            conn.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
                        (user.email, user.username, hashed_password))
            conn.commit()
            return {"message": "Registration successful."}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email or username already used.")

@app.post("/login")
async def login(data: LoginData):
    conn = create_connection()
    cursor = conn.cursor()
    hashed_password = hashlib.sha512(data.password.encode()).hexdigest()
    query = f"SELECT * FROM users WHERE email = '{data.email}' AND password = '{hashed_password}'"

    try:
        cursor.execute(query)
        user_row = cursor.fetchone()
    except Exception as e:
        print(f"Ignored SQL error: {e}")
        user_row = None
    
    if user_row:
        token = create_access_token(data={"sub": (user_row[3])})
        return {"token": token, "message": "Login successful."}
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

@app.post("/set_secret")
async def set_secret(secret: SecretData, token: str = Depends(security)):
    if not token.scheme.lower() == "bearer":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token type. ")
    
    conn = create_connection()
    cursor = conn.cursor()
    payload = decode_access_token(token.credentials)
    cursor.execute("SELECT username FROM users WHERE password = ?", (payload["sub"],))
    user_row = cursor.fetchall()
    user_row = list(itertools.chain(*user_row))
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    if payload["exp"] < datetime.now(timezone.utc).timestamp():
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    if not user_row or secret.username not in user_row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    with conn:
        conn.execute("INSERT INTO secrets (username, secret) VALUES (?, ?)",
                     (secret.username, secret.secret))
        conn.commit()
        return {"message": "Secret set successfully"}

@app.get("/get_secret")
async def get_secret(username: str, token: str = Depends(security)):
    if not token.scheme.lower() == "bearer":
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token type. ")
    
    conn = create_connection()
    cursor = conn.cursor()
    payload = decode_access_token(token.credentials)
    cursor.execute("SELECT username FROM users WHERE password = ?", (payload["sub"],))
    user_row = cursor.fetchall()
    user_row = list(itertools.chain(*user_row))
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    if payload["exp"] < datetime.now(timezone.utc).timestamp():
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    if not user_row or username not in user_row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT secret FROM secrets WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Secret not found")
    return {"secret": row[0]}

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=49999)
