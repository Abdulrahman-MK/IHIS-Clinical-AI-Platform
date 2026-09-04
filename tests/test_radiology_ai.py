import os
import io
import pytest
from app import create_app
from extensions import db
from models.user import Role, User
from models.patient import Patient
from models.orders import RadiologyOrder
from services.radiology.xray_service import XRayFractureDetector
from datetime import date


@pytest.fixture(scope="function")
def app_instance():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    with app.app_context():
        db.create_all()
        # Seed test role & user safely
        for role_name in ['Doctor', 'Patient', 'Admin']:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

        doc_role = Role.query.filter_by(name='Doctor').first()
        pat_role = Role.query.filter_by(name='Patient').first()

        if not User.query.filter_by(username='testdoctor').first():
            doctor = User(username='testdoctor', email='testdoctor@ihis.com', role_id=doc_role.id)
            doctor.set_password('password123')
            db.session.add(doctor)

        if not User.query.filter_by(username='testpatient').first():
            patient_user = User(username='testpatient', email='testpatient@ihis.com', role_id=pat_role.id)
            patient_user.set_password('password123')
            db.session.add(patient_user)
            db.session.commit()

            patient_profile = Patient(
                user_id=patient_user.id,
                first_name='Jane',
                last_name='Smith',
                date_of_birth=date(1985, 3, 20),
                blood_type='A+',
                allergies='None'
            )
            db.session.add(patient_profile)

        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app_instance):
    return app_instance.test_client()


def test_ai_xray_model_direct_inference():
    """Test that XRayFractureDetector loads the offline YOLO weights and generates predictions."""
    sample_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'sample_xrays')
    sample_files = [f for f in os.listdir(sample_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    assert len(sample_files) > 0, "No sample X-ray files found for testing"
    
    sample_path = os.path.join(sample_dir, sample_files[0])
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'test_results')
    
    report = XRayFractureDetector.analyze_xray(
        image_path=sample_path,
        output_dir=output_dir,
        conf_threshold=0.15
    )

    assert report['status'] == 'success'
    assert 'has_fracture' in report
    assert 'fracture_confidence' in report
    assert 'anatomy' in report
    assert 'hardware_detected' in report
    assert 'triage_level' in report
    assert 'clinical_impression' in report
    assert isinstance(report['recommendations'], list)
    assert 'detections' in report
    assert report['annotated_filename'] is not None

    # Check that the annotated image was written to disk
    annotated_path = os.path.join(output_dir, report['annotated_filename'])
    assert os.path.exists(annotated_path)


def test_radiology_dashboard_unauthenticated_access(client):
    """Anonymous users should be redirected to login when accessing radiology endpoints."""
    res = client.get('/radiology/dashboard')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']


def test_radiology_dashboard_authenticated(client):
    """Doctor login should grant access to radiology worklist."""
    with client:
        login_res = client.post('/login', data={
            'username': 'testdoctor',
            'password': 'password123'
        }, follow_redirects=True)
        assert login_res.status_code == 200

        dash_res = client.get('/radiology/dashboard')
        assert dash_res.status_code == 200
        assert b"Radiology Department" in dash_res.data
        assert b"Launch Real-Time AI X-Ray Scanner" in dash_res.data


def test_radiology_scanner_page_authenticated(client):
    """Doctor can access the interactive scanner interface."""
    with client:
        client.post('/login', data={
            'username': 'testdoctor',
            'password': 'password123'
        }, follow_redirects=True)

        res = client.get('/radiology/scan')
        assert res.status_code == 200
        assert b"Scanner" in res.data


def test_radiology_api_analyze_with_image(client):
    """Test POST /radiology/api/analyze with an image payload."""
    with client:
        client.post('/login', data={
            'username': 'testdoctor',
            'password': 'password123'
        }, follow_redirects=True)

        sample_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'sample_xrays')
        sample_files = [f for f in os.listdir(sample_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
        sample_path = os.path.join(sample_dir, sample_files[0])

        with open(sample_path, 'rb') as f:
            img_bytes = f.read()

        data = {
            'scan_file': (io.BytesIO(img_bytes), 'test_scan.jpg')
        }

        res = client.post('/radiology/api/analyze', data=data, content_type='multipart/form-data')
        assert res.status_code == 200
        json_data = res.get_json()
        assert json_data['status'] == 'success'
        assert 'clinical_impression' in json_data
        assert 'has_fracture' in json_data
