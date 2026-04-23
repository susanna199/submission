# schemas.py


from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, time, date

# Common fields shared across schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str # student / trainer / institution / programme_manager / monitoring_officer

# 1. Data received when someone signs up
class UserCreate(UserBase):
    password: str
    institution_id: Optional[int] = None

# 2. Data we send back to the user (Notice: No password field here!)
class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy model data

# 3. Data for the Login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 4. The actual JWT structure returned on successful login
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

# --- Batch Schemas ---

class BatchBase(BaseModel):
    name: str
    institution_id: int

class BatchCreate(BatchBase):
    pass  # Used when receiving data to create a batch

class BatchOut(BatchBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Invite Schemas ---

class InviteOut(BaseModel):
    invite_link: str
    expires_at: datetime

    class Config:
        from_attributes = True

# --- Session Schemas ---

class SessionBase(BaseModel):
    batch_id: int
    date: date
    start_time: time
    end_time: time

class SessionCreate(BaseModel):
    batch_id: int
    title: str  # Add this to satisfy the NOT NULL constraint
    date: date
    start_time: time
    end_time: time

class SessionOut(SessionBase):
    id: int

    class Config:
        from_attributes = True # This tells Pydantic to read data from the SQLAlchemy model