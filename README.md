# 🌱 ZaraiAI (زرعی اے آئی)
### *AI-Powered Crop Intelligence for Every Farmer*

[![Live Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://zaraiaitomatocottonwheat-sgmc3ltf5d8j8bujbrbd6b.streamlit.app/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Hackathon Track](https://img.shields.io/badge/Hackathon-Smart_Agriculture_(Pakistan)-2E7D32.svg)]()
[![Model](https://img.shields.io/badge/Vision_Backbone-EfficientNet--B0-blue.svg)]()
[![RAG](https://img.shields.io/badge/RAG-Grounded_Extension_Science-green.svg)]()
[![LLM](https://img.shields.io/badge/LLM-Qwen3.7--Plus_(Alibaba_Cloud)-orange.svg)]()

---

## 🌾 1. Overview & Problem Statement

Over 65% of Pakistan's population depends directly or indirectly on agriculture. Yet smallholder farmers face staggering post-harvest losses and reduced yields (>30%) due to unmanaged leaf blights, rusts, and whitefly viral epidemics across major staple and cash crops: **Tomato, Wheat, and Cotton**.

Existing diagnostic tools provide simple, ungrounded classification labels without practical agricultural decision support. **ZaraiAI** bridges this gap by combining:
1. **Computer Vision Disease Diagnosis:** Crop-specialized transfer learning classifiers with **Grad-CAM** visual explainability.
2. **Authoritative Pakistani Agricultural RAG:** Integrated Pest Management (IPM) guidance grounded strictly in verified Tier-1 extension publications from the **Government of Punjab Agriculture Department**, **AARI Faisalabad**, **CCRI Multan**, **NARC Islamabad**, and **CABI PlantwisePlus Pakistan**.
3. **Localized Weather Intelligence:** Real-time spray safety condition evaluation via Open-Meteo across Pakistani agricultural districts.
4. **Multilingual Interaction:** Native support for **English**, **Urdu (`اردو`)**, and **Roman Urdu**.

---

## 🎯 2. Target Crops & Verified Disease Taxonomy

ZaraiAI strictly specializes in three core Pakistani crops:

### 🍅 Tomato (`Solanum lycopersicum`)
- `Healthy Tomato Leaf` (صحت مند ٹماٹر)
- `Early Blight` (*Alternaria solani*) (ابتدائی جھلسائو)
- `Late Blight` (*Phytophthora infestans*) (پچھیتا جھلسائو)
- `Septoria Leaf Spot` (*Septoria lycopersici*) (سیپٹوریا پتوں کے دھبے)
- `Leaf Mold` (*Passalora fulva*) (پتوں کی پھپھوندی)
- `Yellow Leaf Curl Virus (TYLCV)` (ٹماٹر کے پتوں کا مڑنا اور زردی وائرس)

### 🌿 Cotton (`Gossypium hirsutum`)
- `Healthy Cotton` (صحت مند کپاس)
- `Alternaria Leaf Spot` (*Alternaria macrospora*) (الٹرنیریا پتوں کے دھبے)
- `Bacterial Blight / Black Arm` (*Xanthomonas citri pv. malvacearum*) (بیکٹیریل بلائٹ اور بلیک آرم)
- `Fusarium Wilt / Ukhera` (*Fusarium oxysporum f. sp. vasinfectum*) (فیوزریئم مرجھائو / اُکھیڑا)
- `Verticillium Wilt` (*Verticillium dahliae*) (ورٹیسیلیم مرجھائو)
- `Cotton Leaf Curl Virus (CLCuV)` (*Begomovirus*) (کپاس کے پتوں کا مروڑ وائرس)

### 🌾 Wheat (`Triticum aestivum`)
- `Healthy Wheat` (صحت مند گندم)
- `Stripe / Yellow Rust` (*Puccinia striiformis f. sp. tritici*) (زرد کنگی / سٹرائپ رسٹ)
- `Black Point` (*Bipolaris sorokiniana*) (بلیک پوائنٹ)
- `Fusarium Foot / Crown Rot` (*Fusarium culmorum*) (فیوزریئم جڑ اور تنے کا گلنا)
- `Leaf Blight / Spot Blotch` (*Bipolaris sorokiniana*) (پتوں کا جھلسائو)
- `Wheat Blast` (*Magnaporthe oryzae Triticum*) (گندم کا بلاسٹ)

---

## 🔬 3. Scientific Integrity & Anti-Leakage Protocol

In strict adherence to scientific rigor:
- **No Augmented Leakage:** Model splitting is performed **strictly on unique original field images** using exact SHA256 content deduplication prior to partitioning into 70% Train, 15% Validation, and 15% Test.
- **Zero Partition Overlap:** Verified `Hash(Train) ∩ Hash(Val) = ∅` and `Hash(Train) ∩ Hash(Test) = ∅`.
- **Zero Ungrounded Chemicals:** All chemical suggestions cite active ingredients, approved dosages, and Pre-Harvest Intervals (PHI) from retrieved Tier-1 publications.

---

## 🏗️ 4. System Architecture

```
User Input (Image + Query + District)
  ↓
Crop Vision Engine (EfficientNet-B0 + Grad-CAM)
  ↓
Confidence Threshold Check (< 0.65 triggers warning)
  ↓
RAG Knowledge Retrieval (Crop-filtered vector store)
  ↓
Open-Meteo Weather Advisor (Rain/Wind/Temp spray safety)
  ↓
LLM Grounded Synthesis (Qwen3.7-Plus via Alibaba Cloud)
  ↓
Safety & Anti-Hallucination Guardrail
  ↓
Multilingual Farmer Response (Action Plan + Citations)
```

---

## 🚀 5. Getting Started & Installation

### Prerequisites
- Python 3.10+ (PyTorch, Torchvision, Streamlit, Scikit-Learn)
- Git & Curl

### Local Setup
```bash
# Clone the repository
git clone https://github.com/HussainAli-AI/ZaraiAI_Tomato_Cotton_Wheat.git
cd ZaraiAI_Tomato_Cotton_Wheat

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env to add your ALIBABA_API_KEY (optional for full Qwen3.7-Plus live reasoning)

# Stage Knowledge Base & Build RAG Index
python scripts/download_kb.py
python scripts/ingest_kb.py

# Run Automated Test Suite
python -m pytest tests/ -v

# Launch ZaraiAI Streamlit Web App
streamlit run app/streamlit_app.py
```

---

## 🐳 6. Docker Deployment

```bash
# Build Docker image
docker build -t zarai-ai:latest .

# Run containerized application
docker run -p 8501:8501 --env-file .env zarai-ai:latest
```

---

## 📊 7. Dataset Manifest & References

| Crop | Dataset Title | DOI / Reference | License | Country |
|---|---|---|---|---|
| **Tomato** | Tomato Leaf Disease Classification Dataset in Pakistan | `10.17632/3mbnb82mxd.2` | CC BY 4.0 | Pakistan (Field) |
| **Cotton** | Cotton Leaf Image Dataset for Disease Classification | `10.17632/t9hgvk2h9p.1` | CC BY 4.0 | Regional Fields |
| **Wheat** | Disease Dataset of Wheat: Original, Augmented, and Balanced | `10.17632/5gc7hwydwg.1` | CC BY 4.0 | Field Crops |

---

## ⚠️ 8. Agricultural Safety Disclaimer

ZaraiAI is an AI decision-support assistant designed to empower farmers with timely diagnostic hypotheses and authoritative extension guidance. Because field conditions and local pathogen biotypes vary, farmers should cross-verify pesticide applications with local agricultural extension officers and always adhere to official manufacturer product labels.
