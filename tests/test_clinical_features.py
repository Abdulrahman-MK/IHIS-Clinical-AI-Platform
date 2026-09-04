import os
import pytest
from datetime import date
from app import create_app
from extensions import db
from models.user import Role, User
from models.patient import Patient, MedicalRecord, VitalSigns
from models.orders import LabOrder, RadiologyOrder, Prescription


@pytest.fixture(scope="session")
def app_instance():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        # Seed test roles
        for role_name in ['Doctor', 'Patient', 'Admin', 'Laboratory Technician']:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

        doc_role = Role.query.filter_by(name='Doctor').first()
        pat_role = Role.query.filter_by(name='Patient').first()

        # Doctor User
        doctor = User.query.filter_by(username='testdoctor').first()
        if not doctor:
            doctor = User(username='testdoctor', email='testdoctor@ihis.com', role_id=doc_role.id)
            doctor.set_password('password123')
            db.session.add(doctor)
            db.session.commit()

        # Patient User & Profile
        patient_user = User.query.filter_by(username='testpat').first()
        if not patient_user:
            patient_user = User(username='testpat', email='testpat@ihis.com', role_id=pat_role.id)
            patient_user.set_password('password123')
            db.session.add(patient_user)
            db.session.commit()

        patient = Patient.query.filter_by(user_id=patient_user.id).first()
        if not patient:
            patient = Patient(
                user_id=patient_user.id,
                first_name='Arthur',
                last_name='Morgan',
                date_of_birth=date(1980, 6, 22),
                gender='Male',
                blood_type='O+',
                phone='+1 555-0199',
                drug_sensitivities='Penicillin, Sulfa drugs',
                allergies='Pollen',
                chronic_diseases='Asthma'
            )
            db.session.add(patient)
            db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_patient_model_age_and_properties(app_instance):
    """Verify age calculation and full name properties on Patient model."""
    with app_instance.app_context():
        patient = Patient.query.filter_by(first_name='Arthur').first()
        assert patient is not None
        assert patient.full_name == "Arthur Morgan"
        assert isinstance(patient.age, int)
        assert patient.age >= 40
        assert patient.drug_sensitivities == "Penicillin, Sulfa drugs"
        assert patient.gender == "Male"


def test_add_patient_route(client, app_instance):
    """Test doctor registering a new patient via /clinical/patient/add."""
    with client:
        # Log in as doctor
        client.post('/login', data={'username': 'testdoctor', 'password': 'password123'}, follow_redirects=True)

        res = client.post('/clinical/patient/add', data={
            'first_name': 'Sadie',
            'last_name': 'Adler',
            'gender': 'Female',
            'age': '35',
            'blood_type': 'B+',
            'drug_sensitivities': 'Aspirin, Ibuprofen (NSAIDs)',
            'allergies': 'Bee stings',
            'chronic_diseases': 'None',
            'phone': '+1 555-0144'
        }, follow_redirects=True)

        assert res.status_code == 200

        with app_instance.app_context():
            new_pat = Patient.query.filter_by(first_name='Sadie', last_name='Adler').first()
            assert new_pat is not None
            assert new_pat.gender == 'Female'
            assert new_pat.blood_type == 'B+'
            assert 'Aspirin' in new_pat.drug_sensitivities
            assert new_pat.user is not None


def test_records_matrix_page(client):
    """Test accessing /clinical/records matrix hub with search."""
    with client:
        client.post('/login', data={'username': 'testdoctor', 'password': 'password123'}, follow_redirects=True)
        res = client.get('/clinical/records')
        assert res.status_code == 200
        assert b"Clinical Records Matrix" in res.data
        assert b"Arthur" in res.data

        # Test search filter
        search_res = client.get('/clinical/records?q=Arthur')
        assert search_res.status_code == 200
        assert b"Arthur" in search_res.data


def test_patient_emr_dossier(client, app_instance):
    """Test viewing full patient EMR dossier."""
    with client:
        client.post('/login', data={'username': 'testdoctor', 'password': 'password123'}, follow_redirects=True)
        
        with app_instance.app_context():
            pat = Patient.query.filter_by(first_name='Arthur').first()
            pat_id = pat.id

        res = client.get(f'/clinical/patient/{pat_id}/records')
        assert res.status_code == 200
        assert b"Arthur" in res.data
        assert b"Known Drug Sensitivities" in res.data
        assert b"Penicillin, Sulfa drugs" in res.data


