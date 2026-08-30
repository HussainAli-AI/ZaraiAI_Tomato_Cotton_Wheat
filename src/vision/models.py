"""Computer Vision model architectures for ZaraiAI (EfficientNet-B0 and MobileNetV3-Large)."""
import torch
import torch.nn as nn
from torchvision import models

def get_crop_classifier(model_name="efficientnet_b0", num_classes=6, pretrained=True, freeze_backbone=False):
    """
    Build a transfer-learning classifier for crop disease identification.
    
    Args:
        model_name (str): 'efficientnet_b0' or 'mobilenet_v3_large'
        num_classes (int): Number of target disease classes for the specific crop
        pretrained (bool): Whether to load ImageNet pretrained weights
        freeze_backbone (bool): Whether to freeze feature extractor layers initially
    """
    model_name = model_name.lower()
    
    if "efficientnet" in model_name:
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        
        if freeze_backbone:
            for param in model.features.parameters():
                param.requires_grad = False
                
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(p=0.3, inplace=True),
            nn.Linear(in_features, 256),
            nn.SiLU(),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(256, num_classes)
        )
        model.target_layer = model.features[-1]  # Target layer for Grad-CAM
        
    elif "mobilenet" in model_name:
        weights = models.MobileNet_V3_Large_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_large(weights=weights)
        
        if freeze_backbone:
            for param in model.features.parameters():
                param.requires_grad = False
                
        in_features = model.classifier[0].in_features
        model.classifier = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.2, inplace=True),
            nn.Linear(256, num_classes)
        )
        model.target_layer = model.features[-1]  # Target layer for Grad-CAM
        
    else:
        raise ValueError(f"Unsupported model architecture: {model_name}. Use 'efficientnet_b0' or 'mobilenet_v3_large'.")
        
    return model
