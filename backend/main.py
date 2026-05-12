from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio

from . import models, database, auth, monitor

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Emotion Monitoring System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Pydantic Schemas
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    session_id: Optional[int] = None

class EmployeeStatus(BaseModel):
    id: int
    name: str
    status: str
    emotion: Optional[str] = "Neutral"
    fatigue: Optional[str] = "Neutral"
    pulse_rate: Optional[int] = 0
    work_duration: Optional[int] = 0

# Dependency to get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    payload = auth.decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        name=user.name, 
        email=user.email, 
        password=hashed_password, 
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role})
    
    from datetime import datetime
    now = datetime.utcnow()
    
    # Close any existing open sessions for this user to prevent double counting
    open_sessions = db.query(models.UserSession).filter(
        models.UserSession.user_id == user.id,
        models.UserSession.logout_time == None
    ).all()
    
    for s in open_sessions:
        s.logout_time = now
        duration = s.logout_time - s.login_time
        s.session_duration = int(duration.total_seconds())
    
    # Create new user session
    new_session = models.UserSession(user_id=user.id, login_time=now)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "name": user.name, "session_id": new_session.id}

@app.post("/logout")
def logout(session_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    from datetime import datetime
    session = db.query(models.UserSession).filter(
        models.UserSession.id == session_id,
        models.UserSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.logout_time = datetime.utcnow()
    # Calculate duration
    duration = session.logout_time - session.login_time
    session.session_duration = int(duration.total_seconds())
    db.commit()
    
    return {"message": "Logged out successfully"}

@app.get("/usage-stats")
def get_usage_stats(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "Manager":
        raise HTTPException(status_code=403, detail="Only managers can view this")
        
    from datetime import datetime, time, timedelta
    
    # Get today's bounds (midnight to next midnight)
    today = datetime.utcnow().date()
    start_of_day = datetime.combine(today, time.min)
    
    employees = db.query(models.User).filter(models.User.role == "Employee").all()
    stats = []
    
    for emp in employees:
        # Get today's sessions
        sessions = db.query(models.UserSession).filter(
            models.UserSession.user_id == emp.id,
            models.UserSession.login_time >= start_of_day
        ).all()
        
        total_seconds = 0
        last_login = None
        
        for sess in sessions:
            if last_login is None or sess.login_time > last_login:
                last_login = sess.login_time
                
            if sess.session_duration > 0:
                total_seconds += sess.session_duration
            elif sess.logout_time is None:
                # Still active session, calculate duration up to now
                current_duration = datetime.utcnow() - sess.login_time
                total_seconds += int(current_duration.total_seconds())
                
        total_hours = total_seconds / 3600.0
        exceeds_limit = total_hours > 8.0
        
        stats.append({
            "employee_id": emp.id,
            "name": emp.name,
            "last_login": last_login.isoformat() if last_login else None,
            "total_hours_today": round(total_hours, 2),
            "total_seconds_today": total_seconds,
            "exceeds_limit": exceeds_limit
        })
        
    return stats

@app.post("/start-monitoring")
def start_monitoring(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    monitor.monitor_service.start()
    
    # Update latest log or create active session
    log = db.query(models.EmotionLog).filter(
        models.EmotionLog.employee_id == current_user.id,
        models.EmotionLog.status == "Active"
    ).first()
    
    if not log:
        log = models.EmotionLog(employee_id=current_user.id, status="Active")
        db.add(log)
        db.commit()
        
    return {"message": "Monitoring started"}

@app.post("/stop-monitoring")
def stop_monitoring(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    monitor.monitor_service.stop()
    
    # Update active log to Inactive
    logs = db.query(models.EmotionLog).filter(
        models.EmotionLog.employee_id == current_user.id,
        models.EmotionLog.status == "Active"
    ).all()
    
    for log in logs:
        log.status = "Inactive"
    db.commit()
    
    return {"message": "Monitoring stopped"}

@app.post("/log-emotion")
def log_emotion(duration: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if not monitor.monitor_service.is_monitoring:
        return {"message": "Not monitoring"}
        
    data = monitor.monitor_service.get_current_data()
    
    log = db.query(models.EmotionLog).filter(
        models.EmotionLog.employee_id == current_user.id,
        models.EmotionLog.status == "Active"
    ).order_by(models.EmotionLog.id.desc()).first()
    
    if log:
        log.emotion = data["emotion"]
        log.fatigue = data.get("dl_fatigue", "Neutral")
        log.pulse_rate = data["pulse_rate"]
        log.work_duration = duration
        db.commit()
        
    return {"status": "success", "data": data}

@app.get("/employees", response_model=List[EmployeeStatus])
def get_employees(current_user: models.User = Depends(get_current_user), db: Session = Depends(database.get_db)):
    if current_user.role != "Manager":
        raise HTTPException(status_code=403, detail="Only managers can view this")
        
    employees = db.query(models.User).filter(models.User.role == "Employee").all()
    result = []
    for emp in employees:
        log = db.query(models.EmotionLog).filter(
            models.EmotionLog.employee_id == emp.id
        ).order_by(models.EmotionLog.id.desc()).first()
        
        result.append({
            "id": emp.id,
            "name": emp.name,
            "status": log.status if log else "Inactive",
            "emotion": log.emotion if log else "Neutral",
            "fatigue": log.fatigue if log else "Neutral",
            "pulse_rate": log.pulse_rate if log else 0,
            "work_duration": log.work_duration if log else 0
        })
    return result

async def video_stream():
    while True:
        frame = monitor.monitor_service.current_frame
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        await asyncio.sleep(0.05)

@app.get("/video-feed")
def video_feed():
    return StreamingResponse(video_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# WebSocket for Manager Dashboard Real-time updates
active_connections: List[WebSocket] = []

@app.websocket("/ws/manager")
async def websocket_manager(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            db = database.SessionLocal()
            try:
                db.commit()
                from datetime import datetime, time
                today = datetime.utcnow().date()
                start_of_day = datetime.combine(today, time.min)
                
                # Broadcast latest state every 3 seconds
                employees = db.query(models.User).filter(models.User.role == "Employee").all()
                data = []
                for emp in employees:
                    log = db.query(models.EmotionLog).filter(
                        models.EmotionLog.employee_id == emp.id
                    ).order_by(models.EmotionLog.id.desc()).first()
                    
                    # Calculate usage stats
                    sessions = db.query(models.UserSession).filter(
                        models.UserSession.user_id == emp.id,
                        models.UserSession.login_time >= start_of_day
                    ).all()
                    
                    total_seconds = 0
                    last_login = None
                    
                    for sess in sessions:
                        if last_login is None or sess.login_time > last_login:
                            last_login = sess.login_time
                            
                        if sess.session_duration > 0:
                            total_seconds += sess.session_duration
                        elif sess.logout_time is None:
                            current_duration = datetime.utcnow() - sess.login_time
                            total_seconds += int(current_duration.total_seconds())
                            
                    total_hours = total_seconds / 3600.0
                    exceeds_limit = total_hours > 8.0
                    
                    data.append({
                        "id": emp.id,
                        "name": emp.name,
                        "status": log.status if log else "Inactive",
                        "emotion": log.emotion if log else "Neutral",
                        "fatigue": log.fatigue if log else "Neutral",
                        "pulse_rate": log.pulse_rate if log else 0,
                        "work_duration": log.work_duration if log else 0,
                        "last_login": last_login.isoformat() + "Z" if last_login else None,
                        "total_seconds_today": total_seconds,
                        "exceeds_limit": exceeds_limit
                    })
                await websocket.send_text(json.dumps(data))
            finally:
                db.close()
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
