"""Reproducible Dataset Downloader and Integrity Verifier for ZaraiAI."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
MANIFEST_PATH = DATA_DIR / "dataset_manifest.csv"

DATASET_SPECS = {
    "tomato": [
        {
            "dataset_id": "tomato_pakistan",
            "crop": "Tomato",
            "name": "Tomato Leaf Disease Classification Dataset in Pakistan",
            "doi": "10.17632/3mbnb82mxd.2",
            "country": "Pakistan",
            "field_controlled": "Real field (smartphones)",
            "expected_images": 7200,
            "classes": "Early Blight, Late Blight, Septoria Leaf Spot, Leaf Mold, Yellow Leaf Curl Virus, Healthy",
            "license": "CC BY 4.0",
            "sha256": "2a2b36a8f972337f6d0e95e436835e55ffee5291fa07277157b40f0441f42f50",
            "filename": "Tomato_Leaf_Disease_Dataset_Pakistan.zip",
            "download_url": "https://data.mendeley.com/public-files/datasets/3mbnb82mxd/files/4844fda3-b66b-4b2a-bd83-775c0da974ea/file_downloaded",
            "recommended_role": "Train / Val / Test (In-Domain)"
        }
    ],
    "cotton": [
        {
            "dataset_id": "cotton_original",
            "crop": "Cotton",
            "name": "Cotton Leaf Image Dataset for Disease Classification (Original)",
            "doi": "10.17632/t9hgvk2h9p.1",
            "country": "Regional Fields",
            "field_controlled": "Real field",
            "expected_images": 1373,
            "classes": "Alternaria Leaf Spot, Bacterial Blight, Fusarium Wilt, Verticillium Wilt, Healthy Leaf",
            "license": "CC BY 4.0",
            "sha256": "f1c666c029d7284e86f79597154bfb5270efd79d4fd352a7b2803ccdd1bbc4c3",
            "filename": "Cotton_Original_Dataset.zip",
            "download_url": "https://data.mendeley.com/public-files/datasets/t9hgvk2h9p/files/a3bc3269-5c19-4394-824b-50be764a27c4/file_downloaded",
            "recommended_role": "Train / Val / Test (In-Domain)"
        }
    ],
    "wheat": [
        {
            "dataset_id": "wheat_disease_main",
            "crop": "Wheat",
            "name": "Disease Dataset of Wheat: Original, Augmented, and Balanced",
            "doi": "10.17632/5gc7hwydwg.1",
            "country": "Bangladesh",
            "field_controlled": "Real field",
            "expected_images": 1603,
            "classes": "Black Point, Fusarium Foot Rot, Healthy Leaf, Leaf Blight, Wheat Blast",
            "license": "CC BY 4.0",
            "sha256": "bb21be5d9dbfb9a543231fb9e3882901248b8c9cd3201a98169eb364e9278196",
            "filename": "Wheat_Disease.zip",
            "download_url": "https://data.mendeley.com/public-files/datasets/5gc7hwydwg/files/5c163bc0-311f-4b10-bd09-d5cb949237cc/file_downloaded",
            "recommended_role": "Train / Val / Test (In-Domain)"
        }
    ]
}

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url, target_path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading from {url} to {target_path} ...")
    cmd = ["curl.exe", "-L", "-C", "-", "--retry", "3", url, "-o", str(target_path)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"Download failed with exit code {result.returncode}")
    print(f"Download completed: {target_path.stat().st_size / (1024*1024):.2f} MB")

def extract_archive(archive_path, extract_to):
    extract_to.mkdir(parents=True, exist_ok=True)
    print(f"Extracting {archive_path.name} to {extract_to} ...")
    if archive_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extraction successful: {extract_to}")
    else:
        print(f"Unsupported archive format for automatic extraction: {archive_path.suffix}")

def update_manifest(records):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)
    if MANIFEST_PATH.exists():
        existing_df = pd.read_csv(MANIFEST_PATH)
        combined = pd.concat([existing_df, df]).drop_duplicates(subset=["dataset_id"], keep="last")
        combined.to_csv(MANIFEST_PATH, index=False)
    else:
        df.to_csv(MANIFEST_PATH, index=False)
    print(f"Updated dataset manifest at {MANIFEST_PATH}")

def main():
    parser = argparse.ArgumentParser(description="Download and verify crop disease datasets for ZaraiAI.")
    parser.add_argument("--crop", choices=["tomato", "wheat", "cotton", "all"], default="all", help="Crop to download")
    parser.add_argument("--no-extract", action="store_true", help="Skip extraction after download")
    args = parser.parse_args()

    crops_to_process = ["tomato", "cotton", "wheat"] if args.crop == "all" else [args.crop]
    manifest_records = []

    for crop in crops_to_process:
        specs = DATASET_SPECS.get(crop, [])
        for spec in specs:
            print(f"\n=======================================================")
            print(f"Processing {spec['crop']} Dataset: {spec['name']}")
            target_zip = RAW_DIR / spec["filename"]
            extract_dir = RAW_DIR / crop / spec["dataset_id"]

            # Download if missing or incomplete
            if not target_zip.exists() or (target_zip.stat().st_size == 0):
                download_file(spec["download_url"], target_zip)
            else:
                print(f"Archive already exists locally: {target_zip}")

            # Verify SHA256
            print(f"Calculating SHA256 checksum for {target_zip.name} ...")
            actual_hash = calculate_sha256(target_zip)
            expected_hash = spec["sha256"]
            
            if actual_hash.lower() == expected_hash.lower():
                print(f"[VERIFIED] SHA256 matches: {actual_hash}")
                verified = True
            else:
                print(f"[WARNING] SHA256 mismatch! Expected: {expected_hash}, Got: {actual_hash}")
                verified = False

            # Extract
            if not args.no_extract:
                if not extract_dir.exists() or not any(extract_dir.iterdir()):
                    extract_archive(target_zip, extract_dir)
                else:
                    print(f"Extracted folder already exists: {extract_dir}")

            # Count extracted files
            extracted_count = len(list(extract_dir.rglob("*.jpg")) + list(extract_dir.rglob("*.JPG")) + list(extract_dir.rglob("*.png")) + list(extract_dir.rglob("*.jpeg")))

            manifest_records.append({
                "dataset_id": spec["dataset_id"],
                "crop": spec["crop"],
                "name": spec["name"],
                "doi": spec["doi"],
                "country": spec["country"],
                "field_controlled": spec["field_controlled"],
                "expected_images": spec["expected_images"],
                "extracted_images": extracted_count,
                "classes": spec["classes"],
                "license": spec["license"],
                "local_archive": str(target_zip.relative_to(BASE_DIR)),
                "extracted_dir": str(extract_dir.relative_to(BASE_DIR)),
                "sha256": actual_hash,
                "sha256_verified": verified,
                "recommended_role": spec["recommended_role"]
            })

    if manifest_records:
        update_manifest(manifest_records)

if __name__ == "__main__":
    main()
