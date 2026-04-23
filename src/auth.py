# auth.py

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()

# Setup password hashing algorithm (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Constants
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def get_password_hash(password: str):
    """Encodes plain text password into a secure hash."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Compares a plain password with the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    """Generates a signed JWT with role-based expiry."""
    to_encode = data.copy()
    
    # Expiry Logic per Requirement
    role = data.get("role")
    if role == "monitoring_officer":
        expire_time = timedelta(hours=1)
    else:
        expire_time = timedelta(hours=24)
        
    expire = datetime.utcnow() + expire_time
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# This function extracts the user id from the JWT token
def get_user_id_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None
    

def get_user_info_from_token(token: str):
    try:
        # 1. Decode the token using your Secret Key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. Extract the data we put in during login
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        
        # 3. Validation check
        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
            
        return {"user_id": user_id, "role": role}
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In auth.py
# In src/auth.py

def create_monitoring_token(data: dict):
    to_encode = data.copy()
    # Task 2 requirement: 1 hour expiry for scoped token
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({
        "exp": expire, 
        "scope": "monitoring_read_only",
        "iat": datetime.utcnow()
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None