def test_create_examination_sheet(client, app_instance):
    """Test creating and submitting a complete clinical examination sheet."""
    with client:
        client.post('/login', data={'username': 'testdoctor', 'password': 'password123'}, follow_redirects=True)

        with app_instance.app_context():
            pat = Patient.query.filter_by(first_name='Arthur').first()
            pat_id = pat.id

        # GET Examination Sheet form
        form_res = client.get(f'/clinical/patient/{pat_id}/examination-sheet')
        assert form_res.status_code == 200
        assert b"Clinical Examination Sheet" in form_res.data
        assert b"Penicillin, Sulfa drugs" in form_res.data

        # POST Submit Examination Sheet
        submit_res = client.post(f'/clinical/patient/{pat_id}/examination-sheet', data={
            'chief_complaint': 'Severe headache and elevated blood pressure',
            'hpi': 'Patient reports 2-day throbbing frontal headache with visual aura.',
            'blood_pressure_sys': '155',
            'blood_pressure_dia': '95',
            'heart_rate': '88',
            'temperature': '37.3',
            'respiratory_rate': '18',
            'spo2': '98',
            'exam_general': 'Alert, oriented, mild distress due to head pain.',
            'exam_heent': 'PERRLA, no papilledema on fundoscopic check.',
            'exam_cardiovascular': 'S1/S2 regular, no murmurs.',
            'exam_respiratory': 'Clear to auscultation.',
            'exam_abdomen': 'Soft, benign.',
            'exam_musculoskeletal': 'Normal tone and strength.',
            'exam_neurological': 'Cranial nerves intact, no focal deficits.',
            'assessment': 'Stage 2 Hypertension with tension-type headache.',
            'plan': '1. Initiate anti-hypertensive therapy.\n2. Hydration and rest.\n3. Recheck BP in 48 hours.',
            'icd10_codes': 'I10 - Essential (primary) hypertension'
        }, follow_redirects=True)

        assert submit_res.status_code == 200
        assert b"Medical Examination Report" in submit_res.data or b"Examination Sheet recorded" in submit_res.data

        with app_instance.app_context():
            record = MedicalRecord.query.filter_by(patient_id=pat_id).first()
            assert record is not None
            assert record.blood_pressure_sys == 155
            assert record.chief_complaint == 'Severe headache and elevated blood pressure'
            assert record.encounter_type == 'Clinical Examination Sheet'


def test_orders_hub_and_quick_create(client, app_instance):
    """Test Labs & Orders Hub and quick creating orders."""
    with client:
        client.post('/login', data={'username': 'testdoctor', 'password': 'password123'}, follow_redirects=True)

        # GET Orders Hub
        hub_res = client.get('/orders')
        assert hub_res.status_code == 200
        assert b"Labs &amp; Orders Central Hub" in hub_res.data or b"Labs & Orders Central Hub" in hub_res.data

        with app_instance.app_context():
            pat = Patient.query.filter_by(first_name='Arthur').first()
            pat_id = pat.id

        # Quick create a Lab Order
        lab_res = client.post('/orders/quick-create', data={
            'patient_id': str(pat_id),
            'order_type': 'lab',
            'test_name': 'Comprehensive Metabolic Panel (CMP)'
        }, follow_redirects=True)
        assert lab_res.status_code == 200

        # Quick create a Prescription
        rx_res = client.post('/orders/quick-create', data={
            'patient_id': str(pat_id),
            'order_type': 'pharmacy',
            'medication_name': 'Lisinopril',
            'dosage': '10mg',
            'frequency': 'Once daily in the morning'
        }, follow_redirects=True)
        assert rx_res.status_code == 200

        with app_instance.app_context():
            assert LabOrder.query.filter_by(patient_id=pat_id).count() >= 1
            assert Prescription.query.filter_by(patient_id=pat_id).count() >= 1
