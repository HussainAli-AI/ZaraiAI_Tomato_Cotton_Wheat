"""Export curated sample test images from held-out test splits for easy UI testing."""
import shutil
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "sample_test_images"
SAMPLE_DIR.mkdir(exist_ok=True)

manifests = {
    "cotton": BASE_DIR / "data" / "processed" / "cotton_split_manifest.csv",
    "tomato": BASE_DIR / "data" / "processed" / "tomato_split_manifest.csv",
    "wheat": BASE_DIR / "data" / "processed" / "wheat_split_manifest.csv"
}

copied_samples = []

for crop, m_path in manifests.items():
    if not m_path.exists():
        continue
    df = pd.read_csv(m_path)
    test_df = df[df["split"] == "test"]
    crop_dir = SAMPLE_DIR / crop
    crop_dir.mkdir(exist_ok=True)
    
    for cls in sorted(test_df["class_name"].unique()):
        cls_df = test_df[test_df["class_name"] == cls]
        # Pick 2 representative samples per class
        for idx, row in cls_df.head(2).reset_index().iterrows():
            src_path = Path(row["image_path"])
            if src_path.exists():
                safe_cls = cls.replace(" ", "_").replace("Tomato_", "")
                dest_name = f"{safe_cls}_test_{idx+1}{src_path.suffix}"
                dest_path = crop_dir / dest_name
                shutil.copy2(src_path, dest_path)
                copied_samples.append({"crop": crop, "class": cls, "path": str(dest_path)})

print(f"Successfully exported {len(copied_samples)} test samples into {SAMPLE_DIR}")
for s in copied_samples:
    print(f" - [{s['crop'].upper()}] {s['class']} -> {s['path']}")
