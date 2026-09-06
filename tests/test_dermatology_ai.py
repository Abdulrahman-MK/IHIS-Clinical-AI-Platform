import os
import io
import pytest
from PIL import Image
from app import create_app
from extensions import db
from models.user import Role, User
from models.audit_log import AuditLog
from services.dermatology_ai import predict_lesion

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
        for role_name in ['Doctor', 'Patient', 'Admin']:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()


        doc_role = Role.query.filter_by(name='Doctor').first()
        if not User.query.filter_by(username='derm_doctor').first():
            doctor = User(username='derm_doctor', email='derm@ihis.com', role_id=doc_role.id)
            doctor.set_password('password123')
            db.session.add(doctor)
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app_instance):
    return app_instance.test_client()

def test_dermatology_model_direct_inference():
    """Test direct EfficientNet-B0 inference on synthetic image bytes."""
    img = Image.new('RGB', (224, 224), color=(180, 100, 80))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    
    result = predict_lesion(buf)
    assert 'label' in result
    assert result['label'] in ['Nevus', 'Malignant Melanoma']
    assert 'confidence' in result
    assert 0.0 <= result['confidence'] <= 100.0

def test_dermatology_upload_page_unauthenticated(client):
    """Ensure unauthenticated access redirects to login."""
    res = client.get('/dermatology/analyze')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

def test_dermatology_upload_flow_authenticated(client):
    """Ensure authenticated doctor can upload and classify an image."""
    with client:
        login_res = client.post('/login', data={
            'username': 'derm_doctor',
            'password': 'password123'
        }, follow_redirects=True)
        assert login_res.status_code == 200

        # GET upload page
        page_res = client.get('/dermatology/analyze')
        assert page_res.status_code == 200
        assert b'Skin Lesion Diagnostic Engine' in page_res.data

        # POST image for classification
        img = Image.new('RGB', (224, 224), color=(200, 120, 90))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)

        post_res = client.post('/dermatology/analyze', data={
            'file': (buf, 'lesion.jpg')
        }, content_type='multipart/form-data')

        assert post_res.status_code == 200
        assert b'Diagnostic Output' in post_res.data
        assert b'Model Confidence' in post_res.data
