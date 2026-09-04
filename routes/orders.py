from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template
from flask_login import login_required, current_user
from extensions import db
from models.audit_log import AuditLog
from models.patient import Patient
from models.orders import LabOrder, RadiologyOrder, Prescription
from services.auth_helpers import roles_required

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


# --- CENTRAL ORDERS MATRIX HUB ---
@orders_bp.route('', strict_slashes=False)
@orders_bp.route('/', strict_slashes=False)
@orders_bp.route('/hub', strict_slashes=False)
@login_required
@roles_required('Doctor', 'Admin', 'Laboratory Technician')
def orders_hub():
    """Unified Clinical Orders Hub managing Labs, Radiology, and Prescriptions."""
    order_filter = request.args.get('tab', 'all')
    status_filter = request.args.get('status', 'all')

    lab_query = LabOrder.query
    rad_query = RadiologyOrder.query
    rx_query = Prescription.query

    if status_filter != 'all':
        lab_query = lab_query.filter_by(status=status_filter)
        rad_query = rad_query.filter_by(status=status_filter)
        rx_query = rx_query.filter_by(status=status_filter)

    lab_orders = lab_query.order_by(LabOrder.created_at.desc()).all()
    radiology_orders = rad_query.order_by(RadiologyOrder.created_at.desc()).all()
    prescriptions = rx_query.order_by(Prescription.created_at.desc()).all()

    total_labs = LabOrder.query.count()
    pending_labs = LabOrder.query.filter_by(status='Pending').count()
    total_rads = RadiologyOrder.query.count()
    pending_rads = RadiologyOrder.query.filter_by(status='Ordered').count()
    total_rxs = Prescription.query.count()
    active_rxs = Prescription.query.filter_by(status='Active').count()

    patients = Patient.query.filter_by(is_deleted=False).all()

    return render_template(
        'orders/hub.html',
        lab_orders=lab_orders,
        radiology_orders=radiology_orders,
        prescriptions=prescriptions,
        total_labs=total_labs,
        pending_labs=pending_labs,
        total_rads=total_rads,
        pending_rads=pending_rads,
        total_rxs=total_rxs,
        active_rxs=active_rxs,
        order_filter=order_filter,
        status_filter=status_filter,
        patients=patients
    )


# --- DOCTOR ACTION: Unified Quick Create Order ---
@orders_bp.route('/quick-create', methods=['POST'])
@login_required
@roles_required('Doctor', 'Admin')
def quick_create():
    """Quick modal order creation for Labs, Radiology, or Pharmacy."""
    order_type = request.form.get('order_type')
    patient_id = request.form.get('patient_id')

    if not patient_id or not order_type:
        flash('Patient and Order Type must be selected.', 'warning')
        return redirect(url_for('orders.orders_hub'))

    patient_id = int(patient_id)

    if order_type == 'lab':
        test_name = request.form.get('test_name', 'Routine Blood Panel')
        new_order = LabOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            test_name=test_name,
            status='Pending'
        )
    elif order_type == 'radiology':
        imaging_type = request.form.get('imaging_type', 'X-Ray Examination')
        new_order = RadiologyOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            imaging_type=imaging_type,
            status='Ordered'
        )
    elif order_type == 'pharmacy':
        med_name = request.form.get('medication_name', '')
        dosage = request.form.get('dosage', 'Standard')
        freq = request.form.get('frequency', 'Once Daily')
        new_order = Prescription(
            patient_id=patient_id,
            doctor_id=current_user.id,
            medication_name=med_name,
            dosage=dosage,
            frequency=freq,
            status='Active'
        )
    else:
        flash('Invalid order type selection.', 'danger')
        return redirect(url_for('orders.orders_hub'))

    db.session.add(new_order)

    # Log action
    log = AuditLog(
        user_id=current_user.id,
        action=f"CREATE_{order_type.upper()}_ORDER",
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()

    flash(f'{order_type.capitalize()} order registered successfully.', 'success')
    return redirect(request.referrer or url_for('orders.orders_hub'))


# --- DOCTOR ACTION: Create Order via Direct Route ---
@orders_bp.route('/create/<string:order_type>/<int:patient_id>', methods=['POST'])
@login_required
@roles_required('Doctor', 'Admin')
def create_order(order_type, patient_id):
    if order_type == 'lab':
        new_order = LabOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            test_name=request.form.get('test_name', 'General Lab Order')
        )
    elif order_type == 'radiology':
        new_order = RadiologyOrder(
            patient_id=patient_id,
            doctor_id=current_user.id,
            imaging_type=request.form.get('imaging_type', 'X-Ray General')
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
    return redirect(request.referrer or url_for('portals.doctor_dashboard'))


# --- TECHNICIAN ACTION: Update Order Status / Add Results ---
@orders_bp.route('/update-lab/<int:order_id>', methods=['POST'])
@login_required
@roles_required('Laboratory Technician', 'Admin', 'Doctor')
def update_lab(order_id):
    order = LabOrder.query.get_or_404(order_id)
    order.results = request.form.get('results')
    order.status = 'Completed'
    db.session.commit()
    flash('Laboratory diagnostic results published.', 'success')
    return redirect(request.referrer or url_for('orders.orders_hub'))