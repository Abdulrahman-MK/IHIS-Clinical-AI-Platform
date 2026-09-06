from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from services.dermatology_ai import predict_lesion
from extensions import db
from models.audit_log import AuditLog

dermatology_bp = Blueprint('dermatology', __name__, url_prefix='/dermatology')

@dermatology_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze_lesion():
    if request.method == 'POST':
        if 'file' not in request.files or request.files['file'].filename == '':
            flash('No image file selected.', 'warning')
            return redirect(request.url)

        file = request.files['file']
        try:
            result = predict_lesion(file.stream)

            # Record inference in system audit log
            log_entry = AuditLog(
                user_id=current_user.id if current_user.is_authenticated else None,
                action="LESION_CLASSIFICATION",
                details=f"Outcome: {result['label']} ({result['confidence']}% confidence)",
                ip_address=request.remote_addr
            )
            db.session.add(log_entry)
            db.session.commit()

            return render_template('portals/dermatology_result.html', result=result)
        except Exception as e:
            flash(f"Error during lesion classification: {str(e)}", "danger")
            return redirect(request.url)

    return render_template('portals/dermatology_upload.html')