# models.py
# This file defines the ORM SQLAlchemy models for creating tables in the Neon PostgreSQL database
# Each class represents a table and the fields represent their attributes
# There are 7 tables and 2 join tables to handle many-to-many relationships between batches, trainers and students


from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Time, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# --- MANY-TO-MANY JOIN TABLES ---
# Requirement: multiple trainers can be assigned to the same batch [cite: 37]
batch_trainers = Table(
    'batch_trainers',
    Base.metadata,
    Column('batch_id', Integer, ForeignKey('batches.id'), primary_key=True),
    Column('trainer_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# Requirement: links students to batches [cite: 38]
batch_students = Table(
    'batch_students',
    Base.metadata,
    Column('batch_id', Integer, ForeignKey('batches.id'), primary_key=True),
    Column('student_id', Integer, ForeignKey('users.id'), primary_key=True)
)

# --- ENTITIES ---

class User(Base):
    __tablename__ = "users"
    # Fields: id, name, email, hashed_password, role, institution_id (nullable), created_at 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False) # student/trainer/institution/programme_manager/monitoring_officer
    institution_id = Column(Integer, ForeignKey('institutions.id'), nullable=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Batch(Base):
    __tablename__ = "batches"
    # Fields: id, name, institution_id, created_at 
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey('institutions.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class BatchInvite(Base):
    __tablename__ = "batch_invites"
    # Fields: id, batch_id, token, created_by, expires_at, used [cite: 39]
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    token = Column(String, unique=True, index=True)
    created_by = Column(Integer, ForeignKey('users.id')) # Trainer ID [cite: 42]
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

class Session(Base):
    __tablename__ = "sessions"
    # Fields: id, batch_id, trainer_id, title, date, start_time, end_time, created_at [cite: 40]
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey('batches.id'))
    trainer_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Attendance(Base):
    __tablename__ = "attendance"
    # Fields: id, session_id, student_id, status (present/absent/late), marked_at [cite: 40]
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey('sessions.id'))
    student_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, nullable=False) # present / absent / late
    marked_at = Column(DateTime(timezone=True), server_default=func.now())