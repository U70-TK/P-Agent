import os
import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

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
        email TEXT PRIMARY KEY,
        invite_id TEXT NOT NULL
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=49999)
