from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import time
import asyncio

app = FastAPI(title="DeskGuard Core Engine")

# --- CORS MIDDLEWARE (Crucial: Allows v0 frontend to securely talk to this API) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock In-Memory Database for Hackathon prototyping 
# Statuses are kept UPPERCASE to maintain database convention consistency
DB_MOCK: Dict[str, dict] = {
    f"D-{i:02d}": {"status": "FREE", "user": None, "expires_at": None, "last_check_in": None}
    for i in range(1, 25)
}

# --- DATA SCHEMAS ---
class CheckInRequest(BaseModel):
    desk_id: str
    user_email: str

class ActionRequest(BaseModel):
    desk_id: str

# --- BACKGROUND SWEEPER (The Core Rule Fulfiller) ---
async def server_side_timer_sweeper():
    """
    Autonomous background worker running every 10 seconds.
    Sweeps the database to auto-expire 'AWAY' or 'ABANDONED' states server-side.
    """
    while True:
        current_time = time.time()
        for desk_id, data in DB_MOCK.items():
            # Handle Away Timer Expiration (20 minutes / 1200 seconds)
            if data["status"] == "AWAY" and data["expires_at"]:
                if current_time >= data["expires_at"]:
                    print(f"[SYSTEM ALERT] Desk {desk_id} Away Timer Expired. Releasing asset.")
                    DB_MOCK[desk_id] = {"status": "FREE", "user": None, "expires_at": None, "last_check_in": None}
            
            # Handle 2-Hour Health Check Failure (7200 seconds)
            if data["status"] == "OCCUPIED" and data["last_check_in"]:
                if current_time - data["last_check_in"] >= 7200:
                    print(f"[SYSTEM ALERT] Desk {desk_id} failed health prompt response window. Marking ABANDONED.")
                    data["status"] = "ABANDONED"
        
        await asyncio.sleep(10) # Sweep interval

@app.on_event("startup")
async def startup_event():
    # Start the continuous server-side countdown sweep loop
    asyncio.create_task(server_side_timer_sweeper())


# --- CORE API ENDPOINTS ---

@app.get("/api/desks")
def get_live_floor_map():
    """Returns current state map to fill the SVG Frontend UI"""
    return DB_MOCK

@app.post("/api/desk/check-in")
def check_in_desk(payload: CheckInRequest):
    """Triggered directly when scanning the QR URL on a smartphone browser"""
    desk_id = payload.desk_id
    if desk_id not in DB_MOCK:
        raise HTTPException(status_code=404, detail="Invalid desk marker target.")
        
    if DB_MOCK[desk_id]["status"] == "OCCUPIED" and DB_MOCK[desk_id]["user"] != payload.user_email:
        raise HTTPException(status_code=400, detail="This desk is currently occupied.")

    # Successful Check-In / Re-verify State
    DB_MOCK[desk_id] = {
        "status": "OCCUPIED",
        "user": payload.user_email,
        "expires_at": None,
        "last_check_in": time.time() # Resets the 2-hour inactivity anchor
    }
    return {"message": f"Successfully secured Desk {desk_id}", "state": DB_MOCK[desk_id]}

@app.post("/api/desk/away")
def set_desk_away(payload: ActionRequest):
    """Triggered when student clicks the 'Away' utility key on their phone browser"""
    desk_id = payload.desk_id
    if desk_id not in DB_MOCK:
        raise HTTPException(status_code=404, detail="Invalid desk marker target.")
        
    if DB_MOCK[desk_id]["status"] != "OCCUPIED":
        raise HTTPException(status_code=400, detail="Desk must be occupied to declare away status.")
    
    DB_MOCK[desk_id]["status"] = "AWAY"
    # Set expiration timestamp exactly 20 minutes into the future
    DB_MOCK[desk_id]["expires_at"] = time.time() + 1200 
    return {"message": f"Desk {desk_id} placed on a 20-minute hold.", "expires_at": DB_MOCK[desk_id]["expires_at"]}

@app.post("/api/admin/reset-desk")
def admin_reset_desk(payload: ActionRequest):
    """Privileged Override: Librarian clears physical hoarding items and releases node"""
    desk_id = payload.desk_id
    if desk_id not in DB_MOCK:
        raise HTTPException(status_code=404, detail="Invalid desk marker target.")
        
    print(f"[ADMIN ACTION] Librarian cleared and forced override reset on {desk_id}")
    DB_MOCK[desk_id] = {"status": "FREE", "user": None, "expires_at": None, "last_check_in": None}
    return {"message": f"Administrative reset completed for desk {desk_id}."} 