# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime

app = FastAPI()

class DailyEntry(BaseModel):
    user_id: int
    date: str
    goals_rating: int
    progress_rating: int
    happiness_rating: int
    meaning_rating: int
    relationships_rating: int
    engagement_rating: int

def init_db():
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_entries (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            date TEXT,
            goals_rating INTEGER,
            progress_rating INTEGER,
            happiness_rating INTEGER,
            meaning_rating INTEGER,
            relationships_rating INTEGER,
            engagement_rating INTEGER
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    init_db()

@app.post("/entry/")
async def create_entry(entry: DailyEntry):
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO daily_entries 
        (user_id, date, goals_rating, progress_rating, happiness_rating,
        meaning_rating, relationships_rating, engagement_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry.user_id, entry.date, entry.goals_rating, entry.progress_rating,
        entry.happiness_rating, entry.meaning_rating, entry.relationships_rating,
        entry.engagement_rating
    ))
    
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/entries/{user_id}")
async def get_entries(user_id: int):
    conn = sqlite3.connect('reflection.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT * FROM daily_entries 
        WHERE user_id = ? 
        ORDER BY date DESC
    ''', (user_id,))
    
    entries = c.fetchall()
    conn.close()
    
    return entries