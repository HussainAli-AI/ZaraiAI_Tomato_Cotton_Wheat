# ZaraiAI: System Architecture & Technical Specifications

**ZaraiAI** is an AI-powered multilingual crop intelligence platform engineered for Pakistani smallholder farmers, targeting three major crops: **Tomato, Wheat, and Cotton**.

---

## 1. High-Level Architectural Diagram

```
+-----------------------------------------------------------------------------------+
|                               FARMER INTERACTION LAYER                            |
|       (Streamlit UI / Multilingual Dialogue: English, Urdu, Roman Urdu)           |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        STATE MACHINE WORKFLOW ORCHESTRATOR                        |
|                               (src/workflow/graph.py)                             |
+---------+------------------------------+----------------------------------+-------+
          |                              |                                  |
          v                              v                                  v
+-------------------+          +-------------------+              +-----------------+
| COMPUTER VISION   |          |  AGRICULTURAL     |              | LOCAL WEATHER   |
| SUBSYSTEM         |          |  RAG SUBSYSTEM    |              | ADVISOR         |
| (src/vision/)     |          |  (src/rag/)       |              | (src/weather/)  |
|                   |          |                   |              |                 |
| - EfficientNet-B0 |          | - Semantic Chunk  |              | - Open-Meteo    |
| - Class Calibrate |          | - Vector Embed    |              | - Rain Warning  |
| - Grad-CAM Visual |          | - Crop Filtering  |              | - Wind Drift    |
|   Explainability  |          | - Tier-1 Citations|              | - Spray Safety  |
+---------+---------+          +---------+---------+              +--------+--------+
          |                              |                                 |
          +------------------------------+---------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                        LLM REASONING & MULTILINGUAL SYNTHESIS                     |
|                   (Alibaba Cloud Model Studio / Qwen3.7-Plus)                     |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           SAFETY & GROUNDING GUARDRAIL                            |
|                            (src/safety/validator.py)                              |
|           - Zero Ungrounded Chemical Claims                                       |
|           - Low-Confidence Warning Suppression                                    |
|           - Verification Disclaimers & Local Escalation                           |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           FINAL FARMER ACTION PLAN                                |
|        (Visual Grad-CAM + Grounded IPM Guidance + Weather Alerts + Citations)     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems

### A. Computer Vision & Explainability (`src/vision/`)
- **Crop-Specific Specialization:** Dedicated classifiers for Tomato (6 classes), Cotton (5 classes), and Wheat (5 classes).
- **Backbone Architecture:** Transfer-learning EfficientNet-B0 and MobileNetV3-Large with custom classification heads.
- **Explainable AI (Grad-CAM):** Generates normalized attention heatmaps overlaying raw leaf imagery to demonstrate model focus without misleading claims of biological lesion segmentation.
- **Confidence Calibration & Fallbacks:** Predictions with confidence `< 0.65` trigger uncertain state warnings, suppressing specific chemical advice and prompting for clearer natural-light leaf captures.

### B. Grounded Knowledge Retrieval / RAG (`src/rag/`)
- **Authoritative Provenance:** Exclusively indexes Tier-1 verified documents (Government of Punjab Agriculture Department, Ayub Agricultural Research Institute Faisalabad, Central Cotton Research Institute Multan, NARC/PARC Islamabad, CABI PlantwisePlus Pakistan).
- **Structure-Preserving Chunking:** Retains agronomic sections, symptoms, and spray schedules intact with complete metadata (Publisher, Year, Authority Tier, Section Header).
- **Vector Retrieval:** Crop-scoped similarity ranking to guarantee wheat recommendations never bleed into cotton queries.

### C. Weather & Agronomic Rules (`src/weather/`)
- **Real-Time Forecasting:** Fetches live temperature, relative humidity, wind speed, and precipitation probability across Pakistani agricultural districts.
- **Spray Condition Rules:**
  - *Rain Risk (>40%):* Warns against chemical applications to avoid wash-off.
  - *Wind Speed (>15 km/h):* Warns of spray drift hazards.
  - *Extreme Heat (>38°C):* Advises morning/evening spray windows.

### D. Multilingual Dialogue Engine (`src/llm/`)
- **Primary LLM:** Alibaba Cloud Model Studio **Qwen3.7-Plus** via OpenAI-compatible endpoints.
- **Multilingual Support:** English, Nastaliq Urdu (`اردو`), and Roman Urdu (`Roman Urdu`), preserving active ingredients, quantities, and citations without loss of meaning.

### E. Safety & Anti-Hallucination Policy (`src/safety/`)
- Zero tolerance for hallucinated pesticides or ungrounded dosages.
- All chemical advice must cite the specific retrieved Tier-1 document and include mandatory Pre-Harvest Intervals (PHI) and local extension officer verification.
