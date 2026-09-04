# seed.py
from datetime import date, datetime
from app import create_app
from extensions import db
from models.user import Role, User
from models.patient import Patient, MedicalRecord, VitalSigns
from models.orders import LabOrder, RadiologyOrder, Prescription

app = create_app()

with app.app_context():
    # 1. Ensure all database tables exist
    db.create_all()

    # 2. Add System Roles if they don't exist yet
    roles = ['Admin', 'Doctor', 'Dentist', 'Rehab Therapist', 'Patient', 'Laboratory Technician']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()

    # 3. Create a Test Doctor Account
    doctor_role = Role.query.filter_by(name='Doctor').first()
    doc_user = User.query.filter_by(username='doctor1').first()
    if not doc_user:
        doc_user = User(username='doctor1', email='doctor@ihis.com', role_id=doctor_role.id)
        doc_user.set_password('password123')
        db.session.add(doc_user)
        db.session.commit()

    # 4. Create Test Patients
    patient_role = Role.query.filter_by(name='Patient').first()
    
    # Patient 1: John Doe
    pat1 = User.query.filter_by(username='patient1').first()
    if not pat1:
        pat1 = User(username='patient1', email='patient@ihis.com', role_id=patient_role.id)
        pat1.set_password('password123')
        db.session.add(pat1)
        db.session.commit()

        p1_profile = Patient(
            user_id=pat1.id,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1988, 5, 15),
            gender='Male',
            blood_type='O+',
            phone='+1 (555) 234-8901',
            drug_sensitivities='Penicillin (Severe Anaphylaxis), Cephalosporins',
            allergies='Latex',
            chronic_diseases='Mild Hypertension'
        )
        db.session.add(p1_profile)
        db.session.commit()

        # Vitals for Patient 1
        v1 = VitalSigns(
            patient_id=p1_profile.id,
            recorded_by=doc_user.id,
            blood_pressure_sys=128,
            blood_pressure_dia=82,
            heart_rate=78,
            temperature=37.1,
            respiratory_rate=16,
            spo2=99
        )
        db.session.add(v1)

        # Examination Sheet for Patient 1
        exam1 = MedicalRecord(
            patient_id=p1_profile.id,
            doctor_id=doc_user.id,
            encounter_type='Clinical Examination Sheet',
            chief_complaint='Acute right wrist trauma with localized pain following basketball injury.',
            hpi='Patient reports falling onto outstretched right hand 2 hours ago. Immediate pain, swelling, and decreased grip strength.',
            drug_sensitivities_snapshot='Penicillin (Severe Anaphylaxis), Cephalosporins',
            blood_pressure_sys=128,
            blood_pressure_dia=82,
            heart_rate=78,
            temperature=37.1,
            respiratory_rate=16,
            spo2=99,
            exam_general='Alert, oriented x3, moderate discomfort due to right wrist pain.',
            exam_heent='Normocephalic, atraumatic.',
            exam_cardiovascular='Regular rate and rhythm, normal S1/S2.',
            exam_respiratory='Clear to auscultation bilaterally.',
            exam_abdomen='Soft, non-tender.',
            exam_musculoskeletal='Right wrist: localized swelling and point tenderness over distal radius. Radial pulse 2+ palpable.',
            exam_neurological='Sensation intact to median, ulnar, and radial nerve distributions.',
            subjective='Chief Complaint: Acute right wrist pain after fall.',
            objective='BP: 128/82, HR: 78, Right wrist swelling and tenderness over distal radius.',
            assessment='Suspected distal radius fracture; rule out scaphoid injury.',
            plan='1. Immobilize with volar wrist splint.\n2. Stat X-Ray Wrist AP & Lateral to Radiology AI.\n3. Non-penicillin analgesia (Acetaminophen 650mg Q6H PRN).',
            icd10_codes='S52.501A - Fracture of lower end of right radius',
            ai_risk_score=0.78,
            ai_triage='Routine Triage',
            ai_directives='Order automated posterior-anterior (PA) chest/wrist imaging panel.'
        )
        db.session.add(exam1)

        # Orders for Patient 1
        rad1 = RadiologyOrder(
            patient_id=p1_profile.id,
            doctor_id=doc_user.id,
            imaging_type='X-Ray Wrist / Hand (AP & Lateral)',
            status='Ordered'
        )
        rx1 = Prescription(
            patient_id=p1_profile.id,
            doctor_id=doc_user.id,
            medication_name='Acetaminophen (Tylenol)',
            dosage='650mg',
            frequency='Every 6 hours as needed for pain',
            status='Active'
        )
        lab1 = LabOrder(
            patient_id=p1_profile.id,
            doctor_id=doc_user.id,
            test_name='Complete Blood Count (CBC)',
            status='Completed',
            results='WBC: 7.2 x10^3/uL (Normal), Hemoglobin: 15.1 g/dL, Platelets: 245 x10^3/uL'
        )
        db.session.add_all([rad1, rx1, lab1])

    # Patient 2: Jane Smith
    pat2 = User.query.filter_by(username='patient2').first()
    if not pat2:
        pat2 = User(username='patient2', email='janesmith@ihis.com', role_id=patient_role.id)
        pat2.set_password('password123')
        db.session.add(pat2)
        db.session.commit()

        p2_profile = Patient(
            user_id=pat2.id,
            first_name='Jane',
            last_name='Smith',
            date_of_birth=date(1962, 11, 28),
            gender='Female',
            blood_type='A+',
            phone='+1 (555) 789-1234',
            drug_sensitivities='Aspirin & NSAIDs (Bronchospasm/Asthma exacerbation)',
            allergies='Sulfa drugs',
            chronic_diseases='Type 2 Diabetes, Osteoarthritis'
        )
        db.session.add(p2_profile)
        db.session.commit()

        rad2 = RadiologyOrder(
            patient_id=p2_profile.id,
            doctor_id=doc_user.id,
            imaging_type='X-Ray Lower Extremity / Leg',
            status='Completed',
            findings='POSITIVE FOR FRACTURE: Structural cortical discontinuity identified in Lower Extremity / Leg with 88.4% AI confidence.'
        )
        rx2 = Prescription(
            patient_id=p2_profile.id,
            doctor_id=doc_user.id,
            medication_name='Metformin HCl',
            dosage='500mg',
            frequency='Twice daily with meals',
            status='Active'
        )
        db.session.add_all([rad2, rx2])

    db.session.commit()
    print("Database successfully seeded! Doctor login: 'doctor1' | Password: 'password123'")