import io
import base64
import os
import numpy as np
import cv2
from PIL import Image
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'dental_unet_model.keras')
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            import tensorflow as tf
            _model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        except ImportError:
            raise RuntimeError("TensorFlow is not installed. Please run: pip install tensorflow")
    return _model

def clean_mask(mask_np):
    """
    Cleans false positives from raw U-Net predictions using border trimming,
    connected component analysis, and morphological filtering.
    """
    h, w = mask_np.shape

    # 1. Zero out outer margins (5% left/right, 3% top/bottom) where dark padding triggers false positives
    margin_x = int(w * 0.05)
    margin_y = int(h * 0.03)
    
    mask_np[:margin_y, :] = 0
    mask_np[h - margin_y:, :] = 0
    mask_np[:, :margin_x] = 0
    mask_np[:, w - margin_x:] = 0

    # 2. Filter connected components (drop large edge blocks and tiny noise)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask_np)
    cleaned_mask = np.zeros_like(mask_np)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        left = stats[i, cv2.CC_STAT_LEFT]
        width = stats[i, cv2.CC_STAT_WIDTH]
        height = stats[i, cv2.CC_STAT_HEIGHT]

        # Ignore tiny noise speckles (< 150 pixels)
        if area < 150:
            continue

        # Ignore large edge artifacts sticking to side margins that span over 35% of total height
        if (left <= margin_x + 10 or (left + width) >= w - margin_x - 10) and height > (h * 0.35):
            continue

        # Retain valid dental detections
        cleaned_mask[labels == i] = 255

    # 3. Smooth mask edges and remove stray pixels via morphological opening
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    cleaned_mask = cv2.morphologyEx(cleaned_mask, cv2.MORPH_OPEN, kernel)

    return cleaned_mask

def predict_segmentation(image_bytes, target_size=(128, 128)):
    """Runs U-Net prediction, applies post-processing cleanup, and returns Base64 masks."""
    # 1. Read original image in RGB mode
    original_img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    orig_w, orig_h = original_img.size

    # 2. Preprocess input tensor (1, 128, 128, 1)
    grayscale_img = original_img.convert('L').resize(target_size)
    img_array = np.array(grayscale_img, dtype=np.float32) / 255.0
    input_tensor = np.expand_dims(img_array, axis=(0, -1))

    # 3. Model Inference
    model = get_model()
    prediction = model.predict(input_tensor)[0]  # Shape: (128, 128, 1)

    # 4. Binarize with a slightly higher confidence threshold (0.60) to drop low-confidence edge noise
    mask_raw = (prediction > 0.60).squeeze().astype(np.uint8) * 255
    
    # Resize raw mask back to full original resolution
    mask_pil_raw = Image.fromarray(mask_raw).resize((orig_w, orig_h), Image.NEAREST)
    mask_np_raw = np.array(mask_pil_raw)

    # 5. Apply post-processing cleanup
    cleaned_mask_np = clean_mask(mask_np_raw)
    mask_pil = Image.fromarray(cleaned_mask_np)
    mask_bool = cleaned_mask_np > 0

    # 6. Apply semi-transparent red overlay onto original image
    orig_np = np.array(original_img)
    overlay_np = orig_np.copy()
    
    highlight_color = np.array([255, 0, 0], dtype=np.uint8)  # Red (R, G, B)
    alpha = 0.4  # 40% red highlight, 60% original image

    overlay_np[mask_bool] = (orig_np[mask_bool] * (1 - alpha) + highlight_color * alpha).astype(np.uint8)
    overlay_img = Image.fromarray(overlay_np)

    # Helper function to encode PIL Image to Base64 PNG
    def to_b64(img_obj):
        buf = io.BytesIO()
        img_obj.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    return {
        "mask": to_b64(mask_pil),
        "overlay": to_b64(overlay_img)
    }