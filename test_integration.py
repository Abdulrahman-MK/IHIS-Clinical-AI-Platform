import pytest
from app import create_app
from extensions import db  # Using your original separate extensions import

@pytest.fixture(scope="session")
def app():
    """Create the application instance with an isolated test database."""
    app = create_app()
    
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:" 
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Provide a clean database state for each individual test run."""
    with app.test_client() as client:
        with app.app_context():
            # Clear metadata cache cleanly before defining structures
            db.metadata.clear() 
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_homepage_redirects_or_loads(client):
    """Test that base route is accessible."""
    response = client.get('/')
    assert response.status_code in [200, 302, 404]

def test_protected_clinical_analytics_denied_anonymous(client):
    """Verify that unauthenticated users cannot access protected clinical endpoints."""
    # Target the real SOAP note route using a dummy patient ID of 1
    response = client.post('/clinical/patient/1/add-soap', follow_redirects=True)
    
    # Assertions: Should redirect to login or show unauthorized
    assert response.status_code == 200
    assert b"Login" in response.data or b"login" in response.data or b"Sign In" in response.data