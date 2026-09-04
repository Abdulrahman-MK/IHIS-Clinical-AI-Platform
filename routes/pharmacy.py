from flask import Blueprint, render_template, request, jsonify
from services.grok_service import run_grok_pharmacy_review

pharmacy_bp = Blueprint('pharmacy', __name__, url_prefix='/pharmacy')

@pharmacy_bp.route('/review', methods=['GET', 'POST'])
def review_page():
    review_result = None
    patient_data = {}  # Initialize so Jinja never throws UndefinedError

    if request.method == 'POST':
        patient_data = {
            'name': request.form.get('name', 'Jane Doe'),
            'age': request.form.get('age', '64'),
            'sex': request.form.get('sex', 'Female'),
            'egfr': request.form.get('egfr', '45'),
            'medications': request.form.get('medications', '')
        }
        review_result = run_grok_pharmacy_review(patient_data)

    return render_template(
        'pharmacy/index.html',
        review_result=review_result,
        patient_data=patient_data
    )

# Endpoint if your page submits via JavaScript / fetch to /pharmacy/api/analyze
@pharmacy_bp.route('/api/analyze', methods=['POST'])
def analyze_api():
    data = request.get_json() or {}
    result = run_grok_pharmacy_review(data)
    return jsonify({'result': result})