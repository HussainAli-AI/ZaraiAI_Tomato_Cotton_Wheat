"""Image preprocessing and augmentation pipelines for ZaraiAI."""
import torch
from torchvision import transforms
from PIL import Image
from torch.utils.data import Dataset
import pandas as pd
from pathlib import Path

# ImageNet standard statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_transforms(img_size=224, is_training=False):
    """
    Get PyTorch transforms for training or evaluation.
    Augmentations are applied ONLY when is_training=True.
    """
    if is_training:
        return transforms.Compose([
            transforms.Resize((img_size + 32, img_size + 32)),
            transforms.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),
            transforms.RandomRotation(degrees=20),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])
    else:
        return transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
        ])

class CropDiseaseDataset(Dataset):
    """PyTorch Dataset loading images from manifest dataframe."""
    def __init__(self, df, transform=None, class_to_idx=None, base_dir=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
        # Build or use class-to-index mapping
        if class_to_idx is None:
            classes = sorted(self.df["class_name"].unique())
            self.class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        else:
            self.class_to_idx = class_to_idx
            
        self.idx_to_class = {i: cls_name for cls_name, i in self.class_to_idx.items()}
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = Path(row["absolute_path"]) if "absolute_path" in row else self.base_dir / row["relative_path"]
        
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            # Fallback for corrupt image
            image = Image.new("RGB", (224, 224), color=(0, 0, 0))
            
        if self.transform:
            image = self.transform(image)
            
        label_str = row["class_name"]
        label = self.class_to_idx.get(label_str, 0)
        
        return image, label
