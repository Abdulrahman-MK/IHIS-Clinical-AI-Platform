from datetime import datetime, date
from extensions import db

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), default='Not Specified')  # Male, Female, Other
    blood_type = db.Column(db.String(5))
    phone = db.Column(db.String(30), nullable=True)
    
    # Clinical History Background & Drug Sensitivities
    allergies = db.Column(db.Text)               # General allergies (e.g. latex, dust, peanuts)
    drug_sensitivities = db.Column(db.Text)      # Specific drug sensitivities & adverse reactions
    chronic_diseases = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))
    vital_signs = db.relationship('VitalSigns', backref='patient', lazy=True, order_by='desc(VitalSigns.recorded_at)')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True, order_by='desc(MedicalRecord.created_at)')
    lab_orders = db.relationship('LabOrder', backref='patient', lazy=True, order_by='desc(LabOrder.created_at)')
    radiology_orders = db.relationship('RadiologyOrder', backref='patient', lazy=True, order_by='desc(RadiologyOrder.created_at)')
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, order_by='desc(Prescription.created_at)')

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.date_of_birth:
            return "N/A"
        today = date.today()
        calculated_age = today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return calculated_age


class VitalSigns(db.Model):
    __tablename__ = 'vital_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Nurse/Doctor ID
    
    blood_pressure_sys = db.Column(db.Integer, nullable=False) # mmHg
    blood_pressure_dia = db.Column(db.Integer, nullable=False) # mmHg
    heart_rate = db.Column(db.Integer, nullable=False)         # bpm
    temperature = db.Column(db.Float, nullable=False)          # Celsius
    respiratory_rate = db.Column(db.Integer, nullable=True)    # breaths/min
    spo2 = db.Column(db.Integer, nullable=True)                # % oxygen saturation
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    recorder = db.relationship('User', foreign_keys=[recorded_by])


class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encounter_type = db.Column(db.String(50), default='SOAP Note') # 'SOAP Note', 'Clinical Examination Sheet', etc.
    
    # Clinical History / HPI
    chief_complaint = db.Column(db.Text, nullable=True)
    hpi = db.Column(db.Text, nullable=True) # History of Present Illness
    drug_sensitivities_snapshot = db.Column(db.Text, nullable=True)

    # Vitals Snapshot during encounter
    blood_pressure_sys = db.Column(db.Integer, nullable=True)
    blood_pressure_dia = db.Column(db.Integer, nullable=True)
    heart_rate = db.Column(db.Integer, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    respiratory_rate = db.Column(db.Integer, nullable=True)
    spo2 = db.Column(db.Integer, nullable=True)

    # Systematic Physical Examination
    exam_general = db.Column(db.Text, nullable=True)
    exam_heent = db.Column(db.Text, nullable=True)
    exam_cardiovascular = db.Column(db.Text, nullable=True)
    exam_respiratory = db.Column(db.Text, nullable=True)
    exam_abdomen = db.Column(db.Text, nullable=True)
    exam_musculoskeletal = db.Column(db.Text, nullable=True)
    exam_neurological = db.Column(db.Text, nullable=True)

    # SOAP Clinical note format
    subjective = db.Column(db.Text)
    objective = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)

    # AI Decision Support Captures
    icd10_codes = db.Column(db.String(255), nullable=True)
    ai_risk_score = db.Column(db.Float, nullable=True)
    ai_triage = db.Column(db.String(100), nullable=True)
    ai_directives = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    doctor = db.relationship('User', foreign_keys=[doctor_id])