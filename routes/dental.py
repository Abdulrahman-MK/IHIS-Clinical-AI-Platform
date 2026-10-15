from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
try:
    from services.dental_ai import predict_segmentation
except Exception:
    predict_segmentation = None

dental_bp = Blueprint('dental', __name__, url_prefix='/dental')

@dental_bp.route('/xray', methods=['GET'])
@login_required
def xray_view():
    """Renders the dental X-ray upload and AI analysis interface."""
    return render_template('dental/xray_analysis.html')

@dental_bp.route('/analyze', methods=['POST'])
@login_required
def analyze_xray():
    """Receives X-ray file upload and returns segmentation mask via JSON."""
    file = request.files.get('xray') or request.files.get('file')
    
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    if predict_segmentation is None:
        return jsonify({'error': 'Dental AI service unavailable. Please install tensorflow in your environment.'}), 503

    try:
        # Run model inference
        results = predict_segmentation(file.read())

        # Extract mask and overlay depending on predict_segmentation return format
        if isinstance(results, dict):
            mask = results.get('mask')
            overlay = results.get('overlay', mask)
        else:
            mask = results
            overlay = results

        return jsonify({
            'success': True,
            'mask': mask,
            'overlay': overlay
        }), 200

    except Exception as e:
        return jsonify({'error': f"AI processing failed: {str(e)}"}), 500