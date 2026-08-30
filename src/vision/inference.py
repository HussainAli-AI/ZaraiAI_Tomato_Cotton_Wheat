"""Vision Inference Engine with Confidence Calibration and Explainability for ZaraiAI."""
import os
import torch
import torch.nn.functional as F
from PIL import Image
from pathlib import Path
import json

from src.vision.models import get_crop_classifier
from src.vision.preprocessing import get_transforms
from src.vision.gradcam import GradCAM
from src.config import TAXONOMY, MODELS_DIR

class CropVisionInference:
    """Inference engine for crop disease diagnosis with Grad-CAM and uncertainty handling."""
    def __init__(self, crop_name, model_path=None, model_arch="efficientnet_b0", device=None, confidence_threshold=0.65):
        self.crop_name = crop_name.lower()
        self.model_arch = model_arch
        self.confidence_threshold = confidence_threshold
        
        # Load crop taxonomy
        crop_data = TAXONOMY.get(self.crop_name, {})
        self.classes_info = crop_data.get("classes", [])
        self.class_ids = [c["id"] for c in self.classes_info]
        
        # Setup device (prefer CUDA if available, fallback to CPU)
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
            
        if model_path is None:
            model_path = MODELS_DIR / f"{self.crop_name}_{self.model_arch}_best.pth"
            
        self.model_path = Path(model_path)
        
        # Checkpoint inspection for dynamic num_classes
        checkpoint = None
        checkpoint_state = None
        checkpoint_class_to_idx = None
        
        if self.model_path.exists():
            checkpoint = torch.load(self.model_path, map_location=self.device)
            if isinstance(checkpoint, dict):
                checkpoint_state = checkpoint.get("state_dict", checkpoint)
                checkpoint_class_to_idx = checkpoint.get("class_to_idx")
            else:
                checkpoint_state = checkpoint
                
        # Determine num_classes from checkpoint or taxonomy
        if checkpoint_state is not None:
            for k in ["classifier.4.weight", "classifier.1.weight", "fc.weight", "head.fc.weight"]:
                if k in checkpoint_state:
                    self.num_classes = checkpoint_state[k].shape[0]
                    break
            else:
                if checkpoint_class_to_idx is not None:
                    self.num_classes = len(checkpoint_class_to_idx)
                else:
                    self.num_classes = len(self.class_ids)
        else:
            self.num_classes = len(self.class_ids)
            
        # Model initialization with detected num_classes
        self.model = get_crop_classifier(model_name=self.model_arch, num_classes=self.num_classes, pretrained=False)
        
        if checkpoint_state is not None:
            self.model.load_state_dict(checkpoint_state)
            print(f"Loaded {self.crop_name.upper()} model checkpoint ({self.num_classes} classes) from {self.model_path}")
            if checkpoint_class_to_idx:
                self.class_to_idx = checkpoint_class_to_idx
            else:
                self.class_to_idx = {cid: i for i, cid in enumerate(self.class_ids[:self.num_classes])}
        else:
            print(f"[NOTE] Checkpoint not found at {self.model_path}. Using initialized architecture.")
            self.class_to_idx = {cid: i for i, cid in enumerate(self.class_ids[:self.num_classes])}
            
        # Invert index mapping and resolve taxonomy metadata
        self.idx_to_class = {i: raw_name for raw_name, i in self.class_to_idx.items()}
        self.idx_to_meta = {}
        for idx, raw_name in self.idx_to_class.items():
            self.idx_to_meta[idx] = self._resolve_class_meta(raw_name)
            
        self.model.to(self.device)
        self.model.eval()
        
        # Transforms and Grad-CAM
        self.transform = get_transforms(img_size=224, is_training=False)
        self.gradcam = GradCAM(self.model)
        
    def _resolve_class_meta(self, raw_name: str) -> dict:
        """Resolve raw dataset class name to canonical taxonomy entry."""
        raw_clean = raw_name.lower().replace("_", " ").strip()
        raw_compact = raw_name.lower().replace("_", "").replace(" ", "").strip()
        
        for c in self.classes_info:
            c_id = c["id"].lower()
            c_id_compact = c_id.replace("_", "")
            c_name = c["canonical_name"].lower()
            labels = [str(l).lower() for l in c.get("dataset_labels", [])]
            
            if c["id"] == raw_name or raw_name in c.get("dataset_labels", []):
                return c
            if raw_clean in labels or raw_name.lower() in labels:
                return c
            if c_id_compact in raw_compact or raw_compact in c_id_compact:
                return c
            if raw_clean in c_name or c_name in raw_clean:
                return c
                
        # Fallback metadata if not in taxonomy
        return {
            "id": raw_name.lower().replace(" ", "_"),
            "canonical_name": raw_name.replace("_", " ").title(),
            "urdu_name": raw_name,
            "roman_urdu_name": raw_name,
            "pathogen": None,
            "disease_type": "unknown"
        }

    def predict(self, image_input, generate_cam=True):
        """
        Run disease inference on an image (PIL Image or path).
        
        Returns structured dictionary with:
        - prediction_id
        - canonical_name
        - urdu_name
        - roman_urdu_name
        - confidence
        - is_uncertain
        - all_probabilities
        - gradcam_image (PIL Image or None)
        """
        if isinstance(image_input, (str, Path)):
            pil_img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            pil_img = image_input.convert("RGB")
        else:
            raise ValueError("image_input must be a file path or PIL Image object.")
            
        tensor_img = self.transform(pil_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(tensor_img)
            probabilities = F.softmax(logits, dim=1).squeeze().cpu().numpy()
            
        # Handle 1D array vs scalar for edge cases
        if probabilities.ndim == 0:
            probabilities = probabilities.reshape(1)
            
        top_idx = int(probabilities.argmax())
        top_prob = float(probabilities[top_idx])
        
        class_meta = self.idx_to_meta.get(top_idx, self._resolve_class_meta(self.idx_to_class.get(top_idx, "unknown")))
        predicted_class_id = class_meta.get("id", f"class_{top_idx}")
        
        is_uncertain = top_prob < self.confidence_threshold
        
        all_probs_dict = {
            self.idx_to_meta.get(i, {}).get("canonical_name", self.idx_to_class.get(i, f"class_{i}")): float(probabilities[i])
            for i in range(len(probabilities))
        }
        
        cam_image = None
        if generate_cam:
            try:
                with torch.enable_grad():
                    tensor_grad = tensor_img.clone().detach().requires_grad_(True)
                    heatmap = self.gradcam.generate_heatmap(tensor_grad, target_class=top_idx)
                    cam_image = self.gradcam.overlay_heatmap(pil_img, heatmap)
            except Exception as e:
                print(f"Warning: Grad-CAM generation failed: {e}")
                cam_image = None
                
        return {
            "crop": self.crop_name,
            "prediction_id": predicted_class_id,
            "canonical_name": class_meta["canonical_name"],
            "urdu_name": class_meta["urdu_name"],
            "roman_urdu_name": class_meta["roman_urdu_name"],
            "pathogen": class_meta.get("pathogen"),
            "disease_type": class_meta.get("disease_type", "unknown"),
            "confidence": round(top_prob, 4),
            "confidence_score": round(top_prob, 4),
            "confidence_percentage": f"{top_prob * 100:.1f}%",
            "is_uncertain": is_uncertain,
            "all_probabilities": all_probs_dict,
            "gradcam_image": cam_image,
            "original_image": pil_img
        }
