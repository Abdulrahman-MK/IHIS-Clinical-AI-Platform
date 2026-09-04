# routes/orders.py
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.audit_log import AuditLog
from models.orders import LabOrder, RadiologyOrder, Prescription
from services.auth_helpers import roles_required

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# --- DOCTOR ACTION: Create an Order ---
@orders_bp.route('/create/<string:order_type>/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Doctor')
def create_order(order_type, patient_id):
    if order_type == 'lab':
        new_order = LabOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            test_name=request.form.get('test_name')
        )
    elif order_type == 'radiology':
        new_order = RadiologyOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            imaging_type=request.form.get('imaging_type')
        )
    elif order_type == 'pharmacy':
        new_order = Prescription(
            patient_id=patient_id,
            doctor_id=current_user.id,
            medication_name=request.form.get('medication_name'),
            dosage=request.form.get('dosage'),
            frequency=request.form.get('frequency')
        )
    else:
        flash('Invalid order type selection.', 'danger')
        return redirect(url_for('portals.doctor_dashboard'))

    db.session.add(new_order)
    
    # Audit log
    log_entry = AuditLog(
        user_id=current_user.id,
        action=f"CREATE_{order_type.upper()}_ORDER",
        ip_address=request.remote_addr
    )
    db.session.add(log_entry)
    db.session.commit()

    flash(f'{order_type.capitalize()} order routed successfully.', 'success')
    return redirect(url_for('portals.doctor_dashboard'))

# --- TECHNICIAN ACTION: Update Order Status / Add Results ---
@orders_bp.route('/update-lab/<int:order_id>', methods=['POST'])
@login_required
@roles_required('Laboratory Technician', 'Admin')
def update_lab(order_id):
    order = LabOrder.query.get_or_404(order_id)
    order.results = request.form.get('results')
    order.status = 'Completed'
    db.session.commit()
    flash('Laboratory diagnostic results published.', 'success')
    return redirect(url_for('portals.dashboard_redirect'))