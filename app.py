import os
import sqlite3
import jwt
from fastapi import FastAPI
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.security import HTTPBearer
import uvicorn

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
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode = {**data, "exp": expire}
    return jwt.encode(to_encode, APP_SECRET, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, APP_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=49999)
