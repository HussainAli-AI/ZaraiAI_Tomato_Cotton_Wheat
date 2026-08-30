# ZaraiAI: Comprehensive Dataset Audit & Integrity Report

## 1. Executive Summary & Quality Gates

This audit establishes the benchmark dataset integrity for ZaraiAI (Tomato, Cotton, Wheat) prior to model training.
In accordance with our strict scientific integrity rules:
- All candidate datasets have verified DOIs, author provenance, and CC BY 4.0 licenses.
- Images are validated for file readability, corruptions, and exact SHA256 duplicates.
- **Zero Data Leakage:** Splits are performed strictly on original deduplicated images. No augmented variants cross train/val/test boundaries.

## 2. Dataset Quality Audit Table

| Crop | Source / Dataset | DOI | License | Total Raw Images | Valid Images | Corrupt Files | Exact Duplicates | Unique Images | Train Count (70%) | Val Count (15%) | Test Count (15%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Wheat** | Disease Dataset of Wheat (Original Field) | `10.17632/5gc7hwydwg.1` | CC BY 4.0 | 1603 | 1603 | 0 | 128 | 1475 | 1032 | 221 | 222 |
| **Cotton** | Cotton Leaf Image Dataset for Disease Classification (Original) | `10.17632/t9hgvk2h9p.1` | CC BY 4.0 | 1373 | 1373 | 0 | 224 | 1149 | 804 | 172 | 173 |
| **Tomato** | Tomato Leaf Disease Classification Dataset in Pakistan (Raw Field) | `10.17632/3mbnb82mxd.2` | CC BY 4.0 | 830 | 830 | 0 | 42 | 788 | 551 | 118 | 119 |

## 3. Class Distributions & Imbalance Analysis

### Wheat Class Distribution (Disease Dataset of Wheat (Original Field))

| Class Label | Total Count | Train | Val | Test | Imbalance Ratio |
|---|---|---|---|---|---|
| `LeafBlight` | 364 | 255 | 54 | 55 | 1:1.00 |
| `WheatBlast` | 310 | 217 | 46 | 47 | 1:1.17 |
| `BlackPoint` | 303 | 212 | 45 | 46 | 1:1.20 |
| `HealthyLeaf` | 250 | 175 | 38 | 37 | 1:1.46 |
| `FusariumFootRot` | 248 | 173 | 38 | 37 | 1:1.47 |

### Cotton Class Distribution (Cotton Leaf Image Dataset for Disease Classification (Original))

| Class Label | Total Count | Train | Val | Test | Imbalance Ratio |
|---|---|---|---|---|---|
| `Fusarium Wilt` | 316 | 221 | 47 | 48 | 1:1.00 |
| `Verticillium Wilt` | 291 | 204 | 43 | 44 | 1:1.09 |
| `Bacterial Blight` | 195 | 136 | 30 | 29 | 1:1.62 |
| `Healthy Leaf` | 174 | 122 | 26 | 26 | 1:1.82 |
| `Alternaria Leaf Spot` | 173 | 121 | 26 | 26 | 1:1.83 |

### Tomato Class Distribution (Tomato Leaf Disease Classification Dataset in Pakistan (Raw Field))

| Class Label | Total Count | Train | Val | Test | Imbalance Ratio |
|---|---|---|---|---|---|
| `Tomato_mold_leaf` | 185 | 129 | 28 | 28 | 1:1.00 |
| `Tomato_Septoria_leaf_spot` | 172 | 120 | 26 | 26 | 1:1.08 |
| `Tomato_Healthy_leaf` | 132 | 92 | 20 | 20 | 1:1.40 |
| `Tomato_Early_blight_leaf` | 115 | 81 | 17 | 17 | 1:1.61 |
| `Tomato_leaf_late_blight` | 104 | 73 | 15 | 16 | 1:1.78 |
| `Tomato_leaf_yellow_curl_virus` | 80 | 56 | 12 | 12 | 1:2.31 |

## 4. Verification of Anti-Leakage Protocol

> [!IMPORTANT]
> Every split was validated via intersection of SHA256 content hashes between partitions:
> - `Hash(Train) ∩ Hash(Val) = ∅` (Zero overlap)
> - `Hash(Train) ∩ Hash(Test) = ∅` (Zero overlap)
> - `Hash(Val) ∩ Hash(Test) = ∅` (Zero overlap)
> All augmentation is strictly confined to the dynamic training DataLoader.
