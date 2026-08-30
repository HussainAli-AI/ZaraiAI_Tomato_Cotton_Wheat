"""Comprehensive Model Evaluation and Confusion Matrix Generator for ZaraiAI."""
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
from torch.utils.data import DataLoader
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

from src.vision.models import get_crop_classifier
from src.vision.preprocessing import get_transforms, CropDiseaseDataset
from src.config import MODELS_DIR, REPORTS_DIR, PROCESSED_DATA_DIR

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def evaluate_crop_model(crop_name, arch="efficientnet_b0", batch_size=32):
    print(f"\n=======================================================")
    print(f"Running Full Evaluation for {crop_name.upper()} ({arch})")
    
    manifest_file = PROCESSED_DATA_DIR / f"{crop_name}_split_manifest.csv"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Split manifest not found: {manifest_file}")
        
    df = pd.read_csv(manifest_file)
    test_df = df[df["split"] == "test"].copy()
    print(f"Held-out Test Images: {len(test_df)}")
    
    checkpoint_path = MODELS_DIR / f"{crop_name}_{arch}_best.pth"
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Trained checkpoint not found: {checkpoint_path}")
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    class_to_idx = checkpoint.get("class_to_idx")
    classes = [k for k, v in sorted(class_to_idx.items(), key=lambda item: item[1])]
    num_classes = len(classes)
    
    model = get_crop_classifier(model_name=arch, num_classes=num_classes, pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.to(device)
    model.eval()
    
    eval_transform = get_transforms(img_size=224, is_training=False)
    test_dataset = CropDiseaseDataset(test_df, transform=eval_transform, class_to_idx=class_to_idx, base_dir=BASE_DIR)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    all_preds = []
    all_targets = []
    latencies = []
    
    with torch.no_grad():
        for images, targets in test_loader:
            images = images.to(device)
            t0 = time.perf_counter()
            outputs = model(images)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) / images.size(0) * 1000)  # ms per image
            
            preds = torch.argmax(outputs, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_targets.extend(targets.numpy())
            
    # Metrics
    acc = accuracy_score(all_targets, all_preds)
    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(all_targets, all_preds, average="macro", zero_division=0)
    per_class_p, per_class_r, per_class_f1, per_class_support = precision_recall_fscore_support(all_targets, all_preds, average=None, zero_division=0)
    
    cm = confusion_matrix(all_targets, all_preds, labels=list(range(num_classes)))
    avg_latency = float(np.mean(latencies))
    model_size_mb = float(checkpoint_path.stat().st_size / (1024 * 1024))
    
    print(f"\n--- {crop_name.upper()} TEST METRICS ---")
    print(f"Overall Accuracy:  {acc * 100:.2f}%")
    print(f"Macro Precision:   {macro_p:.4f}")
    print(f"Macro Recall:      {macro_r:.4f}")
    print(f"Macro F1 Score:    {macro_f1:.4f}")
    print(f"Avg Inference Latency: {avg_latency:.2f} ms/image")
    print(f"Model Checkpoint Size: {model_size_mb:.2f} MB")
    
    # Save Confusion Matrix Plot
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=classes, yticklabels=classes)
    plt.title(f"Confusion Matrix: {crop_name.capitalize()} Disease Classifier\n(Macro F1: {macro_f1:.4f})")
    plt.xlabel("Predicted Disease")
    plt.ylabel("Ground Truth")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    cm_plot_path = REPORTS_DIR / f"confusion_matrix_{crop_name}.png"
    plt.savefig(cm_plot_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix visualization to {cm_plot_path}")
    
    per_class_metrics = {}
    for i, cls_name in enumerate(classes):
        per_class_metrics[cls_name] = {
            "precision": round(float(per_class_p[i]), 4),
            "recall": round(float(per_class_r[i]), 4),
            "f1_score": round(float(per_class_f1[i]), 4),
            "test_samples": int(per_class_support[i])
        }
        
    eval_result = {
        "crop": crop_name,
        "architecture": arch,
        "test_accuracy": round(float(acc), 4),
        "macro_precision": round(float(macro_p), 4),
        "macro_recall": round(float(macro_r), 4),
        "macro_f1": round(float(macro_f1), 4),
        "average_latency_ms": round(avg_latency, 2),
        "model_size_mb": round(model_size_mb, 2),
        "total_test_samples": len(test_df),
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": cm.tolist()
    }
    
    # Update global metrics report
    metrics_file = REPORTS_DIR / "model_metrics.json"
    existing_metrics = {}
    if metrics_file.exists():
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                existing_metrics = json.load(f)
        except Exception:
            existing_metrics = {}
            
    existing_metrics[crop_name] = eval_result
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(existing_metrics, f, indent=2)
        
    print(f"Updated global model metrics at {metrics_file}")
    return eval_result

def main():
    parser = argparse.ArgumentParser(description="Evaluate crop disease classifiers.")
    parser.add_argument("--crops", nargs="+", default=["cotton", "tomato"], help="Crops to evaluate")
    parser.add_argument("--arch", default="efficientnet_b0", help="Model architecture")
    args = parser.parse_args()
    
    for crop in args.crops:
        try:
            evaluate_crop_model(crop, arch=args.arch)
        except Exception as e:
            print(f"Error evaluating {crop}: {e}")

if __name__ == "__main__":
    main()
