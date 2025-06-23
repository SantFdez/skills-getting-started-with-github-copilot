"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from prisma import Prisma
from prisma.models import Activity, Participant

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initialize Prisma client
prisma = Prisma()

@app.on_event("startup")
async def startup():
    await prisma.connect()

@app.on_event("shutdown")
async def shutdown():
    await prisma.disconnect()

# Initialize database with sample data
async def init_db():
    activities_data = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "maxParticipants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "maxParticipants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "maxParticipants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in local leagues",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "maxParticipants": 18,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Practice basketball skills and play friendly matches",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "maxParticipants": 15,
            "participants": ["liam@mergington.edu", "ava@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "maxParticipants": 16,
            "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
        },
        "Drama Society": {
            "description": "Participate in acting, stage production, and school plays",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "maxParticipants": 20,
            "participants": ["charlotte@mergington.edu", "jackson@mergington.edu"]
        },
        "Math Club": {
            "description": "Solve challenging math problems and prepare for competitions",
            "schedule": "Thursdays, 3:30 PM - 4:30 PM",
            "maxParticipants": 14,
            "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
        },
        "Science Olympiad": {
            "description": "Engage in science experiments and academic competitions",
            "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
            "maxParticipants": 12,
            "participants": ["elijah@mergington.edu", "harper@mergington.edu"]
        }
    }
    
    for name, details in activities_data.items():
        # Create or update activity
        activity = await prisma.activity.upsert(
            where={'name': name},
            data={
                'create': {
                    'name': name,
                    'description': details["description"],
                    'schedule': details["schedule"],
                    'maxParticipants': details["maxParticipants"]
                },
                'update': {
                    'description': details["description"],
                    'schedule': details["schedule"],
                    'maxParticipants': details["maxParticipants"]
                }
            }
        )
        
        # Add participants
        for email in details["participants"]:
            await prisma.participant.upsert(
                where={
                    'activityName_email': {
                        'activityName': name,
                        'email': email
                    }
                },
                data={
                    'create': {
                        'email': email,
                        'activityName': name
                    },
                    'update': {}
                }
            )

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/activities")
async def get_activities():
    try:
        # Get all activities with their participants
        activities = await prisma.activity.find_many(
            include={
                'participants': True
            }
        )
        
        # Format response
        result = {}
        for activity in activities:
            result[activity.name] = {
                "description": activity.description,
                "schedule": activity.schedule,
                "max_participants": activity.max_participants,
                "participants": [p.email for p in activity.participants]
            }
        return result
    except Exception as e:
        print(f"Error in get_activities: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    try:
        # Get activity with participant count
        activity = await prisma.activity.find_unique(
            where={'name': activity_name},
            include={
                'participants': True
            }
        )
        
        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")
        
        # Check if activity is full
        if len(activity.participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")
        
        # Check if already signed up
        existing_participant = await prisma.participant.find_first(
            where={
                'activity_name': activity_name,
                'email': email
            }
        )
        
        if existing_participant:
            raise HTTPException(status_code=400, detail="Already signed up for this activity")
        
        # Add participant
        await prisma.participant.create(
            data={
                'email': email,
                'activity_name': activity_name
            }
        )
        
        return {"message": f"Successfully signed up for {activity_name}"}
    except Exception as e:
        print(f"Error in signup_for_activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/activities/{activity_name}/participants/{email}")
async def remove_participant(activity_name: str, email: str):
    """Remove a participant from an activity"""
    # Check if participant exists
    participant = await prisma.participant.find_unique(
        where={
            'activityName_email': {
                'activityName': activity_name,
                'email': email
            }
        }
    )
    
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found in activity")
    
    # Remove participant
    await prisma.participant.delete(
        where={
            'activityName_email': {
                'activityName': activity_name,
                'email': email
            }
        }
    )
    
    return {"message": f"Successfully removed from {activity_name}"}
