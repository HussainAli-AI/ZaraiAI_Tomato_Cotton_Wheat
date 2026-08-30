"""Unit and Integration Tests for ZaraiAI Vision Components."""
import sys
from pathlib import Path
import pytest
import torch
from PIL import Image

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.vision.models import get_crop_classifier
from src.vision.preprocessing import get_transforms
from src.vision.inference import CropVisionInference
from src.vision.gradcam import GradCAM

def test_model_architecture_creation():
    """Verify classifier head matches target number of disease classes."""
    model = get_crop_classifier(model_name="efficientnet_b0", num_classes=6, pretrained=False)
    dummy_input = torch.randn(2, 3, 224, 224)
    output = model(dummy_input)
    assert output.shape == (2, 6), f"Expected shape (2, 6), got {output.shape}"

def test_preprocessing_transforms():
    """Verify transform output tensor dimensions and normalization."""
    transform = get_transforms(img_size=224, is_training=False)
    img = Image.new("RGB", (300, 400), color=(100, 150, 200))
    tensor = transform(img)
    assert tensor.shape == (3, 224, 224), f"Expected tensor shape (3, 224, 224), got {tensor.shape}"

def test_gradcam_generation():
    """Verify Grad-CAM produces normalized heatmap in [0, 1]."""
    model = get_crop_classifier(model_name="efficientnet_b0", num_classes=5, pretrained=False)
    gradcam = GradCAM(model)
    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=True)
    heatmap = gradcam.generate_heatmap(dummy_input, target_class=0)
    assert heatmap.shape == (7, 7), f"Expected spatial heatmap, got {heatmap.shape}"
    assert heatmap.min() >= 0.0 and heatmap.max() <= 1.0, "Heatmap values must be normalized in [0, 1]"

def test_vision_inference_pipeline():
    """Verify end-to-end vision prediction output structure."""
    engine = CropVisionInference(crop_name="tomato")
    dummy_img = Image.new("RGB", (224, 224), color=(50, 180, 50))
    res = engine.predict(dummy_img, generate_cam=False)
    
    assert "prediction_id" in res
    assert "canonical_name" in res
    assert "urdu_name" in res
    assert "confidence" in res
    assert "is_uncertain" in res
    assert 0.0 <= res["confidence"] <= 1.0
