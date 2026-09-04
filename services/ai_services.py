# services/ai_service.py
import re

class ClinicalAIEngine:
    @staticmethod
    def calculate_risk_score(heart_rate, temperature):
        """
        Calculates a simple heuristic risk index (R) based on physiological strain metrics.
        Formula: R = (HR / 100) + (Temp - 37.0)
        """
        try:
            hr = float(heart_rate) if heart_rate else 80.0
            temp = float(temperature) if temperature else 37.0
        except ValueError:
            hr, temp = 80.0, 37.0

        # Technical heuristic tracking physiological outliers
        risk = (hr / 100.0) + (temp - 37.0)
        return round(max(0.0, risk), 2)

    @staticmethod
    def generate_insights(subjective_text, objective_text, risk_score):
        """
        Parses SOAP text streams to map clinical keywords into predictive insights and diagnostic tags.
        """
        text_to_analyze = f"{subjective_text or ''} {objective_text or ''}".lower()
        
        diagnoses = []
        recommendations = []
        triage_level = "Routine"

        # Diagnostic Heuristic Mapping Rules
        if any(w in text_to_analyze for w in ["cough", "fever", "chest pain", "shortness of breath"]):
            diagnoses.append({"code": "J22", "description": "Unspecified acute lower respiratory infection"})
            recommendations.append("Order automated posterior-anterior (PA) chest X-ray panel.")
            
        if any(w in text_to_analyze for w in ["toothache", "gum", "cavity", "dental pain"]):
            diagnoses.append({"code": "K02.9", "description": "Dental caries, unspecified"})
            recommendations.append("Route immediate intraoral periapical radiograph request to Dental Sciences.")

        if any(w in text_to_analyze for w in ["knee", "fracture", "swelling", "joint", "sprain"]):
            diagnoses.append({"code": "M25.56", "description": "Pain in knee joint"})
            recommendations.append("Schedule physical therapy range-of-motion assessment via Rehab module.")

        # Escalation criteria based on composite score matrix
        if risk_score > 1.5:
            triage_level = "Emergent Escalation Required"
            recommendations.insert(0, "CRITICAL: Patient metrics meet outlier thresholds. Notify attending specialist immediately.")
        elif risk_score > 0.8:
            triage_level = "Urgent Review"

        # Fallback default if no keywords match
        if not diagnoses:
            diagnoses.append({"code": "Z00.00", "description": "General adult medical examination without abnormal findings"})
            recommendations.append("Maintain baseline standard preventive clinical tracking.")

        return {
            "risk_score": risk_score,
            "triage_level": triage_level,
            "suggested_diagnoses": diagnoses,
            "clinical_plan_directives": recommendations
        }