# ZaraiAI: 3-Minute Live Hackathon Demo Script

**Target Track:** Smart Agriculture  
**Target Region:** Pakistan (Punjab & Sindh)  
**Theme:** "AI-powered crop intelligence for every farmer."

---

## Part 1: Problem & Vision (30 Seconds)
- *"Distinguished judges, 65% of Pakistan's population depends on agriculture, yet smallholder farmers lose over 30% of their harvest each year to preventable crop diseases like Early Blight on Tomatoes, Yellow Rust on Wheat, and Whitefly-transmitted Leaf Curl Virus on Cotton."*
- *"Current diagnostic apps give an ungrounded classification label and stop there. But a farmer doesn't just need a label—they need an authoritative, weather-aware, multilingual action plan grounded in verified Pakistani agricultural extension science."*
- *"Today we present **ZaraiAI**."*

---

## Part 2: Live Demonstration — Tomato Early Blight in Urdu (90 Seconds)

### Step 1: Language & Region Selection
- **Action:** Open ZaraiAI UI -> Select language: **اردو (Urdu)** -> Select District: **Faisalabad, Punjab**.
- **Narrative:** *"A farmer in Faisalabad uploads a smartphone photo of their affected tomato leaf."*

### Step 2: Computer Vision & Grad-CAM Explainability
- **Action:** Click **"بیماری کی تشخیص کریں" (Analyze Crop Disease)**.
- **Result displayed:**
  - Disease: **ابتدائی جھلسائو (Early Blight / Alternaria solani)**
  - Confidence: **92.4%** (Verified confident)
  - Grad-CAM: Shows model attention centered on concentric target-board lesions on the leaf.
- **Narrative:** *"ZaraiAI's crop-specific EfficientNet model identifies Early Blight and renders Grad-CAM attention maps to explain why the AI reached this conclusion."*

### Step 3: Localized Weather Integration
- **Result displayed:**
  - Real-time weather for Faisalabad: 31°C, 58% RH, Wind 8 km/h, Rain probability 15%.
  - Spray Suitability: **Optimal**.
- **Narrative:** *"ZaraiAI instantly assesses real-time weather from Open-Meteo to confirm that spray conditions are safe and rain wash-off risk is low."*

### Step 4: Authoritative Knowledge Base RAG & Action Plan
- **Result displayed:**
  - Action 1: Prune lower infected leaves to reduce fungal spore load.
  - Action 2: Apply protective fungicide **Mancozeb 75% WP @ 2.5 g/L** as per Punjab Agriculture Department guidelines.
  - Action 3: Observe 7-day Pre-Harvest Interval (PHI) before picking tomatoes.
  - **Sources Drawer:** Displays citations from *CABI PlantwisePlus Pakistan* & *Punjab Agriculture Extension*.

---

## Part 3: Roman Urdu Follow-Up & Cotton/Wheat Coverage (45 Seconds)
- **Action:** Switch to **Ask ZaraiAI** tab -> Ask in Roman Urdu:  
  `"Kapas par safed makhi ka hamla hai, whitefly control spray bataein"`
- **Result:** Instant grounded advice citing *CCRI Multan* guidelines: Pyriproxyfen 10.8 EC @ 400ml/acre or Acetamiprid, with Economic Injury Level threshold (5 whiteflies/leaf).
- **Action:** Show Wheat Rust alerts and dataset manifest in Tab 3.

---

## Part 4: Technical Rigor & Scientific Integrity (15 Seconds)
- *"ZaraiAI was trained strictly on deduplicated original field images with zero data leakage, validated with 10 automated end-to-end tests, and backed by Alibaba Cloud Model Studio Qwen3.7-Plus for multilingual reasoning."*
- *"Thank you!"*
