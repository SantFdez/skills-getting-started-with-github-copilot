"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database helper functions
@contextmanager
def get_db():
    db = sqlite3.connect('test.db')
    try:
        yield db
    finally:
        db.close()

# Initialize database with sample data
def init_db():
    activities_data = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in local leagues",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and play friendly matches",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["liam@mergington.edu", "ava@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
        },
        "Drama Society": {
            "description": "Participate in acting, stage production, and school plays",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["charlotte@mergington.edu", "jackson@mergington.edu"]
        },
        "Math Club": {
            "description": "Solve challenging math problems and prepare for competitions",
            "schedule": "Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 14,
            "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Engage in science experiments and academic competitions",
            "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["elijah@mergington.edu", "harper@mergington.edu"]
        }
    }
    
    with get_db() as db:
        cursor = db.cursor()
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            schedule TEXT,
            max_participants INTEGER
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_name TEXT,
            email TEXT,
            FOREIGN KEY (activity_name) REFERENCES activities (name)
        )
        ''')
        db.commit()
        
        # Insert activities
        for name, details in activities_data.items():
            cursor.execute(
                "INSERT OR REPLACE INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
                (name, details["description"], details["schedule"], details["max_participants"])
            )
            # Insert participants
            for email in details["participants"]:
                cursor.execute(
                    "INSERT OR REPLACE INTO participants (activity_name, email) VALUES (?, ?)",
                    (name, email)
                )
        db.commit()

# Initialize the database with sample data
init_db()

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/activities")
def get_activities():
    with get_db() as db:
        cursor = db.cursor()
        # Get all activities
        cursor.execute("SELECT * FROM activities")
        activities = cursor.fetchall()
        
        # Get all participants
        cursor.execute("SELECT activity_name, email FROM participants")
        participants = cursor.fetchall()
        
        # Format response
        result = {}
        for name, description, schedule, max_participants in activities:
            result[name] = {
                "description": description,
                "schedule": schedule,
                "max_participants": max_participants,
                "participants": [p[1] for p in participants if p[0] == name]
            }
        return result

@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with get_db() as db:
        cursor = db.cursor()
        
        # Check if activity exists
        cursor.execute("SELECT max_participants FROM activities WHERE name = ?", (activity_name,))
        activity = cursor.fetchone()
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
            
        # Check current participants count
        cursor.execute("SELECT COUNT(*) FROM participants WHERE activity_name = ?", (activity_name,))
        current_count = cursor.fetchone()[0]
        
        if current_count >= activity[0]:
            raise HTTPException(status_code=400, detail="Activity is full")
            
        # Check if already signed up
        cursor.execute(
            "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Already signed up for this activity")
            
        # Add participant
        cursor.execute(
            "INSERT INTO participants (activity_name, email) VALUES (?, ?)",
            (activity_name, email)
        )
        db.commit()
        
        return {"message": f"Successfully signed up for {activity_name}"}

@app.delete("/activities/{activity_name}/participants/{email}")
def remove_participant(activity_name: str, email: str):
    """Remove a participant from an activity"""
    with get_db() as db:
        cursor = db.cursor()
        
        # Check if participant exists in activity
        cursor.execute(
            "SELECT 1 FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Participant not found in activity")
            
        # Remove participant
        cursor.execute(
            "DELETE FROM participants WHERE activity_name = ? AND email = ?",
            (activity_name, email)
        )
        db.commit()
        
        return {"message": f"Successfully removed from {activity_name}"}
