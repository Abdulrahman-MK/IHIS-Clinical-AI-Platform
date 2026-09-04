import os
import cv2
import numpy as np
from datetime import datetime

# Lazy import for ultralytics so application starts fast
_yolo_model = None

def get_yolo_model():
    """Singleton getter to load the YOLO model once in memory."""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'best.pt')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Radiology AI model weights not found at {model_path}")
        _yolo_model = YOLO(model_path)
    return _yolo_model


class XRayFractureDetector:
    """
    Diagnostic service wrapping the offline YOLO bone fracture and identification model.
    Supported classes:
      - 0: 'fractured'
      - 1: 'hand'
      - 2: 'hardware'
      - 3: 'hip'
      - 4: 'leg'
      - 5: 'shoulder'
    """

    ANATOMICAL_CLASSES = {'hand': 'Hand / Wrist', 'hip': 'Hip / Pelvis', 'leg': 'Lower Extremity / Leg', 'shoulder': 'Shoulder / Clavicle'}

    @classmethod
    def analyze_xray(cls, image_path, output_dir=None, conf_threshold=0.20):
        """
        Runs bone fracture & anatomical location inference on an X-ray image.

        Args:
            image_path (str): Path to input X-ray image.
            output_dir (str, optional): Directory to save annotated visualization.
            conf_threshold (float): Confidence threshold for YOLO detection.

        Returns:
            dict: Structured diagnostic report.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Target X-ray image file not found: {image_path}")

        model = get_yolo_model()
        results = model.predict(source=image_path, conf=conf_threshold, verbose=False)
        result = results[0]

        detections = []
        has_fracture = False
        max_fracture_conf = 0.0
        detected_anatomy = set()
        hardware_detected = False
        max_hardware_conf = 0.0

        boxes = result.boxes
        if boxes is not None and len(boxes) > 0:
            for i in range(len(boxes)):
                cls_idx = int(boxes.cls[i].item())
                class_name = model.names.get(cls_idx, f"class_{cls_idx}")
                conf = float(boxes.conf[i].item())
                xyxy = [round(coord, 1) for coord in boxes.xyxy[i].tolist()]

                detections.append({
                    "class_name": class_name,
                    "confidence": round(conf * 100, 2),
                    "confidence_raw": conf,
                    "box": xyxy
                })

                if class_name == 'fractured':
                    has_fracture = True
                    if conf > max_fracture_conf:
                        max_fracture_conf = conf

                if class_name in cls.ANATOMICAL_CLASSES:
                    detected_anatomy.add(cls.ANATOMICAL_CLASSES[class_name])

                if class_name == 'hardware':
                    hardware_detected = True
                    if conf > max_hardware_conf:
                        max_hardware_conf = conf

        # Handle Annotated Image Export
        annotated_filename = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            annotated_img = result.plot() # Returns BGR numpy array
            base_name = os.path.basename(image_path)
            annotated_filename = f"ai_annotated_{base_name}"
            annotated_path = os.path.join(output_dir, annotated_filename)
            cv2.imwrite(annotated_path, annotated_img)

        # Primary Anatomy Description
        anatomy_str = ", ".join(detected_anatomy) if detected_anatomy else "General Skeletal / Unspecified"

        # Generate automated Clinical Impression
        if has_fracture:
            triage_level = "Urgent Orthopedic Review"
            impression = (
                f"POSITIVE FOR FRACTURE: Structural cortical discontinuity identified in {anatomy_str} "
                f"with {max_fracture_conf * 100:.1f}% AI confidence."
            )
            recommendations = [
                f"Urgent orthopedic consult recommended for {anatomy_str}.",
                "Immobilize affected region and obtain secondary orthogonal view if indicated.",
                "Review neurovascular status distally."
            ]
        else:
            triage_level = "Routine"
            impression = f"NEGATIVE FOR ACUTE FRACTURE: No definitive osseous fracture pattern detected in {anatomy_str}."
            recommendations = [
                "Correlate clinically with localized pain, tenderness, or functional deficit.",
                "Consider follow-up imaging in 7-10 days if symptoms persist."
            ]

        if hardware_detected:
            impression += f" Orthopedic hardware / fixation devices visualized ({max_hardware_conf * 100:.1f}% confidence)."
            recommendations.append("Assess alignment and stability of existing orthopedic hardware.")

        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "has_fracture": has_fracture,
            "fracture_confidence": round(max_fracture_conf * 100, 1) if has_fracture else 0.0,
            "anatomy": anatomy_str,
            "hardware_detected": hardware_detected,
            "triage_level": triage_level,
            "detections": detections,
            "total_detections": len(detections),
            "annotated_filename": annotated_filename,
            "clinical_impression": impression,
            "recommendations": recommendations
        }
