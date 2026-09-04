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
    return render_template('portals/patient.html', profile=patient_profile)

# --- CLINICAL MEDICAL DASHBOARD ---
@portals_bp.route('/doctor')
@login_required
@roles_required('Doctor')
def doctor_dashboard():
    # Doctors see active patient clinical lists
    active_patients = Patient.query.filter_by(is_deleted=False).all()
    return render_template('portals/doctor.html', patients=active_patients)

# --- DENTAL SCIENCES DASHBOARD ---
@portals_bp.route('/dental')
@login_required
@roles_required('Dentist')
def dental_dashboard():
    # Dental specific worklist view using our exact model
    dental_cases = DentalRecord.query.filter_by(is_deleted=False).all()
    return render_template('portals/dental.html', cases=dental_cases)

# --- REHABILITATION DASHBOARD ---
@portals_bp.route('/rehab')
@login_required
@roles_required('Rehab Therapist')
def rehab_dashboard():
    # Rehabilitation portal home
    return render_template('portals/rehab.html')