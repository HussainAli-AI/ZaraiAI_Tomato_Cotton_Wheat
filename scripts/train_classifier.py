"""Production Training Pipeline for Crop Disease Classifiers in ZaraiAI."""
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import argparse
import json
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import ReduceLROnPlateau
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from src.vision.models import get_crop_classifier
from src.vision.preprocessing import get_transforms, CropDiseaseDataset
from src.config import MODELS_DIR, REPORTS_DIR, PROCESSED_DATA_DIR, TAXONOMY

def set_seed(seed=42):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.deterministic = True

def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    all_preds = []
    all_targets = []
    
    for images, targets in dataloader:
        images = images.to(device)
        targets = targets.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
        preds = torch.argmax(outputs, dim=1).detach().cpu().numpy()
        all_preds.extend(preds)
        all_targets.extend(targets.cpu().numpy())
        
    epoch_loss = running_loss / len(dataloader.dataset)
    acc = accuracy_score(all_targets, all_preds)
    p, r, f1, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)
    
    return epoch_loss, acc, f1

def evaluate(model, dataloader, criterion, device):
    model.eval()
    running_loss = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for images, targets in dataloader:
            images = images.to(device)
            targets = targets.to(device)
            
            outputs = model(images)
            loss = criterion(outputs, targets)
            
            running_loss += loss.item() * images.size(0)
            preds = torch.argmax(outputs, dim=1).detach().cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.cpu().numpy())
            
    epoch_loss = running_loss / len(dataloader.dataset)
    acc = accuracy_score(all_targets, all_preds)
    p, r, f1, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)
    
    return epoch_loss, acc, f1, all_preds, all_targets

def run_training(crop_name, arch="efficientnet_b0", epochs=15, batch_size=32, lr=1e-4, seed=42):
    set_seed(seed)
    print(f"\n=======================================================")
    print(f"Starting Training for {crop_name.upper()} ({arch})")
    print(f"Epochs: {epochs} | Batch Size: {batch_size} | Learning Rate: {lr}")
    
    manifest_file = PROCESSED_DATA_DIR / f"{crop_name}_split_manifest.csv"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Split manifest not found: {manifest_file}. Run scripts/audit_datasets.py first.")
        
    df = pd.read_csv(manifest_file)
    train_df = df[df["split"] == "train"].copy()
    val_df = df[df["split"] == "val"].copy()
    test_df = df[df["split"] == "test"].copy()
    
    print(f"Dataset split sizes -> Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")
    
    # Class mapping
    classes = sorted(df["class_name"].unique())
    class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
    num_classes = len(classes)
    print(f"Number of classes: {num_classes} -> {classes}")
    
    # Compute class weights for imbalanced classes
    class_counts = train_df["class_name"].value_counts()
    total_train = len(train_df)
    weights = [total_train / (num_classes * class_counts[cls]) for cls in classes]
    class_weights_tensor = torch.tensor(weights, dtype=torch.float32)
    
    # Datasets and Loaders
    train_transform = get_transforms(img_size=224, is_training=True)
    eval_transform = get_transforms(img_size=224, is_training=False)
    
    train_dataset = CropDiseaseDataset(train_df, transform=train_transform, class_to_idx=class_to_idx, base_dir=BASE_DIR)
    val_dataset = CropDiseaseDataset(val_df, transform=eval_transform, class_to_idx=class_to_idx, base_dir=BASE_DIR)
    test_dataset = CropDiseaseDataset(test_df, transform=eval_transform, class_to_idx=class_to_idx, base_dir=BASE_DIR)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Execution Device: {device}")
    
    model = get_crop_classifier(model_name=arch, num_classes=num_classes, pretrained=True)
    model.to(device)
    class_weights_tensor = class_weights_tensor.to(device)
    
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)
    
    best_val_f1 = 0.0
    best_checkpoint_path = MODELS_DIR / f"{crop_name}_{arch}_best.pth"
    history = {"train_loss": [], "train_f1": [], "val_loss": [], "val_f1": [], "val_acc": []}
    
    for epoch in range(1, epochs + 1):
        start_time = time.time()
        tr_loss, tr_acc, tr_f1 = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_f1, _, _ = evaluate(model, val_loader, criterion, device)
        
        scheduler.step(val_f1)
        elapsed = time.time() - start_time
        
        history["train_loss"].append(round(tr_loss, 4))
        history["train_f1"].append(round(tr_f1, 4))
        history["val_loss"].append(round(val_loss, 4))
        history["val_f1"].append(round(val_f1, 4))
        history["val_acc"].append(round(val_acc, 4))
        
        print(f"Epoch [{epoch:02d}/{epochs:02d}] ({elapsed:.1f}s) | Train Loss: {tr_loss:.4f} F1: {tr_f1:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} F1: {val_f1:.4f}")
        
        # Save best model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            torch.save({
                "epoch": epoch,
                "arch": arch,
                "crop": crop_name,
                "state_dict": model.state_dict(),
                "class_to_idx": class_to_idx,
                "val_f1": val_f1,
                "val_acc": val_acc
            }, best_checkpoint_path)
            print(f"  --> Saved new best checkpoint to {best_checkpoint_path} (Val F1: {val_f1:.4f})")
            
    # Final Test Set Evaluation
    print("\n--- Evaluating Best Model on Held-Out Test Set ---")
    best_chk = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(best_chk["state_dict"])
    
    test_loss, test_acc, test_f1, test_preds, test_targets = evaluate(model, test_loader, criterion, device)
    print(f"Test Set Results -> Loss: {test_loss:.4f} | Accuracy: {test_acc:.4f} | Macro F1: {test_f1:.4f}")
    
    # Save metrics report
    report_file = REPORTS_DIR / f"{crop_name}_{arch}_metrics.json"
    metrics_summary = {
        "crop": crop_name,
        "arch": arch,
        "num_classes": num_classes,
        "classes": classes,
        "best_val_f1": round(best_val_f1, 4),
        "test_accuracy": round(test_acc, 4),
        "test_macro_f1": round(test_f1, 4),
        "history": history
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"Saved metrics summary to {report_file}")
    
    return metrics_summary

def main():
    parser = argparse.ArgumentParser(description="Train crop disease classifier for ZaraiAI.")
    parser.add_argument("--crop", required=True, choices=["tomato", "cotton", "wheat"], help="Crop to train")
    parser.add_argument("--arch", default="efficientnet_b0", choices=["efficientnet_b0", "mobilenet_v3_large"], help="Backbone architecture")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    args = parser.parse_args()
    
    run_training(crop_name=args.crop, arch=args.arch, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)

if __name__ == "__main__":
    main()
