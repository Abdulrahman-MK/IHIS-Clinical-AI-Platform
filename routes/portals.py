# routes/portals.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services.auth_helpers import roles_required

# Directly import the exact models we built in Phase 2
from models.patient import Patient
from models.dental import DentalRecord

# Initialize the modular portal blueprint
portals_bp = Blueprint('portals', __name__, url_prefix='/portal')

# --- PATIENT DASHBOARD ---
@portals_bp.route('/patient')
@login_required
@roles_required('Patient')
def patient_dashboard():
    # Fetch profile information mapped to this specific user account
    patient_profile = Patient.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    
    # Initialize lists so the template tables don't crash if no records exist
    clinical_records = []
    appointments = []
    invoices = []
    
    if patient_profile:
        # Fetch dental/clinical records linked to this patient ID
        clinical_records = DentalRecord.query.filter_by(patient_id=patient_profile.id, is_deleted=False).all()
        
        # Note: If you add Appointment or Invoice models later, you can query them here:
        # appointments = Appointment.query.filter_by(patient_id=patient_profile.id).all()
        # invoices = Invoice.query.filter_by(patient_id=patient_profile.id).all()

    return render_template(
        'portals/patient.html', 
        profile=patient_profile,
        clinical_records=clinical_records,
        appointments=appointments,
        invoices=invoices
    )

# --- CLINICAL MEDICAL DASHBOARD ---
@portals_bp.route('/doctor')
@login_required
@roles_required('Doctor')
def doctor_dashboard():
    # Doctors see active patient clinical lists
    active_patients = Patient.query.filter_by(is_deleted=False).all()
    return render_template('portals/doctor.html', patients=active_patients)

# --- DENTAL SCIENCES DASHBOARD ---
# --- DENTAL SCIENCES DASHBOARD ---
@portals_bp.route('/dental')
@login_required
@roles_required('Dentist')
def dental_dashboard():
    # Fetch all active dental records, and you can also join or fetch patient details if needed
    dental_cases = DentalRecord.query.filter_by(is_deleted=False).all()
    return render_template('portals/dental.html', cases=dental_cases)

# --- REHABILITATION DASHBOARD ---
@portals_bp.route('/rehab')
@login_required
@roles_required('Rehab Therapist')
def rehab_dashboard():
    # Rehabilitation portal home
    return render_template('portals/rehab.html')