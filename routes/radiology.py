import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models.orders import RadiologyOrder
from models.patient import Patient
from models.audit_log import AuditLog
from services.auth_helpers import roles_required
from services.radiology.xray_service import XRayFractureDetector

radiology_bp = Blueprint('radiology', __name__, url_prefix='/radiology')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@radiology_bp.route('/files/<path:filename>')
def serve_upload(filename):
    """Safely serves uploaded radiology scans and AI-annotated results."""
    upload_root = current_app.config.get('UPLOAD_FOLDER', os.path.join(current_app.root_path, 'uploads'))
    return send_from_directory(upload_root, filename)


@radiology_bp.route('/')
@radiology_bp.route('/dashboard')
@login_required
@roles_required('Doctor', 'Admin')
def dashboard():
    """Radiology department worklist and clinical orders view."""
    status_filter = request.args.get('status', 'all')
    query = RadiologyOrder.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    orders = query.order_by(RadiologyOrder.created_at.desc()).all()
    total_orders = RadiologyOrder.query.count()
    pending_orders = RadiologyOrder.query.filter_by(status='Ordered').count()
    completed_orders = RadiologyOrder.query.filter_by(status='Completed').count()

    return render_template(
        'radiology/dashboard.html',
        orders=orders,
        status_filter=status_filter,
        total_orders=total_orders,
        pending_orders=pending_orders,
        completed_orders=completed_orders
    )


@radiology_bp.route('/scan', methods=['GET', 'POST'])
@login_required
@roles_required('Doctor', 'Admin')
def interactive_scanner():
    """Interactive diagnostic workspace for on-demand X-ray AI bone & fracture analysis."""
    prediction = None
    original_rel_url = None
    annotated_rel_url = None
    sample_images = []

    # Find sample images if available
    samples_dir = os.path.join(current_app.root_path, 'static', 'sample_xrays')
    if os.path.exists(samples_dir):
        sample_images = [f for f in os.listdir(samples_dir) if allowed_file(f)]

    if request.method == 'POST':
        scan_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'scans')
        results_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'results')
        os.makedirs(scan_folder, exist_ok=True)
        os.makedirs(results_folder, exist_ok=True)

        target_file_path = None
        selected_sample = request.form.get('sample_image')

        # Check if user selected a sample image or uploaded a file
        if selected_sample and selected_sample in sample_images:
            source_sample = os.path.join(samples_dir, selected_sample)
            dest_name = f"sample_{selected_sample}"
            target_file_path = os.path.join(scan_folder, dest_name)
            # Copy to scan folder
            import shutil
            shutil.copyfile(source_sample, target_file_path)
            original_rel_url = url_for('radiology.serve_upload', filename=f"radiology/scans/{dest_name}")
        elif 'scan_file' in request.files:
            file = request.files['scan_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Timestamp prefix to prevent overwrite collisions
                import time
                unique_name = f"{int(time.time())}_{filename}"
                target_file_path = os.path.join(scan_folder, unique_name)
                file.save(target_file_path)
                original_rel_url = url_for('radiology.serve_upload', filename=f"radiology/scans/{unique_name}")
            else:
                flash('Please upload a valid image file (.png, .jpg, .jpeg).', 'warning')
                return redirect(url_for('radiology.interactive_scanner'))

        if target_file_path and os.path.exists(target_file_path):
            try:
                prediction = XRayFractureDetector.analyze_xray(
                    image_path=target_file_path,
                    output_dir=results_folder
                )
                if prediction.get('annotated_filename'):
                    annotated_rel_url = url_for(
                        'radiology.serve_upload',
                        filename=f"radiology/results/{prediction['annotated_filename']}"
                    )

                # Log AI scan run in audit trail
                log = AuditLog(
                    user_id=current_user.id,
                    action="AI_XRAY_ANALYSIS_EXECUTED",
                    ip_address=request.remote_addr
                )
                db.session.add(log)
                db.session.commit()

            except Exception as e:
                flash(f"Error executing AI model: {str(e)}", 'danger')

    patients = Patient.query.filter_by(is_deleted=False).all()

    return render_template(
        'radiology/scan.html',
        prediction=prediction,
        original_url=original_rel_url,
        annotated_url=annotated_rel_url,
        sample_images=sample_images,
        patients=patients
    )


@radiology_bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
@login_required
@roles_required('Doctor', 'Admin')
def order_detail(order_id):
    """View a specific radiology order, upload scan image, and run AI detection."""
    order = RadiologyOrder.query.get_or_404(order_id)
    patient = Patient.query.get(order.patient_id)

    if request.method == 'POST':
        # Handle Scan Upload and Analysis
        scan_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'scans')
        results_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'results')
        os.makedirs(scan_folder, exist_ok=True)
        os.makedirs(results_folder, exist_ok=True)

        if 'scan_file' in request.files:
            file = request.files['scan_file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                unique_name = f"order_{order.id}_{int(time.time())}_{filename}"
                saved_path = os.path.join(scan_folder, unique_name)
                file.save(saved_path)

                # Run AI Model
                prediction = XRayFractureDetector.analyze_xray(
                    image_path=saved_path,
                    output_dir=results_folder
                )

                # Update Order Record
                order.image_url = f"radiology/results/{prediction['annotated_filename']}" if prediction.get('annotated_filename') else f"radiology/scans/{unique_name}"
                order.status = 'Completed'
                order.findings = prediction.get('clinical_impression', '')
                
                # Append formatted recommendations
                recs = prediction.get('recommendations', [])
                if recs:
                    order.findings += "\n\nDirectives:\n- " + "\n- ".join(recs)

                db.session.commit()
                flash('X-ray analyzed and findings updated successfully with AI assistance.', 'success')
                return redirect(url_for('radiology.order_detail', order_id=order.id))

    return render_template('radiology/order_detail.html', order=order, patient=patient)


@radiology_bp.route('/api/analyze', methods=['POST'])
@login_required
@roles_required('Doctor', 'Admin')
def api_analyze():
    """Asynchronous JSON API endpoint for external or AJAX UI calls."""
    if 'scan_file' not in request.files:
        return jsonify({"status": "error", "message": "No scan file provided"}), 400

    file = request.files['scan_file']
    if not file or file.filename == '' or not allowed_file(file.filename):
        return jsonify({"status": "error", "message": "Invalid file format"}), 400

    scan_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'scans')
    results_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'radiology', 'results')
    os.makedirs(scan_folder, exist_ok=True)
    os.makedirs(results_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    import time
    unique_name = f"api_{int(time.time())}_{filename}"
    saved_path = os.path.join(scan_folder, unique_name)
    file.save(saved_path)

    prediction = XRayFractureDetector.analyze_xray(
        image_path=saved_path,
        output_dir=results_folder
    )

    if prediction.get('annotated_filename'):
        prediction['annotated_image_url'] = url_for('radiology.serve_upload', filename=f"radiology/results/{prediction['annotated_filename']}")
    prediction['original_image_url'] = url_for('radiology.serve_upload', filename=f"radiology/scans/{unique_name}")

    return jsonify(prediction)
