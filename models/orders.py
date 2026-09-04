from datetime import datetime
from extensions import db

class LabOrder(db.Model):
    __tablename__ = 'lab_orders'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    test_name = db.Column(db.String(100), nullable=False) # e.g., 'CBC', 'Lipid Panel', 'Metabolic Panel'
    status = db.Column(db.String(30), default='Pending')  # Pending, Processing, Completed
    results = db.Column(db.Text, nullable=True)           # Lab findings entered later
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    doctor = db.relationship('User', foreign_keys=[doctor_id])

class RadiologyOrder(db.Model):
    __tablename__ = 'radiology_orders'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    imaging_type = db.Column(db.String(100), nullable=False) # e.g., 'X-Ray Chest', 'X-Ray Wrist / Hand'
    status = db.Column(db.String(30), default='Ordered')     # Ordered, Scheduled, Completed
    findings = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)     # Path to uploaded scan file
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    medication_name = db.Column(db.String(150), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)        # e.g., '500mg'
    frequency = db.Column(db.String(100), nullable=False)    # e.g., 'Twice daily for 7 days'
    status = db.Column(db.String(30), default='Active')       # Active, Fulfilled, Discontinued
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('User', foreign_keys=[doctor_id])