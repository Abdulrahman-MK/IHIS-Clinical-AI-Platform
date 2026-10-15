from dotenv import load_dotenv
load_dotenv()  # This explicitly loads the .env file fields into os.environ
import os
from flask import Flask, redirect, url_for
from config import Config
from routes.pharmacy import pharmacy_bp

# Import the shared extensions from our new file
from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    # Using db.session.get() is the safest, most modern way to query by ID
    return db.session.get(User, int(user_id))
from models.audit_log import AuditLog
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Initialize Extensions First
    db.init_app(app)
    login_manager.init_app(app)
    
    login_manager.login_view = 'auth.login' # type: ignore
    login_manager.login_message_category = 'info'

    # Ensure folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['BASE_DIR'], 'database'), exist_ok=True)

    @app.context_processor
    def inject_roles():
        return dict(roles_enabled=True)

    # 2. Open the App Context and Register Everything Else
    with app.app_context():
        # Import database tables so SQLAlchemy knows they exist
        from models.user import User, Role
        from models.audit_log import AuditLog
        from models.patient import Patient, VitalSigns, MedicalRecord
        from models.specialties import Doctor, Specialty, RehabSession
        from models.dental import DentalRecord, DentalChart, DentalProcedure
        from models.orders import LabOrder, RadiologyOrder, Prescription
        
        # Create tables if missing
        db.create_all()

        # 3. Blueprint Imports (Kept inside context to prevent circular loops!)
        from routes.auth import auth_bp
        from routes.portals import portals_bp
        from routes.clinical import clinical_bp
        from routes.orders import orders_bp
        from routes.pharmacy import pharmacy_bp
        from routes.radiology import radiology_bp
        from routes.dermatology import dermatology_bp
        from routes.dental import dental_bp
        from routes.rag import rag_bp
        
        # Automatically kick users to the login page if they visit the base URL
        @app.route('/')
        def index():
            return redirect(url_for('auth.login'))
    
        # 4. Register Blueprints (Must happen after extensions are initialized)
        app.register_blueprint(auth_bp)
        app.register_blueprint(portals_bp)
        app.register_blueprint(clinical_bp)
        app.register_blueprint(orders_bp)
        app.register_blueprint(pharmacy_bp)
        app.register_blueprint(radiology_bp)
        app.register_blueprint(dermatology_bp)
        app.register_blueprint(dental_bp)
        app.register_blueprint(rag_bp)

    # 5. Finally, return the completely built application
    return app


if __name__ == '__main__':
    app = create_app()

    is_prod = os.getenv('FLASK_ENV') == 'production'
    app.run(
        host='0.0.0.0' if is_prod else '127.0.0.1',
        port=5000,
        debug=not is_prod
    )