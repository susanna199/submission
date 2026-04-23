# SkillBridge Attendance Management System

A robust, multi-tenant attendance tracking API built with FastAPI and PostgreSQL (Neon). Designed for institutional oversight with secure, role-based access control.

## 1. Live Deployment


## 2. Local Setup Instructions

1. **Clone & Enter Folder:**
   ```bash
   git clone <your-repo-url>
   cd skillbridge-backend

2. Environment Setup:

    ```bash

    python -m venv venv
    .\venv\Scripts\activate  # Windows: .\venv\Scripts\activate
    pip install -r requirements.txt
    

3. Configuration: Create a .env file in the root:

    ```code snippet

    DATABASE_URL=your_postgresql_connection_string
    SECRET_KEY=your_jwt_secret
    MONITORING_SECRET_KEY=CHRIS_DS_2026_SECURE

4. Run

    ```bash

    uvicorn src.main:app --reload


## 3. Test Accounts (Templates)
*Note: Since the database starts empty, the signup commands must be used below to register these accounts first.*

| Role | Email | Password |
| :--- | :--- | :--- |
| **Student** | `student@test.com` | `password@123` |
| **Trainer** | `trainer@test.com` | `password123` |
| **Institution** | `admin@christ.edu` | `password123` |
| **Monitoring Officer** | `auditor@test.com` | `password123` |

## 4. Sample curl Commands
Windows Users: Please use the PowerShell versions to avoid JSON decoding errors.

**Part A: Signup and Login**

1. **Trainer:**

   I. Signup:
   ```bash
      curl.exe -X POST "http://localhost:8000/auth/signup" `
               -H "Content-Type: application/json" `
               -d "{\`"name\`": \`"Trainer Joe\`", \`"email\`": \`"trainer@test.com\`", \`"password\`": \`"password123\`", \`"role\`": \`"trainer\`"}"
   ```

   II. Standard Login (Obtain 24h JWT)
   All Platforms:
   
   ```bash
      curl.exe -X POST "http://localhost:8000/auth/login" -d "username=trainer@test.com&password=password123"
   ```

2. **Student:**

   I. Signup:

   ```bash
      curl.exe -X POST "http://localhost:8000/auth/signup" -H "Content-Type: application/json" -d "{\`"name\`": \`"Susanna\`", \`"email\`": \`"student@test.com\`",    \`"password\`": \`"password123\`", \`"role\`": \`"student\`"}"
   ```

   II. Standard Login (Obtain 24h JWT)

   ```bash
      curl.exe -X POST "http://localhost:8000/auth/login" -d "username=student@test.com&password=password123"
   ```

3. **Monitoring Officer:**

   I. Signup

   ```bash
      curl.exe -X POST "http://localhost:8000/auth/signup" -H "Content-Type: application/json" -d "{\`"name\`": \`"Auditor\`", \`"email\`": \`"auditor@test.com\`", \`"password\`": \`"pass123\`", \`"role\`": \`"monitoring_officer\`"}"
   ```
   
   II. Login as Monitoring Officer

   ```bash
      curl.exe -X POST "http://localhost:8000/auth/login" -d "username=auditor@test.com&password=pass123"
   ```
   III. Obtain Monitoring Scoped Token (Step-Up Authentication)

   ```bash
      curl.exe -X POST "http://localhost:8000/auth/monitoring-token" -H "Authorization: Bearer <PASTE_TOKEN_FROM_STEP_2_HERE>" -H "Content-Type: application/json" -d "{\`"key\`": \`"CHRIS_DS_2026_SECURE\`"}"
   ```

**Part B: Batch & Enrollment Management**

   1. Generating Batch Invite Link

      ```bash
         curl.exe -X POST "http://localhost:8000/batches/4/invite" -H "Authorization: Bearer <JWT>"
      ```
   2. Join Batch

      ```bash
         curl.exe -X POST "http://localhost:8000/batches/join" -H "Authorization: Bearer <STUDENT_JWT>" -H "Content-Type: application/json" -d "{\`"token\`": \`"PASTE_INVITE_TOKEN_HERE\`"}"
      ```

**Part C: Attendance Operations**

   1. Create Session (Trainer only)

      ```bash
         curl.exe -X POST "http://localhost:8000/sessions" -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" -d "{\`"batch_id\`": 4, \`"title\`": \`"Python Lab 1\`", \`"date\`": \`"2026-04-25\`", \`"start_time\`": \`"10:00:00\`", \`"end_time\`": \`"12:00:00\`"}"
      ```

   2. Mark Attendance (Student only)

      ```bash
         curl.exe -X POST "http://localhost:8000/attendance/mark?session_id=1" -H "Authorization: Bearer <STUDENT_JWT>"
      ```

   3. Get Session Attendance List

      ```bash
         curl.exe -X GET "http://localhost:8000/sessions/1/attendance" -H "Authorization: Bearer <JWT>"
      ```

**Part D: Monitoring**

   1. Get Batch Summary (Monitoring Officer\'s JWT)

      ```bash
         curl.exe -X GET "http://localhost:8000/batches/4/summary" -H "Authorization: Bearer <JWT>"
      ```
   


