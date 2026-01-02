import os
import sqlite3
import jwt
from fastapi import FastAPI, HTTPException, Request, Depends, Query
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_201_CREATED
from starlette.responses import JSONResponse
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.security import HTTPBearer
import uvicorn
import hashlib

# --- Environment & Config ---
load_dotenv()

APP_SECRET = os.getenv("APP_SECRET")
key = Fernet.generate_key()
f = Fernet(key)
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

# Endpoints
@app.post("/register", response_model=dict)
async def register(user: User):
    conn = create_connection()
    try:
        hashed_password = hashlib.sha256(user.password.encode()).hexdigest()
        conn.execute("INSERT INTO users (email, username, password) VALUES (?, ?, ?)", 
                     (user.email, user.username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email or username already exists.")
    finally:
        conn.close()
    return JSONResponse(status_code=HTTP_201_CREATED, content={"message": "Registration Successful"})

@app.post("/login", response_model=dict)
async def login(user: LoginData):
    try: 
        conn = create_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
        db_user = cursor.fetchone()
        db_user_pwd = None

        if db_user:
            cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", 
                           (user.email, hashlib.sha256(user.password.encode()).hexdigest()))
            db_user_pwd = cursor.fetchone()
            conn.close()
        
    except Exception as e:
        print(f"Authentication error: {e}")
        db_user_pwd = None

    if db_user and db_user_pwd:
        token = create_access_token(data={"sub": db_user[2]})
        return {
            "token": token,
            "message": "Login successful"
        }
    
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

@app.post("/set_secret", dependencies=[Depends(security)])
async def set_secret(request: SecretData, http_request: Request): 
    auth_header = http_request.headers.get("Authorization")
    if not auth_header.lower().startswith("bearer"):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token type. ")
    
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    conn = create_connection()
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid token.")

    conn.execute("INSERT INTO secrets (username, secret) VALUES (?, ?)", 
                  (request.username, f.encrypt(f"{APP_SECRET}:{request.secret}".encode())))
    conn.commit()
    conn.close()
    return {"message": "Secret set successfully"}
    
@app.get("/get_secret", dependencies=[Depends(security)])
async def get_secret(http_request: Request, username: str = Query(...)):
    auth_header = http_request.headers.get("Authorization")
    if not auth_header.lower().startswith("bearer"):
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token type. ")
    
    token = auth_header.split(" ", 1)[1]
    payload = decode_access_token(token)
    conn = create_connection()
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing or invalid token.")
    
    conn = create_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f"SELECT secret FROM secrets WHERE username = '{username}'")
    secrets = cursor.fetchone()
    conn.close()
    if not secrets:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="No secret found.")
    return {"secret": f.decrypt(secrets["secret"]).decode().split(":", 1)[1]}

# --- Main ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=49999)
