from datetime import datetime
from extensions import db

class DentalRecord(db.Model):
    __tablename__ = 'dental_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dentist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dental_history = db.Column(db.Text)
    dental_allergies = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

class DentalChart(db.Model):
    __tablename__ = 'dental_charts'
    
    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    
    # Numbering Systems Tracking support
    tooth_number = db.Column(db.Integer, nullable=False, index=True) # Unified database mapping integers
    numbering_system = db.Column(db.String(20), default='FDI') # FDI, Universal, or Palmer
    
    # Surface/Condition Diagnostics
    condition = db.Column(db.String(50), nullable=False) # e.g., 'Caries', 'Missing', 'Crown', 'Filling'
    surfaces = db.Column(db.String(20)) # e.g., 'MODFL' (Mesial, Occlusal, Distal, Facial, Lingual)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DentalProcedure(db.Model):
    __tablename__ = 'dental_procedures'
    
    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    tooth_number = db.Column(db.Integer)
    
    procedure_code = db.Column(db.String(20), nullable=False) # ADA or local clinical billing code
    description = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text)
    
    status = db.Column(db.String(30), default='Planned') # Planned, In-Progress, Completed
    completed_at = db.Column(db.DateTime, nullable=True)