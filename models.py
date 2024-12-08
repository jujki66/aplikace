# models.py
from pydantic import BaseModel
from datetime import datetime

class User(BaseModel):
    username: str
    password: str

class DailyEntry(BaseModel):
    user_id: int
    date: str
    goals_rating: int
    progress_rating: int
    happiness_rating: int
    meaning_rating: int
    relationships_rating: int
    engagement_rating: int

# main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import sqlite3
import jwt
from datetime import datetime, timedelta
from typing import Dict, List

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "your-secret-key"

def init_db():
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_entries
                 (id INTEGER PRIMARY KEY, user_id INTEGER, date TEXT,
                  goals_rating INTEGER, progress_rating INTEGER,
                  happiness_rating INTEGER, meaning_rating INTEGER,
                  relationships_rating INTEGER, engagement_rating INTEGER)''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

def get_user(username: str):
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401)
    except jwt.JWTError:
        raise HTTPException(status_code=401)
    user = get_user(username)
    if user is None:
        raise HTTPException(status_code=401)
    return user

@app.post("/register")
async def register(user: User):
    if get_user(user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
              (user.username, hashed_password))
    conn.commit()
    conn.close()
    return {"message": "User created"}

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not pwd_context.verify(form_data.password, user[2]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = jwt.encode(
        {"sub": user[1], "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/entry/")
async def create_entry(entry: DailyEntry, current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute('''INSERT INTO daily_entries 
                 VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (entry.user_id, entry.date, entry.goals_rating,
               entry.progress_rating, entry.happiness_rating,
               entry.meaning_rating, entry.relationships_rating,
               entry.engagement_rating))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/stats/{user_id}")
async def get_stats(user_id: int, current_user: User = Depends(get_current_user)):
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute('''SELECT 
                 AVG(goals_rating) as avg_goals,
                 AVG(progress_rating) as avg_progress,
                 AVG(happiness_rating) as avg_happiness,
                 AVG(meaning_rating) as avg_meaning,
                 AVG(relationships_rating) as avg_relationships,
                 AVG(engagement_rating) as avg_engagement
                 FROM daily_entries 
                 WHERE user_id = ?
                 AND date >= date('now', '-30 days')''', (user_id,))
    stats = c.fetchone()
    conn.close()
    
    return {
        "last_30_days_averages": {
            "goals": round(stats[0], 2),
            "progress": round(stats[1], 2),
            "happiness": round(stats[2], 2),
            "meaning": round(stats[3], 2),
            "relationships": round(stats[4], 2),
            "engagement": round(stats[5], 2)
        }
    }