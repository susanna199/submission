import pytest
from src import models

# --- 1. Successful Student Signup and Login (Hits Real DB) ---
def test_signup_and_login_success(client):
    # Signup
    signup_data = {
        "name": "Test Student",
        "email": "teststudent@christ.edu",
        "password": "securepassword123",
        "role": "student"
    }
    signup_res = client.post("/auth/signup", json=signup_data)
    assert signup_res.status_code == 201 
    
    # Login
    login_data = {"username": "teststudent@christ.edu", "password": "securepassword123"}
    login_res = client.post("/auth/login", data=login_data) # data= for OAuth2 form
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

# --- 2. Trainer Creating a Session ----
def test_trainer_create_session(client, db):
    # We create the institution directly in the test database
    new_inst = models.Institution(name="Christ University")
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)
    inst_id = new_inst.id

    # 2. Signup & Login as a Trainer
    client.post("/auth/signup", json={
        "name": "Trainer Joe", "email": "joe@c.in", "password": "pass", "role": "trainer"
    })
    login = client.post("/auth/login", data={"username": "joe@c.in", "password": "pass"})
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create a Batch using the ACTUAL Batch endpoint
    batch_res = client.post("/batches", json={
        "name": "DS 2026", 
        "institution_id": inst_id
    }, headers=headers)
    batch_id = batch_res.json()["id"]

    # 4. Create the Session
    session_data = {
        "batch_id": batch_id, 
        "title": "Lab 1", 
        "date": "2026-05-01", "start_time": "10:00:00", "end_time": "11:00:00"
    }
    response = client.post("/sessions", json=session_data, headers=headers)
    assert response.status_code == 200


# --- 3. Student Marking Attendance ---
def test_student_mark_attendance_success(client, db):
    # 1. SETUP: Create Institution, Batch, and Session via DB Fixture
    new_inst = models.Institution(name="Test Uni")
    db.add(new_inst)
    db.commit()

    new_batch = models.Batch(name="DS Batch", institution_id=new_inst.id)
    db.add(new_batch)
    db.commit()

    new_session = models.Session(
        batch_id=new_batch.id, 
        title="Logic Lab", 
        date="2026-05-01", 
        start_time="10:00:00", 
        end_time="11:00:00"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session) # This gives us the real ID (likely 1)

    # 2. SIGNUP & ENROLL STUDENT
    client.post("/auth/signup", json={
        "name": "Susanna", "email": "s@test.com", "password": "pass", "role": "student"
    })
    
    # Manually link student to batch in junction table so we pass the 403 check
    # (Assuming student ID is 1 as they are the first user in test DB)
    stmt = models.batch_students.insert().values(student_id=1, batch_id=new_batch.id)
    db.execute(stmt)
    db.commit()

    # 3. LOGIN & MARK ATTENDANCE
    login_res = client.post("/auth/login", data={"username": "s@test.com", "password": "pass"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # USE THE DYNAMIC ID: Use new_session.id instead of hardcoded '2'
    response = client.post(f"/attendance/mark?session_id={new_session.id}", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Attendance marked successfully"

# --- 4. 405 Method Not Allowed ---
def test_monitoring_attendance_wrong_method(client):
    # Trying to POST to a GET-only endpoint
    response = client.post("/monitoring/attendance", json={})
    assert response.status_code == 405
    assert response.json()["detail"] == "Method Not Allowed"

# --- 5. Protected Endpoint No Token (401) ---
def test_protected_endpoint_no_token(client):
    # Trying to access batch summary without login
    response = client.get("/batches/1/summary")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"