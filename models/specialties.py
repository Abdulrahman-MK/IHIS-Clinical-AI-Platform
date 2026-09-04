# models/specialties.py
from datetime import datetime
from extensions import db

class Doctor(db.Model):
    __tablename__ = 'doctors'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialty_name = db.Column(db.String(100), nullable=False)

class Specialty(db.Model):
    __tablename__ = 'specialties'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class RehabSession(db.Model):
    __tablename__ = 'rehab_sessions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    range_of_motion = db.Column(db.String(100))
    muscle_strength = db.Column(db.String(50))
    functional_goals = db.Column(db.Text)
    therapist_notes = db.Column(db.Text)
    session_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)