# seed.py
from app import create_app
from extensions import db
from models.user import Role, User
from models.patient import Patient
from datetime import date

app = create_app()

with app.app_context():
    # 1. Clear out any accidental partial table formats
    db.create_all()

    # 2. Add System Roles if they don't exist yet
    roles = ['Admin', 'Doctor', 'Dentist', 'Rehab Therapist', 'Patient']
    for role_name in roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()

    # 3. Create a Test Doctor Account
    doctor_role = Role.query.filter_by(name='Doctor').first()
    if not User.query.filter_by(username='doctor1').first():
        doc_user = User(username='doctor1', email='doctor@ihis.com', role_id=doctor_role.id)
        doc_user.set_password('password123') # Clear text password hook
        db.session.add(doc_user)
    
    # 4. Create a Test Patient Account
    patient_role = Role.query.filter_by(name='Patient').first()
    if not User.query.filter_by(username='patient1').first():
        pat_user = User(username='patient1', email='patient@ihis.com', role_id=patient_role.id)
        pat_user.set_password('password123')
        db.session.add(pat_user)
        db.session.commit()

        # Connect the user account to a physical clinical patient file
        new_profile = Patient(
            user_id=pat_user.id,
            first_name='John',
            last_name='Doe',
            date_of_birth=date(1990, 5, 15),
            blood_type='O+',
            allergies='Penicillin',
            chronic_diseases='None'
        )
        db.session.add(new_profile)
        db.session.commit()

        # 5. Create Sample Radiology Orders
        from models.orders import RadiologyOrder
        doc = User.query.filter_by(username='doctor1').first()
        if not RadiologyOrder.query.filter_by(patient_id=new_profile.id).first():
            order1 = RadiologyOrder(
                patient_id=new_profile.id,
                doctor_id=doc.id,
                imaging_type='X-Ray Wrist / Hand (AP & Lateral)',
                status='Ordered',
                findings=None
            )
            order2 = RadiologyOrder(
                patient_id=new_profile.id,
                doctor_id=doc.id,
                imaging_type='X-Ray Left Lower Extremity / Leg',
                status='Completed',
                findings='POSITIVE FOR FRACTURE: Structural cortical discontinuity identified in Lower Extremity / Leg with 88.4% AI confidence.'
            )
            db.session.add_all([order1, order2])

    db.session.commit()
    print("Database successfully seeded! Logins: 'doctor1' or 'patient1' with password: 'password123'")