# SkillBridge Attendance Management System

A robust, multi-tenant attendance tracking API built with FastAPI and PostgreSQL (Neon). Designed for institutional oversight with secure, role-based access control.

## 1. Live Deployment
Railway Deployment Link: https://endearing-presence-production.up.railway.app/docs

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


## NOTE: JWT Payload Token Structure

Standard Login Token

   ```code snippet
   
      {
     "sub": "user_id_123",        // Unique user identifier
     "email": "susanna@test.com", // For display and identification
     "role": "student",           // role: student | trainer | monitoring_officer
     "exp": 1714567890,           // Expiration (e.g., 24 hours)
     "iat": 1714532100            // Issued at timestamp
   }
```

Scoped Monitoring Token

   ```code snippet
   {
     "sub": "user_id_123",
     "role": "monitoring_officer",
     "scope": "monitoring_read_only", // CRITICAL: The "Extra Key"
     "exp": 1714535700,               // Short lifespan (e.g., 1 hour)
     "iat": 1714532100
   }
   ```

To ensure a better security enforced for the scoped monitoring token, I would implement rate limiting. If a user provides the wrong secret key 5 times in a row, their IP address is "jailed" (blocked) for 30 minutes.

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

## 5. Schema Decisions

a) The batch_trainers and batch_students were designed with a many-to-many relationship. This is because a student can enroll themselves in multiple batches and a batch can have multiple trainers.

b) To invite students to a batch, a token system was created, where the trainers creating a new batch give out a token. By generating a signed, time-limited invite_token, only students with the physical or digital "key" provided by a Trainer can link themselves to a batch.

c) The User model stores a hashed_password rather than plain text. For this, the passlib with the bcrypt backend was utilized to ensure industry-standard salted hashing, satisfying the requirement for secure credential storage.

d) The Monitoring Officer has more than just a standard role based access control. Because this rolecan see sensitive attendance data across all institutions, a single login is a high risk. The scoped token is usually configured to expire much faster (within one hour). This Master Key is an environment variable and is not stored in the database. If the database is ever leaked, they still would not find the Master Key because it lives in the server's memory, not the disk.

## 5. Done/Partially Done/Skipped

Done:
1. Role-Based Access Control (RBAC)
2. Authentication
3. Many-to-many enrolements
4. Attendance Lifecycle
5. Swagger docs for UI

Partially Done:
1. Session Conflict Logic: At this point, a trainer can create overlapping session for the same batch which needs to be corrected using a collision check.
2. Testcase fail: The test for marking attendance failed with a 403 Forbidden error. I built the system so that a student must be officially enrolled in a batch before they can mark attendance. Because the test script tried to skip the enrollment process and jump straight to marking attendance, my code correctly blocked it to protect the data integrity. 

Skipped:
-> The session invite link created is not shared with the student through an email for now. 

## 6. Enhancement with more time:
1. Ensure the student receive the session links created by trainers so they can opt to join a session.
2. To enhance features that the monitoring officer has, an analytics layer can be included that gives alerts to find any batch where attendance has dropped below 75% over the last 5 sessions. It moves from tracking to alerting based functionality.
3. Since students are the ones marking their own attendance, integrity checks need to be enforced that allow them to mark attendance only within the stipulated time.


