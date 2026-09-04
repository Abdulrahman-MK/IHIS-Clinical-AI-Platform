# routes/clinical.py
from flask import Blueprint, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.patient import MedicalRecord
from services.auth_helpers import roles_required
from services.ai_services import ClinicalAIEngine

clinical_bp = Blueprint('clinical', __name__, url_prefix='/clinical')

@clinical_bp.route('/patient/<int:patient_id>/add-soap', methods=['POST'])
@login_required
@roles_required('Doctor')
def add_soap_note(patient_id):
    new_note = MedicalRecord(
        patient_id=patient_id,
        doctor_id=current_user.id,
        subjective=request.form.get('subjective'),
        objective=request.form.get('objective'),
        assessment=request.form.get('assessment'),
        plan=request.form.get('plan')
    )
    db.session.add(new_note)
    db.session.commit()
    flash('SOAP note added successfully.', 'success')
    return redirect(url_for('portals.doctor_dashboard'))


# --- NEW: ASYNCHRONOUS AI COMPUTE ENDPOINT ---
@clinical_bp.route('/ai-analyze', methods=['POST'])
@login_required
@roles_required('Doctor', 'Dentist', 'Rehab Therapist')
def ai_analyze_encounter():
    """
    Asynchronous JSON bridge capturing clinical inputs to feed back predictive analysis packages.
    """
    data = request.get_json() or {}
    
    subjective = data.get('subjective', '')
    objective = data.get('objective', '')
    heart_rate = data.get('heart_rate', 80)
    temperature = data.get('temperature', 37.0)

    # Execute analytics pipeline
    calculated_risk = ClinicalAIEngine.calculate_risk_score(heart_rate, temperature)
    ai_payload = ClinicalAIEngine.generate_insights(subjective, objective, calculated_risk)

    return jsonify(ai_payload)