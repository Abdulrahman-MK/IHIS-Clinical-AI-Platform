import os
import random
import string
from datetime import datetime, date, timedelta
from flask import Blueprint, request, jsonify, redirect, url_for, flash, render_template
from flask_login import login_required, current_user
from extensions import db
from models.user import User, Role
from models.audit_log import AuditLog
from models.patient import Patient, MedicalRecord, VitalSigns
from models.orders import LabOrder, RadiologyOrder, Prescription
from services.auth_helpers import roles_required
from services.ai_services import ClinicalAIEngine

clinical_bp = Blueprint('clinical', __name__, url_prefix='/clinical')


# --- PATIENT ONBOARDING / REGISTRATION ---
@clinical_bp.route('/patient/add', methods=['POST'])
@login_required
@roles_required('Doctor', 'Admin')
def add_patient():
    """Register a new patient into the hospital information system."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    gender = request.form.get('gender', 'Not Specified')
    dob_str = request.form.get('date_of_birth')
    age_input = request.form.get('age')
    blood_type = request.form.get('blood_type', 'Unknown')
    drug_sensitivities = request.form.get('drug_sensitivities', '').strip()
    allergies = request.form.get('allergies', '').strip()
    chronic_diseases = request.form.get('chronic_diseases', '').strip()
    phone = request.form.get('phone', '').strip()

    if not first_name or not last_name:
        flash('Patient first name and second/last name are required.', 'danger')
        return redirect(request.referrer or url_for('portals.doctor_dashboard'))

    # Parse Date of Birth or approximate from Age
    parsed_dob = None
    if dob_str:
        try:
            parsed_dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    if not parsed_dob and age_input:
        try:
            age_int = int(age_input)
            today = date.today()
            parsed_dob = date(today.year - age_int, today.month, today.day)
        except Exception:
            pass

    if not parsed_dob:
        parsed_dob = date(1990, 1, 1) # Fallback

    # Ensure Patient Role Exists
    patient_role = Role.query.filter_by(name='Patient').first()
    if not patient_role:
        patient_role = Role(name='Patient', description='Hospital Patient')
        db.session.add(patient_role)
        db.session.commit()

    # Generate a unique username for portal access
    rand_suffix = ''.join(random.choices(string.digits, k=4))
    username = f"{first_name.lower()[:3]}{last_name.lower()[:3]}_{rand_suffix}"
    email = f"{username}@patient.ihis.local"

    pat_user = User(
        username=username,
        email=email,
        role_id=patient_role.id
    )
    pat_user.set_password('patient123') # Default initial password
    db.session.add(pat_user)
    db.session.commit()

    # Create Patient Record
    new_patient = Patient(
        user_id=pat_user.id,
        first_name=first_name,
        last_name=last_name,
        date_of_birth=parsed_dob,
        gender=gender,
        blood_type=blood_type,
        phone=phone,
        drug_sensitivities=drug_sensitivities or 'None Known',
        allergies=allergies or 'None Reported',
        chronic_diseases=chronic_diseases or 'None Reported'
    )
    db.session.add(new_patient)

    # Log action
    log = AuditLog(
        user_id=current_user.id,
        action="PATIENT_REGISTERED",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'Patient {new_patient.full_name} successfully registered. (ID: #{new_patient.id})', 'success')
    return redirect(url_for('clinical.patient_records', patient_id=new_patient.id))


# --- RECORDS MATRIX HUB ---
@clinical_bp.route('/records')
@login_required
@roles_required('Doctor', 'Admin', 'Dentist', 'Rehab Therapist')
def records_matrix():
    """Central searchable electronic medical records repository."""
    search_query = request.args.get('q', '').strip()
    blood_filter = request.args.get('blood_type', 'all')
    gender_filter = request.args.get('gender', 'all')

    query = Patient.query.filter_by(is_deleted=False)

    if search_query:
        query = query.filter(
            (Patient.first_name.ilike(f'%{search_query}%')) |
            (Patient.last_name.ilike(f'%{search_query}%')) |
            (Patient.drug_sensitivities.ilike(f'%{search_query}%')) |
            (Patient.chronic_diseases.ilike(f'%{search_query}%'))
        )

    if blood_filter != 'all':
        query = query.filter_by(blood_type=blood_filter)

    if gender_filter != 'all':
        query = query.filter_by(gender=gender_filter)

    patients = query.order_by(Patient.created_at.desc()).all()
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    total_records = MedicalRecord.query.filter_by(is_deleted=False).count()
    total_vitals = VitalSigns.query.count()

    return render_template(
        'clinical/records_matrix.html',
        patients=patients,
        search_query=search_query,
        blood_filter=blood_filter,
        gender_filter=gender_filter,
        total_patients=total_patients,
        total_records=total_records,
        total_vitals=total_vitals
    )


# --- INDIVIDUAL PATIENT EMR DOSSIER ---
@clinical_bp.route('/patient/<int:patient_id>/records')
@login_required
@roles_required('Doctor', 'Admin', 'Dentist', 'Rehab Therapist')
def patient_records(patient_id):
    """Complete longitudinal medical file for a specific patient."""
    patient = Patient.query.get_or_404(patient_id)
    return render_template('clinical/patient_emr.html', patient=patient)


# --- CLINICAL EXAMINATION SHEET WORKSPACE ---
@clinical_bp.route('/patient/<int:patient_id>/examination-sheet', methods=['GET', 'POST'])
@login_required
@roles_required('Doctor', 'Admin')
def examination_sheet(patient_id):
    """Create and submit a comprehensive medical examination sheet."""
    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Extract Vitals
        def safe_int(val, default=None):
            try: return int(val) if val else default
            except (ValueError, TypeError): return default

        def safe_float(val, default=None):
            try: return float(val) if val else default
            except (ValueError, TypeError): return default

        bp_sys = safe_int(request.form.get('blood_pressure_sys'))
        bp_dia = safe_int(request.form.get('blood_pressure_dia'))
        hr = safe_int(request.form.get('heart_rate'), 80)
        temp = safe_float(request.form.get('temperature'), 37.0)
        rr = safe_int(request.form.get('respiratory_rate'))
        spo2 = safe_int(request.form.get('spo2'))

        chief_complaint = request.form.get('chief_complaint', '')
        hpi = request.form.get('hpi', '')
        drug_sensitivities_snapshot = request.form.get('drug_sensitivities', patient.drug_sensitivities)

        # Physical Exam findings
        exam_general = request.form.get('exam_general', '')
        exam_heent = request.form.get('exam_heent', '')
        exam_cardiovascular = request.form.get('exam_cardiovascular', '')
        exam_respiratory = request.form.get('exam_respiratory', '')
        exam_abdomen = request.form.get('exam_abdomen', '')
        exam_musculoskeletal = request.form.get('exam_musculoskeletal', '')
        exam_neurological = request.form.get('exam_neurological', '')

        assessment = request.form.get('assessment', '')
        plan = request.form.get('plan', '')
        icd10_codes = request.form.get('icd10_codes', '')

        # AI calculations
        calculated_risk = ClinicalAIEngine.calculate_risk_score(hr, temp)
        combined_text = f"{chief_complaint} {hpi} {assessment} {plan}"
        ai_insights = ClinicalAIEngine.generate_insights(chief_complaint, hpi, calculated_risk)

        # Save Medical Record
        new_record = MedicalRecord(
            patient_id=patient.id,
            doctor_id=current_user.id,
            encounter_type='Clinical Examination Sheet',
            chief_complaint=chief_complaint,
            hpi=hpi,
            drug_sensitivities_snapshot=drug_sensitivities_snapshot,
            blood_pressure_sys=bp_sys,
            blood_pressure_dia=bp_dia,
            heart_rate=hr,
            temperature=temp,
            respiratory_rate=rr,
            spo2=spo2,
            exam_general=exam_general,
            exam_heent=exam_heent,
            exam_cardiovascular=exam_cardiovascular,
            exam_respiratory=exam_respiratory,
            exam_abdomen=exam_abdomen,
            exam_musculoskeletal=exam_musculoskeletal,
            exam_neurological=exam_neurological,
            subjective=f"Chief Complaint: {chief_complaint}\nHPI: {hpi}",
            objective=f"BP: {bp_sys}/{bp_dia} mmHg, HR: {hr} bpm, Temp: {temp}C, SpO2: {spo2}%\nPE: {exam_general} | {exam_cardiovascular} | {exam_respiratory}",
            assessment=assessment,
            plan=plan,
            icd10_codes=icd10_codes or (ai_insights['suggested_diagnoses'][0]['code'] if ai_insights['suggested_diagnoses'] else ''),
            ai_risk_score=calculated_risk,
            ai_triage=ai_insights.get('triage_level', 'Routine'),
            ai_directives="\n".join(ai_insights.get('clinical_plan_directives', []))
        )
        db.session.add(new_record)

        # Save VitalSigns if provided
        if bp_sys and bp_dia:
            new_vitals = VitalSigns(
                patient_id=patient.id,
                recorded_by=current_user.id,
                blood_pressure_sys=bp_sys,
                blood_pressure_dia=bp_dia,
                heart_rate=hr or 80,
                temperature=temp or 37.0,
                respiratory_rate=rr,
                spo2=spo2
            )
            db.session.add(new_vitals)

        # Audit trail
        log = AuditLog(
            user_id=current_user.id,
            action="EXAMINATION_SHEET_CREATED",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        flash(f'Clinical Examination Sheet recorded successfully for {patient.full_name}.', 'success')
        return redirect(url_for('clinical.view_examination', record_id=new_record.id))

    return render_template('clinical/examination_sheet.html', patient=patient)


# --- VIEW / PRINT EXAMINATION SHEET ---
@clinical_bp.route('/examination/<int:record_id>/view')
@login_required
@roles_required('Doctor', 'Admin', 'Dentist', 'Rehab Therapist')
def view_examination(record_id):
    """View a formatted, printable clinical examination sheet."""
    record = MedicalRecord.query.get_or_404(record_id)
    return render_template('clinical/examination_view.html', record=record, patient=record.patient)


# --- LEGACY / QUICK SOAP NOTE ACTION ---
@clinical_bp.route('/patient/<int:patient_id>/add-soap', methods=['POST'])
@login_required
@roles_required('Doctor')
def add_soap_note(patient_id):
    new_note = MedicalRecord(
        patient_id=patient_id,
        doctor_id=current_user.id,
        encounter_type='SOAP Note',
        subjective=request.form.get('subjective'),
        objective=request.form.get('objective'),
        assessment=request.form.get('assessment'),
        plan=request.form.get('plan')
    )
    db.session.add(new_note)
    db.session.commit()
    flash('SOAP note added successfully.', 'success')
    return redirect(url_for('portals.doctor_dashboard'))


# --- ASYNCHRONOUS AI COMPUTE ENDPOINT ---
@clinical_bp.route('/ai-analyze', methods=['POST'])
@login_required
@roles_required('Doctor', 'Dentist', 'Rehab Therapist', 'Admin')
def ai_analyze_encounter():
    """Asynchronous JSON bridge capturing clinical inputs to feed back predictive analysis packages."""
    data = request.get_json() or {}
    subjective = data.get('subjective', '')
    objective = data.get('objective', '')
    heart_rate = data.get('heart_rate', 80)
    temperature = data.get('temperature', 37.0)

    calculated_risk = ClinicalAIEngine.calculate_risk_score(heart_rate, temperature)
    ai_payload = ClinicalAIEngine.generate_insights(subjective, objective, calculated_risk)

    return jsonify(ai_payload)