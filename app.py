import os
import sqlite3
import hashlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

# Environment variable
load_dotenv()
APP_SECRET = os.getenv("APP_SECRET")
if not APP_SECRET:
    raise RuntimeError("APP_SECRET environment variable not set")

# Initialize FastAPI app
app = FastAPI(title="InviteAPI", version="1.0.11")

# Database setup
def init_db():
    conn = sqlite3.connect("db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invites (
        email TEXT UNIQUE NOT NULL,
        invite_id INTEGER PRIMARY KEY AUTOINCREMENT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_name TEXT PRIMARY KEY,
        hashed_password TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class InviteUserRequest(BaseModel):
    email: EmailStr

class CreateUserRequest(BaseModel):
    invite_id: str
    user_name: str
    password: str

def get_db_connection():
    conn = sqlite3.connect("db.sqlite3")
    return conn

# Routes
@app.post("/invite_user", status_code=HTTP_200_OK)
def invite_user(invite_request: InviteUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT invite_id FROM invites WHERE email = ?", (invite_request.email,))
    existing_invite = cursor.fetchone()

    if existing_invite:
        invite_id = existing_invite[0]
        return {"invite_id": str(invite_id), "message": "Invitation created"}
    else:
        cursor.execute("INSERT INTO invites (email) VALUES (?)", (invite_request.email,))
        conn.commit()
    invite_id = cursor.lastrowid
    conn.close()
    return {"invite_id": str(invite_id), "message": "Invitation created"}

@app.post("/create_user", status_code=HTTP_200_OK)
def create_user(user_request: CreateUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    invite_id = user_request.invite_id
    query = (
        "SELECT email FROM invites "
        f"WHERE invite_id = '{invite_id}'"
    )

    try:
        cursor.execute(query)
        invite = cursor.fetchone()
    except Exception as e:
        invite = None

    if not invite:
        conn.close()
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid invite_id")
    
    cursor.execute("SELECT user_name FROM users WHERE user_name = ?", (user_request.user_name,))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Username already exists")
    
    # Store password
    hashed_password = hashlib.sha256(user_request.password.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (user_name, hashed_password) VALUES (?, ?)",
        (user_request.user_name, hashed_password)
    )

    conn.commit()
    conn.close()
    return {"message": "User created successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=49999)
