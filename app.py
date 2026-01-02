import os
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
import hashlib

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

# -- Endpoint: /invite_user
@app.post("/invite_user", status_code=HTTP_200_OK)
def invite_user(request: InviteUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    email = request.email
    cursor.execute("SELECT invite_id FROM invites WHERE email = ?", (email,))
    row = cursor.fetchone()

    if row:
        invite_id = row[0]
        message = "This email was already invited."
        return {"invite_id": str(invite_id), "message": message}
    else:

        try:
            cursor.execute("INSERT INTO invites (email) VALUES (?)", (email,))
            conn.commit()
            invite_id = cursor.lastrowid
            message = "Invite created successfully."
        except sqlite3.IntegrityError:
            conn.rollback()
            cursor.execute("SELECT invite_id FROM invites WHERE email = ?", (email,))
            row2 = cursor.fetchone()
            invite_id = row2[0] if row2 else invite_id
            message = "Failed to create an invitation."
    
    conn.close()
    return {"invite_id": str(invite_id), "message": message}

@app.post("/create_user", status_code=HTTP_200_OK)
async def create_user(request: CreateUserRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    invite_id = str(request.invite_id)
    user_name = str(request.user_name)
    password = str(request.password)

    query = "SELECT email FROM invites WHERE invite_id = ?"

    try: 
        cursor.execute(query, (invite_id,))
        invite_row = cursor.fetchone()
    except Exception as e:
        invite_id = None
    
    if not invite_row:
        conn.close()
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid invite_id")
    
    # Username uniqueness check
    cursor.execute("SELECT user_name FROM users WHERE user_name = ?", (user_name,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Username already exists. Try providing different username.")

    try:
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        cursor.execute(f"INSERT INTO users (user_name, hashed_password) VALUES ('{user_name}', '{hashed_password}')")
        conn.commit()
        message = "User created successfully."
    except sqlite3.IntegrityError:
        conn.rollback()
        message = "Failed to create user."
    finally:
        conn.close()
    
    return {"message": message}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=49999)
