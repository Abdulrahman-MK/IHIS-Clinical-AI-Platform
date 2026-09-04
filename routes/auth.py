from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, login_manager
from models.user import User
from models.audit_log import AuditLog
from flask import redirect, url_for
from flask_login import login_required, current_user


# Initialize the authentication blueprint
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard_redirect'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username, is_deleted=False).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Create a security audit log entry
            log = AuditLog(
                user_id=user.id, 
                action="USER_LOGGED_IN", 
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Logged in successfully!', 'success')
            return redirect(url_for('auth.dashboard_redirect'))
        else:
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/dashboard-redirect')
@login_required
def dashboard_redirect():
    # Route the user to their designated dashboard template based on their DB role string
    if current_user.role.name == 'Doctor':
        return redirect(url_for('portals.doctor_dashboard')) # <-- Change this line!
        
    elif current_user.role.name == 'Patient':
        return redirect(url_for('portals.patient_dashboard'))
        
    elif current_user.role.name == 'Dentist':
        return redirect(url_for('portals.dental_dashboard'))
        
    elif current_user.role.name == 'Rehab Therapist':
        return redirect(url_for('portals.rehab_dashboard'))
        
    # If something goes wrong or role is unrecognized, send them back safely
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    log = AuditLog(
        user_id=current_user.id, 
        action="USER_LOGGED_OUT", 
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))