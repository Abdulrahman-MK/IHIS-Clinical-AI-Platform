import time

def run_grok_pharmacy_review(patient_data):
    """
    Mocked Clinical Decision Support Service for testing UI/Flask flows
    without an external API key.
    """
    # Simulate a brief network call delay
    time.sleep(1)

    patient_name = patient_data.get('name', 'Patient')
    meds = patient_data.get('medications', 'None reported')
    egfr = patient_data.get('egfr', 'N/A')

    # Realistic mock clinical safety response
    mock_response = f"""
## 🏥 Clinical Medication Safety Review for {patient_name}

---

### 1. ⚠️ Severe Drug Interactions
* **High Risk Identified:** Potential interaction detected between prescribed agents. Close monitoring for QT prolongation or altered plasma concentrations recommended.

### 2. 🩺 Drug-Disease & Organ Function Warnings
* **Renal Function Status (eGFR: {egfr} mL/min/1.73m²):**
  * Evaluate renal-dosed medications. Adjustment recommended if eGFR < 60 mL/min/1.73m².

### 3. 📋 Current Medication Profile Assessed
{meds}

### 4. 💡 Clinical Recommendations & Monitoring
* Monitor serum electrolytes (K+, Na+) and renal function panels within 7–14 days.
* Confirm patient compliance and check for duplicate therapeutic classes.
* *Note: System operating in local evaluation mode.*
"""
    return mock_response