import os
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
import timm

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def get_weights_path():
    # Priority 1: Relative to this file location
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_path = os.path.join(base_dir, "models", "weights", "efficientnet_b0_melanoma.pth")
    if os.path.exists(target_path):
        return target_path
    
    # Priority 2: Relative to CWD
    cwd_path = os.path.join("models", "weights", "efficientnet_b0_melanoma.pth")
    if os.path.exists(cwd_path):
        return cwd_path
        
    alt_path = os.path.join("models", "efficientnet_b0_melanoma.pth")
    if os.path.exists(alt_path):
        return alt_path

    return target_path

# 1. Load Architecture and Trained Weights
def load_model(weights_path=None):
    if weights_path is None:
        weights_path = get_weights_path()
        
    model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=device))
    model.to(device)
    model.eval()
    return model

MODEL = None

def get_model():
    global MODEL
    if MODEL is None:
        MODEL = load_model()
    return MODEL

CLASS_NAMES = ["Nevus", "Malignant Melanoma"]

# 2. Image Preprocessing Pipeline
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 3. Inference Function
def predict_lesion(image_bytes):
    model = get_model()
    image = Image.open(image_bytes).convert("RGB")
    tensor = transform(image).unsqueeze(0).to(device)
    
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.softmax(outputs, dim=1)[0]
        confidence, predicted_idx = torch.max(probabilities, 0)
        
    return {
        "label": CLASS_NAMES[predicted_idx.item()],
        "confidence": round(confidence.item() * 100, 2)
    }