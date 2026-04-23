import uuid
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import models, schemas, auth, database
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm # Add this import
from sqlalchemy import func

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Hardcoded API key for Task 2 requirement
MONITORING_SECRET_KEY = "CHRIS_DS_2026_SECURE"

app = FastAPI(title="SkillBridge API")

# Dependency to get DB
get_db = database.get_db

@app.post("/auth/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email exists
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 2. Hash the password
    # hashed_password = auth.get_password_hash(user.password)
    password_to_hash = str(user.password) 
    hashed_pwd = auth.get_password_hash(password_to_hash)
    
    # 3. Create the DB record
    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role,
        institution_id=user.institution_id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# @app.post("/auth/login", response_model=schemas.Token)
# def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
#     # 1. Find the user
#     user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
#     if not user:
#         raise HTTPException(status_code=403, detail="Invalid Credentials")
    
#     # 2. Verify password
#     if not auth.verify_password(user_credentials.password, user.hashed_password):
#         raise HTTPException(status_code=403, detail="Invalid Credentials")
    
#     # 3. Create Token
#     access_token = auth.create_access_token(data={"user_id": user.id, "role": user.role})
#     return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/login", response_model=schemas.Token)
def login(
    # Change UserLogin to OAuth2PasswordRequestForm
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(database.get_db)
):
    # Note: OAuth2PasswordRequestForm uses .username instead of .email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"user_id": user.id, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

# 1. Create a Batch
@app.post("/batches", response_model=schemas.BatchOut)
def create_batch(
    batch: schemas.BatchCreate, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    user_info = auth.get_user_info_from_token(token)
    # PER PDF: Trainer manages batches
    if user_info["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Only Trainers can create and manage batches")
    
    # 1. Check if a batch with this name already exists
    existing_batch = db.query(models.Batch).filter(models.Batch.name == batch.name).first()
    if existing_batch:
        raise HTTPException(status_code=400, detail="A batch with this name already exists")

    new_batch = models.Batch(**batch.dict())
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    return new_batch


# 2. Generate Invite Link
# @app.post("/batches/{batch_id}/invite", response_model=schemas.InviteOut)
# def generate_invite(batch_id: int, db: Session = Depends(database.get_db)):
#     # Generate a unique token
#     token = str(uuid.uuid4())
#     expiry = datetime.utcnow() + timedelta(days=7) # Links valid for 7 days
    
#     new_invite = models.BatchInvite(
#         batch_id=batch_id,
#         token=token,
#         expires_at=expiry
#     )
#     db.add(new_invite)
#     db.commit()
#     db.refresh(new_invite)
#     return {"invite_link": f"http://localhost:8000/batches/join?token={token}", "expires_at": expiry}
# --- Trainer: Generate Invite Link ---

# @app.post("/batches/{batch_id}/invite")
# def generate_invite(
#     batch_id: int, 
#     db: Session = Depends(database.get_db),
#     token: str = Depends(oauth2_scheme)
# ):
#     user_info = auth.get_user_info_from_token(token)
#     if user_info["role"] != "trainer":
#         raise HTTPException(status_code=403, detail="Only Trainers can generate invite links")
    
#     # Generate UUID and save to batch_invites table...
#     return {"invite_token": str(uuid.uuid4())}

@app.post("/batches/{batch_id}/invite")
def generate_invite(
    batch_id: int, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Security Check: Only Trainers
    user_info = auth.get_user_info_from_token(token)
    if user_info["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Only Trainers can generate invites")

    # 2. Verify the batch exists
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # 3. Create the Invite Token (UUID)
    invite_token = str(uuid.uuid4())
    expiry = datetime.utcnow() + timedelta(days=7) # Link valid for 1 week

    new_invite = models.BatchInvite(
        batch_id=batch_id,
        token=invite_token,
        expires_at=expiry
    )
    
    db.add(new_invite)
    db.commit()
    
    return {
        "invite_link": f"http://localhost:8000/batches/join?token={invite_token}",
        "expires_at": expiry
    }


@app.post("/batches/join")
def join_batch(
    token: str, 
    db: Session = Depends(database.get_db), 
    ad_token: str = Depends(oauth2_scheme)
):
    # 1. Decode the student's ID and Role from their login token
    # Ensure this function in auth.py returns the actual ID
    user_info = auth.get_user_info_from_token(ad_token)
    student_id = user_info.get("user_id")
    role = user_info.get("role")

    if not student_id or role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only students can join batches via invite links"
        )

    # 2. Validate the Invite Token (the UUID generated by the trainer)
    invite = db.query(models.BatchInvite).filter(models.BatchInvite.token == token).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invite link")

    # Check if the link has expired
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This invite link has expired")
    
    # 3. Check if the student is already enrolled in this specific batch
    # This prevents duplicate rows in your many-to-many table
    already_joined = db.query(models.batch_students).filter(
        models.batch_students.c.student_id == student_id,
        models.batch_students.c.batch_id == invite.batch_id
    ).first()

    if already_joined:
        return {"message": "You are already a member of this batch", "batch_id": invite.batch_id}

    # 4. PERFORM THE ACTUAL INSERT into the junction table
    # Since batch_students is a Table object, we use the .insert() syntax
    try:
        stmt = models.batch_students.insert().values(
            student_id=student_id, 
            batch_id=invite.batch_id
        )
        db.execute(stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to join batch. Please try again.")
    
    return {
        "status": "success",
        "message": f"Successfully joined batch {invite.batch_id}",
        "student_id": student_id
    }

@app.post("/sessions", response_model=schemas.SessionOut)
def create_session(
    session_payload: schemas.SessionCreate, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Get the Trainer's info from the token
    user_info = auth.get_user_info_from_token(token)
    if user_info["role"] != "trainer":
        raise HTTPException(status_code=403, detail="Only trainers can create sessions")

    # 2. Create the session object including the missing pieces
    new_session = models.Session(
        batch_id=session_payload.batch_id,
        date=session_payload.date,
        start_time=session_payload.start_time,
        end_time=session_payload.end_time,
        title=session_payload.title,    # Include the title from the payload
        trainer_id=user_info["user_id"] # Automatically link the logged-in trainer
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@app.post("/attendance/mark")
def mark_attendance(
    session_id: int, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    user_info = auth.get_user_info_from_token(token)
    student_id = user_info["user_id"]
    
    if user_info["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can mark attendance")

    # 1. Find the session and its batch
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Check if the student is enrolled in this session's batch
    # We check the 'batch_students' junction table
    enrollment = db.query(models.batch_students).filter(
        models.batch_students.c.student_id == student_id,
        models.batch_students.c.batch_id == session.batch_id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch")

    # 3. Check for existing attendance (Prevent double marking)
    existing = db.query(models.Attendance).filter(
        models.Attendance.session_id == session_id,
        models.Attendance.student_id == student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked")

    # 4. Mark it!
    new_attendance = models.Attendance(
        session_id=session_id,
        student_id=student_id,
        status="present" # Default status
    )
    db.add(new_attendance)
    db.commit()
    return {"message": "Attendance marked successfully"}


@app.get("/sessions/{session_id}/attendance")
def get_session_attendance(
    session_id: int, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    user_info = auth.get_user_info_from_token(token)
    if user_info["role"] == "student":
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 1. Execute the query
    results = db.query(
        models.User.name, 
        models.User.email, 
        models.Attendance.marked_at
    ).join(models.Attendance, models.User.id == models.Attendance.student_id)\
     .filter(models.Attendance.session_id == session_id).all()

    # 2. Convert the list of tuples into a list of dictionaries
    # This solves the 'dictionary update sequence' error
    formatted_attendance = [
        {"name": row.name, "email": row.email, "marked_at": row.marked_at} 
        for row in results
    ]

    return formatted_attendance
from sqlalchemy import func

@app.get("/batches/{id}/summary")
def get_batch_summary(
    id: int, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Identity & Role Check
    user_info = auth.get_user_info_from_token(token)
    if user_info["role"] not in ["institution", "programme_manager", "monitoring_officer"]:
        raise HTTPException(status_code=403, detail="Unauthorized to view batch summaries")

    # 2. Check if Batch exists
    batch = db.query(models.Batch).filter(models.Batch.id == id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # 3. Data Aggregation
    # Total students enrolled in this batch
    total_students = db.query(models.batch_students).filter(
        models.batch_students.c.batch_id == id
    ).count()

    # Total sessions conducted for this batch
    total_sessions = db.query(models.Session).filter(
        models.Session.batch_id == id
    ).count()

    # Total attendance marks (presents) across all sessions in this batch
    total_attendance_marks = db.query(models.Attendance)\
        .join(models.Session, models.Attendance.session_id == models.Session.id)\
        .filter(models.Session.batch_id == id).count()

    # 4. Math: Calculate the Attendance Percentage
    # Formula: (Actual Marks / (Students * Sessions)) * 100
    max_possible_attendance = total_students * total_sessions
    
    attendance_percentage = 0
    if max_possible_attendance > 0:
        attendance_percentage = (total_attendance_marks / max_possible_attendance) * 100

    return {
        "batch_name": batch.name,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "total_attendance_marks": total_attendance_marks,
        "overall_attendance_percentage": f"{round(attendance_percentage, 2)}%"
    }


@app.get("/institutions/{id}/summary")
def get_institution_summary(
    id: int, 
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Identity & Role Check
    user_info = auth.get_user_info_from_token(token)
    # Per PDF: Programme Manager and Monitoring Officer oversee multiple institutions
    if user_info["role"].lower() not in ["programme_manager", "monitoring_officer", "institution", "trainer"]:
        raise HTTPException(status_code=403, detail="Unauthorized for institutional reporting")

    # 2. Basic Metadata
    inst = db.query(models.Institution).filter(models.Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # 3. Aggregation Logic
    # Count all batches under this institution
    total_batches = db.query(models.Batch).filter(models.Batch.institution_id == id).count()

    # Count total unique students enrolled in all batches of this institution
    total_students = db.query(models.batch_students)\
        .join(models.Batch, models.batch_students.c.batch_id == models.Batch.id)\
        .filter(models.Batch.institution_id == id).count()

    # Total sessions conducted across all batches of this institution
    total_sessions = db.query(models.Session)\
        .join(models.Batch, models.Session.batch_id == models.Batch.id)\
        .filter(models.Batch.institution_id == id).count()

    # Total attendance marks recorded for all sessions in this institution
    total_attendance = db.query(models.Attendance)\
        .join(models.Session, models.Attendance.session_id == models.Session.id)\
        .join(models.Batch, models.Session.batch_id == models.Batch.id)\
        .filter(models.Batch.institution_id == id).count()

    # 4. Calculation: Overall Institutional Attendance Rate
    max_possible = total_students * total_sessions
    overall_rate = (total_attendance / max_possible * 100) if max_possible > 0 else 0

    return {
        "institution_name": inst.name,
        "metrics": {
            "total_batches": total_batches,
            "total_students": total_students,
            "total_sessions_conducted": total_sessions,
            "total_attendance_records": total_attendance,
            "institutional_attendance_rate": f"{round(overall_rate, 2)}%"
        }
    }


@app.get("/programme/summary")
def get_programme_wide_summary(
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Identity & Role Check
    user_info = auth.get_user_info_from_token(token)
    
    # PER PDF: Monitoring Officer (read-only) and PM oversee the entire program
    if user_info["role"] not in ["programme_manager", "monitoring_officer"]:
        raise HTTPException(
            status_code=403, 
            detail="Unauthorized. Only Programme-level officers can view global metrics."
        )

    # 2. Global Aggregation
    total_institutions = db.query(models.Institution).count()
    total_batches = db.query(models.Batch).count()
    total_trainers = db.query(models.User).filter(models.User.role == "trainer").count()
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_sessions = db.query(models.Session).count()
    
    # Total attendance marks across the entire SkillBridge system
    total_attendance = db.query(models.Attendance).count()

    # 3. Global Efficiency Calculation
    # Max possible = Total Enrolled Students * Total Sessions Held
    # Note: This is a simplified global metric for prototype reporting
    max_possible_attendance = total_students * total_sessions
    global_attendance_rate = (total_attendance / max_possible_attendance * 100) if max_possible_attendance > 0 else 0

    return {
        "programme_name": "SkillBridge State Skilling Initiative",
        "global_metrics": {
            "institutions_participating": total_institutions,
            "active_batches": total_batches,
            "total_trainers": total_trainers,
            "total_students": total_students,
            "total_sessions_conducted": total_sessions,
            "total_attendance_records": total_attendance
        },
        "performance_indicators": {
            "global_attendance_rate": f"{round(global_attendance_rate, 2)}%",
            "average_students_per_batch": round(total_students / total_batches, 1) if total_batches > 0 else 0
        }
    }


# @app.get("/monitoring/attendance")
# def get_global_attendance_logs(
#     db: Session = Depends(database.get_db),
#     token: str = Depends(oauth2_scheme)
# ):
#     # 1. Identity & Role Check
#     user_info = auth.get_user_info_from_token(token)
    
#     # Strictly for Programme-level oversight
#     if user_info["role"] not in ["programme_manager", "monitoring_officer"]:
#         raise HTTPException(
#             status_code=403, 
#             detail="Access denied. Monitoring logs are restricted to program officers."
#         )

#     # 2. Complex Join to gather full context
#     # We join Attendance -> Session -> Batch -> Institution AND Attendance -> User
#     logs = db.query(
#         models.Attendance.id.label("attendance_id"),
#         models.User.name.label("student_name"),
#         models.Session.title.label("session_title"),
#         models.Batch.name.label("batch_name"),
#         models.Institution.name.label("institution_name"),
#         models.Attendance.marked_at
#     ).join(models.User, models.Attendance.student_id == models.User.id)\
#      .join(models.Session, models.Attendance.session_id == models.Session.id)\
#      .join(models.Batch, models.Session.batch_id == models.Batch.id)\
#      .join(models.Institution, models.Batch.institution_id == models.Institution.id)\
#      .order_by(models.Attendance.marked_at.desc())\
#      .all()

#     # 3. Format as dictionaries for FastAPI
#     return [
#         {
#             "id": log.attendance_id,
#             "student": log.student_name,
#             "session": log.session_title,
#             "batch": log.batch_name,
#             "institution": log.institution_name,
#             "timestamp": log.marked_at
#         } for log in logs
#     ]


@app.get("/monitoring/attendance")
def get_global_attendance_logs(
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    # 1. Scoped Token Check (Requirement: validate scoped token, not standard login)
    # We use auth.decode_token to see the full payload including 'scope'
    payload = auth.decode_token(token)
    
    if not payload:
         raise HTTPException(status_code=401, detail="Invalid or expired token")

    # STRICT VALIDATION: Must have the specific scope and the correct role
    if payload.get("scope") != "monitoring_read_only" or payload.get("role") != "monitoring_officer":
        raise HTTPException(
            status_code=401, 
            detail="Valid Monitoring Scoped Token required. Please exchange your API key for a scoped token."
        )

    # 2. Complex Join to gather full context (remains the same)
    logs = db.query(
        models.Attendance.id.label("attendance_id"),
        models.User.name.label("student_name"),
        models.Session.title.label("session_title"),
        models.Batch.name.label("batch_name"),
        models.Institution.name.label("institution_name"),
        models.Attendance.marked_at
    ).join(models.User, models.Attendance.student_id == models.User.id)\
     .join(models.Session, models.Attendance.session_id == models.Session.id)\
     .join(models.Batch, models.Session.batch_id == models.Batch.id)\
     .join(models.Institution, models.Batch.institution_id == models.Institution.id)\
     .order_by(models.Attendance.marked_at.desc())\
     .all()

    # 3. Format as dictionaries
    return [
        {
            "id": log.attendance_id,
            "student": log.student_name,
            "session": log.session_title,
            "batch": log.batch_name,
            "institution": log.institution_name,
            "timestamp": log.marked_at
        } for log in logs
    ]

@app.post("/auth/monitoring-token")
def get_monitoring_token(
    payload: dict, # Expecting {"key": "..."}
    db: Session = Depends(database.get_db),
    ad_token: str = Depends(oauth2_scheme)
):
    # 1. Verify standard JWT first
    user_info = auth.get_user_info_from_token(ad_token)
    if user_info["role"] != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Only Monitoring Officers can request this token")

    # 2. Check the hardcoded API key
    if payload.get("key") != MONITORING_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid Monitoring Key")

    # 3. Issue the 1-hour scoped token
    scoped_token = auth.create_monitoring_token({"user_id": user_info["user_id"], "role": "monitoring_officer"})
    return {"access_token": scoped_token, "token_type": "bearer"}