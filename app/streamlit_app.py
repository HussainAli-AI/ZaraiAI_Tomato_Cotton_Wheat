"""ZaraiAI: Multilingual AI Crop Intelligence Web Application for Pakistan."""
import sys
from pathlib import Path
import os

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from PIL import Image
import pandas as pd
import json
import torch

# Optimize PyTorch memory footprint for cloud container limits
torch.set_num_threads(1)

from src.workflow.graph import ZaraiWorkflow
from src.llm.client import QwenClient, PROVIDER_PRESETS
from src.weather.client import PAKISTAN_AGRICULTURAL_DISTRICTS
from src.config import TAXONOMY

# Page Configuration
st.set_page_config(
    page_title="ZaraiAI - Crop Intelligence for Pakistan",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design & Multilingual RTL Support
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Noto+Nastaliq+Urdu:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .urdu-text {
        font-family: 'Noto Nastaliq Urdu', serif !important;
        direction: rtl !important;
        text-align: right !important;
        line-height: 2.2 !important;
        font-size: 1.15rem !important;
        unicode-bidi: embed !important;
    }
    
    .hero-container {
        background: linear-gradient(135deg, #103B2B 0%, #1E6B47 100%);
        padding: 2.2rem;
        border-radius: 16px;
        color: #FFFFFF;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(16, 59, 43, 0.2);
    }
    
    .badge-confidence {
        display: inline-block;
        padding: 0.4rem 0.95rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
        background-color: #E8F5E9;
        color: #1B5E20 !important;
        border: 1.5px solid #2E7D32;
    }
    
    .badge-warning {
        background-color: #FFF3E0 !important;
        color: #B45309 !important;
        border: 1.5px solid #F59E0B !important;
    }
    
    .card-metric {
        background: #F1F8F4;
        border: 1px solid #A5D6A7;
        border-radius: 12px;
        padding: 1.1rem;
        text-align: center;
        color: #0F172A;
        font-size: 1rem;
    }
    
    .source-card {
        background: #F0FDF4;
        border-left: 5px solid #16A34A;
        border-top: 1px solid #DCFCE7;
        border-right: 1px solid #DCFCE7;
        border-bottom: 1px solid #DCFCE7;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: #0F172A;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
    }
    
    .source-title {
        font-weight: 700;
        font-size: 1.1rem;
        color: #15803D !important;
        margin-bottom: 6px;
    }
    
    .source-meta {
        font-size: 0.95rem;
        color: #334155 !important;
        line-height: 1.6;
    }
    
    .llm-badge-live {
        background-color: #DCFCE7;
        color: #166534 !important;
        border: 1.5px solid #22C55E;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 12px;
    }
    
    .llm-badge-offline {
        background-color: #FEF3C7;
        color: #92400E !important;
        border: 1.5px solid #F59E0B;
        padding: 6px 14px;
        border-radius: 12px;
        font-size: 0.9rem;
        font-weight: 700;
        display: inline-block;
        margin-bottom: 12px;
    }
    
    .advisory-box {
        background: #F8FAFC;
        border: 1.5px solid #CBD5E1;
        border-left: 6px solid #16A34A;
        border-radius: 14px;
        padding: 1.8rem 2.2rem;
        font-size: 1.08rem;
        line-height: 1.85;
        color: #0F172A !important;
        margin-top: 1rem;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    
    .advisory-box h2, .advisory-box h3 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #15803D !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 6px;
    }
    
    .advisory-box h2:first-child, .advisory-box h3:first-child {
        margin-top: 0 !important;
    }
    
    .advisory-box p {
        font-size: 1.06rem !important;
        font-weight: 450 !important;
        line-height: 1.85 !important;
        margin-bottom: 0.95rem !important;
        color: #1E293B !important;
    }
    
    .advisory-box ol, .advisory-box ul {
        margin-top: 0.5rem;
        margin-bottom: 1.2rem;
        padding-left: 1.6rem;
    }
    
    .advisory-box li {
        font-size: 1.05rem !important;
        font-weight: 450 !important;
        line-height: 1.85 !important;
        margin-bottom: 0.8rem !important;
        color: #1E293B !important;
    }
    
    .advisory-box strong, .advisory-box b {
        font-weight: 700 !important;
        color: #0F172A !important;
    }
    
    /* Dark Mode Overrides */
    @media (prefers-color-scheme: dark) {
        .advisory-box {
            background: #0B1914 !important;
            border: 1.5px solid #1E4634 !important;
            border-left: 6px solid #22C55E !important;
            color: #F1F5F9 !important;
        }
        .advisory-box p, .advisory-box li {
            color: #E2E8F0 !important;
        }
        .advisory-box strong, .advisory-box b {
            color: #86EFAC !important;
        }
        .advisory-box h2, .advisory-box h3 {
            color: #4ADE80 !important;
            border-bottom: 2px solid #1E4634 !important;
        }
        .source-card {
            background: #0B1914 !important;
            border-top: 1px solid #1E4634 !important;
            border-right: 1px solid #1E4634 !important;
            border-bottom: 1px solid #1E4634 !important;
            color: #F1F5F9 !important;
        }
        .source-meta {
            color: #CBD5E1 !important;
        }
        .card-metric {
            background: #0B1914 !important;
            border: 1px solid #1E4634 !important;
            color: #F1F5F9 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Cached Global Workflow Instance (Memory-Efficient Singleton)
@st.cache_resource
def get_global_workflow():
    return ZaraiWorkflow()

workflow = get_global_workflow()

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "latest_analysis" not in st.session_state:
    st.session_state.latest_analysis = None
if "active_llm_client" not in st.session_state:
    st.session_state.active_llm_client = QwenClient()

# UI Localization Dictionary
UI_TEXT = {
    "en": {
        "tagline": "AI-Powered Crop Intelligence for Every Farmer",
        "crop_select": "Select Target Crop",
        "lang_select": "Select Language",
        "district_select": "Agricultural District",
        "upload_label": "Upload Crop Leaf Photo",
        "notes_label": "Additional Notes (Optional):",
        "notes_ph": "e.g., Lower leaves turning yellow with dark spots after rain",
        "analyze_btn": "🔍 Analyze Crop Disease",
        "analyzing": "Analyzing leaf image and generating grounded decision guidance...",
        "prediction_header": "Diagnosis Results",
        "gradcam_header": "Visual Model Attention (Grad-CAM)",
        "weather_header": "Real-Time Weather & Spray Advisory",
        "action_plan_header": "Action Plan & Decision Guidance",
        "ask_header": "Ask ZaraiAI Agricultural Guidance",
        "chat_ph": "Ask about diseases, sprays, irrigation, or fertilizer for Tomato, Wheat, Cotton:",
        "chat_send": "Send Question",
        "source_drawer": "📚 Grounded Agricultural Sources & Evidence",
        "gradcam_disclaimer": "⚠️ The heatmap highlights image regions influencing the AI prediction and is not a biological lesion mask.",
        "uncertain_warning": "⚠️ Low AI confidence. Image may be blurry or out-of-distribution. Please capture a clear, close photo in natural light.",
        "tabs": ["🔬 Disease Analysis", "💬 Ask ZaraiAI", "📚 Knowledge Sources & Manifest"]
    },
    "ur": {
        "tagline": "ہر کسان کے لیے جدید ترین زرعی مصنوعی ذہانت",
        "crop_select": "فصل کا انتخاب کریں",
        "lang_select": "زبان منتخب کریں",
        "district_select": "زرعی ضلع منتخب کریں",
        "upload_label": "پودے کے پتے کی تصویر اپلوڈ کریں",
        "notes_label": "اضافی تفصیل یا نوٹ (اختیاری):",
        "notes_ph": "مثلاً: بارش کے بعد نچلے پتے پیلے ہو رہے ہیں اور داغ بن رہے ہیں",
        "analyze_btn": "🔍 بیماری کی تشخیص کریں",
        "analyzing": "تصویر کا تجزیہ اور مستند زرعی گائیڈ لائنز حاصل کی جا رہی ہیں...",
        "prediction_header": "تشخیصی نتائج",
        "gradcam_header": "ماڈل فوکس میپ (Grad-CAM)",
        "weather_header": "موسمی صورتحال اور سپرے کی رہنمائی",
        "action_plan_header": "حکمت عملی اور تجاویز",
        "ask_header": "زرعی سوال پوچھیں",
        "chat_ph": "ٹماٹر، گندم یا کپاس کی بیماریوں، سپرے، کھاد اور آبپاشی کے بارے میں پوچھیں:",
        "chat_send": "سوال بھیجیں",
        "source_drawer": "📚 مستند زرعی کتب و حکومتی گائیڈ لائنز",
        "gradcam_disclaimer": "⚠️ ہیٹ میپ ماڈل کی توجہ ظاہر کرتا ہے، یہ بیماری کا میڈیکل سائز نہیں ہے۔",
        "uncertain_warning": "⚠️ ماڈل کا اعتماد کم ہے۔ براہ کرم واضح اور قدرتی روشنی میں قریبی تصویر لیں۔",
        "tabs": ["🔬 بیماری کی تشخیص", "💬 زرعی سوال و جواب", "📚 مستند کتب و ذرائع"]
    },
    "roman_ur": {
        "tagline": "Har Kisaan Ke Liye Jadeed Ziraat AI",
        "crop_select": "Fasal Select Karein",
        "lang_select": "Zaban Select Karein",
        "district_select": "Zilai Area (District)",
        "upload_label": "Patte Ki Photo Upload Karein",
        "notes_label": "Izafi Detail / Notes (Optional):",
        "notes_ph": "Maslan: Baarish ke baad nichlay patte peelay ho rahay hain",
        "analyze_btn": "🔍 Bemari Check Karein",
        "analyzing": "Photo analyze aur official guide check ho rahi hai...",
        "prediction_header": "Tashkheesi Nataij",
        "gradcam_header": "Model Focus Heatmap (Grad-CAM)",
        "weather_header": "Mausam Aur Spray Rehnumai",
        "action_plan_header": "Kisaan Action Plan",
        "ask_header": "ZaraiAI Se Sawal Poochein",
        "chat_ph": "Tamatar, Gandum ya Kapas ki bemarion, spray, khad ya pani ke baray mein poochein:",
        "chat_send": "Sawal Bhejein",
        "source_drawer": "📚 Official Sources & Evidence",
        "gradcam_disclaimer": "⚠️ Heatmap model ke focus ko zahir karta hai, lesion boundary nahi hai.",
        "uncertain_warning": "⚠️ Model confidence kam hai. Barah-e-karam saaf aur qareebi photo lein.",
        "tabs": ["🔬 Bemari Ki Tashkhees", "💬 ZaraiAI Chat", "📚 Knowledge Sources"]
    }
}

# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/plant-under-rain.png", width=70)
    st.title("🌱 ZaraiAI Settings")
    
    # Language, Crop, District
    lang = st.selectbox(
        "Language / زبان",
        options=["en", "ur", "roman_ur"],
        format_func=lambda x: {"en": "English", "ur": "اردو (Urdu)", "roman_ur": "Roman Urdu"}[x],
        index=0
    )
    t = UI_TEXT[lang]
    
    crop_display = {
        "en": {"tomato": "🍅 Tomato", "wheat": "🌾 Wheat", "cotton": "🌿 Cotton"},
        "ur": {"tomato": "🍅 ٹماٹر", "wheat": "🌾 گندم", "cotton": "🌿 کپاس"},
        "roman_ur": {"tomato": "🍅 Tamatar", "wheat": "🌾 Gandum", "cotton": "🌿 Kapas"}
    }
    
    crop = st.selectbox(
        t["crop_select"],
        options=["tomato", "wheat", "cotton"],
        format_func=lambda x: crop_display[lang].get(x, x.capitalize()),
        index=0
    )
    
    district_keys = list(PAKISTAN_AGRICULTURAL_DISTRICTS.keys())
    district = st.selectbox(
        t["district_select"],
        options=district_keys,
        format_func=lambda x: PAKISTAN_AGRICULTURAL_DISTRICTS[x]["name"],
        index=0
    )
    
    st.divider()
    
    # Interactive LLM Configuration Expander
    with st.expander("🤖 Live LLM Configuration", expanded=True):
        provider_key = st.selectbox(
            "LLM Provider:",
            options=list(PROVIDER_PRESETS.keys()),
            format_func=lambda x: PROVIDER_PRESETS[x]["name"],
            index=0
        )
        preset = PROVIDER_PRESETS[provider_key]
        
        # Get existing key from env
        default_env_key = preset.get("env_key", "")
        env_val = os.getenv(default_env_key, "") if default_env_key else ""
        if not env_val:
            env_val = os.getenv("ALIBABA_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GROQ_API_KEY") or ""
            
        custom_key = st.text_input(
            f"{preset['name']} API Key:",
            value=env_val,
            type="password",
            placeholder="Paste your API key here (e.g. sk-...)",
            key=f"key_input_{provider_key}"
        )
        
        # Clean model selection dropdown
        available_models = preset.get("fallback_models", [preset["default_model"]])
        if preset["default_model"] not in available_models:
            available_models = [preset["default_model"]] + available_models
            
        custom_model = st.selectbox(
            "Select Model:",
            options=available_models,
            index=0,
            key=f"model_choice_{provider_key}"
        )
        
        # Update active LLM client in session state
        st.session_state.active_llm_client = QwenClient(
            provider=provider_key,
            api_key=custom_key,
            base_url=preset["base_url"],
            model=custom_model
        )
        
        col_test, col_status = st.columns([1, 1])
        with col_test:
            if st.button("⚡ Test LLM", use_container_width=True):
                with st.spinner("Connecting to LLM..."):
                    test_res = st.session_state.active_llm_client.test_connection()
                    if test_res["success"]:
                        st.success("✅ " + test_res["message"])
                    else:
                        st.error("❌ " + test_res["message"])
                        
        if st.session_state.active_llm_client.is_configured():
            st.markdown(f"<span class='llm-badge-live'>🟢 Live LLM Active: {custom_model}</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='llm-badge-offline'>🟠 Grounded Extension Engine (Offline Fallback)</span>", unsafe_allow_html=True)
            st.caption("Enter your API key above to enable dynamic AI dialogue.")
            
    st.divider()
    st.markdown("""
    **Track:** Smart Agriculture (Pakistan)  
    **Models:** EfficientNet-B0 + Grad-CAM  
    **RAG:** Pakistani Extension Publications  
    **Weather:** Open-Meteo API (Live)
    """)

# Header Hero Banner
st.markdown(f"""
<div class="hero-container">
    <h1 style="margin:0; font-size:2.5rem; font-weight:700;">🌱 ZaraiAI</h1>
    <p style="margin:0.5rem 0 0 0; font-size:1.2rem; opacity:0.95;">{t['tagline']}</p>
</div>
""", unsafe_allow_html=True)

# Main Workspace Tabs
tab1, tab2, tab3 = st.tabs(t["tabs"])

with tab1:
    col_input, col_preview = st.columns([1, 1])
    
    with col_input:
        st.subheader(t["upload_label"])
        uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png"], key="leaf_uploader")
        
        user_notes = st.text_input(
            t["notes_label"],
            placeholder=t["notes_ph"]
        )
        
        analyze_btn = st.button(t["analyze_btn"], type="primary", use_container_width=True)
        
    with col_preview:
        if uploaded_file:
            preview_img = Image.open(uploaded_file).convert("RGB")
            st.image(preview_img, caption="Uploaded Leaf Image", use_container_width=True)
            
    # Process Analysis
    if analyze_btn and uploaded_file:
        with st.spinner(t["analyzing"]):
            img = Image.open(uploaded_file).convert("RGB")
            result = workflow.run_pipeline(
                crop=crop,
                image_input=img,
                user_query=user_notes,
                language=lang,
                district=district,
                llm_client=st.session_state.active_llm_client
            )
            st.session_state.latest_analysis = result
            
    # Display Results
    if st.session_state.latest_analysis:
        res = st.session_state.latest_analysis
        st.divider()
        
        # Diagnosis Header & Badges
        col_res1, col_res2, col_res3 = st.columns([2, 1, 1])
        
        with col_res1:
            st.subheader(t["prediction_header"])
            vis = res.get("vision")
            if vis:
                pred_title = vis["urdu_name"] if lang == "ur" else (vis["roman_urdu_name"] if lang == "roman_ur" else vis["canonical_name"])
                st.markdown(f"### **{pred_title}**")
                if vis.get("pathogen"):
                    st.caption(f"*Pathogen:* {vis['pathogen']}")
            else:
                st.markdown("### General Consultation")
                
        with col_res2:
            if vis:
                conf = vis["confidence_percentage"]
                if vis["is_uncertain"]:
                    st.markdown(f"<div class='badge-confidence badge-warning'>⚠️ Confidence: {conf}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='badge-confidence'>✅ Confidence: {conf}</div>", unsafe_allow_html=True)
                    
        with col_res3:
            st.markdown(f"<div class='card-metric'><b>Crop:</b> {res['crop'].capitalize()}<br><b>Region:</b> {res['district'].capitalize()}</div>", unsafe_allow_html=True)
            
        # Warning if uncertain
        if vis and vis.get("is_uncertain"):
            st.warning(t["uncertain_warning"])
            
        # Visual Explainability & Weather Columns
        col_cam, col_weather = st.columns([1, 1])
        
        with col_cam:
            st.subheader(t["gradcam_header"])
            if vis and vis.get("gradcam_image"):
                st.image(vis["gradcam_image"], caption="Grad-CAM Attention Map", use_container_width=True)
                st.caption(t["gradcam_disclaimer"])
            else:
                st.info("Grad-CAM generated on confident leaf detections.")
                
        with col_weather:
            st.subheader(t["weather_header"])
            w = res.get("weather", {})
            if w.get("status") == "success":
                w_col1, w_col2, w_col3 = st.columns(3)
                w_col1.metric("Temperature", f"{w['temperature_c']} °C")
                w_col2.metric("Humidity", f"{w['relative_humidity']} %")
                w_col3.metric("Wind Speed", f"{w['wind_speed_kmh']} km/h")
                
                spray_msg = w["spray_advice_ur"] if lang == "ur" else (w["spray_advice_roman_ur"] if lang == "roman_ur" else w["spray_advice_en"])
                st.info(f"**Spray Condition:** {spray_msg}")
            else:
                st.caption("Weather metrics unavailable.")
                
        # Farmer Action Plan
        st.subheader(t["action_plan_header"])
        
        # Display engine badge
        if res.get("llm_connected"):
            st.markdown(f"<span class='llm-badge-live'>✨ Dynamically Generated by {res.get('llm_model')} ({res.get('llm_provider', 'LLM').upper()})</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='llm-badge-offline'>⚡ Grounded Extension Engine (Offline Mode - Add API Key for Live LLM)</span>", unsafe_allow_html=True)
            
        rtl_class = "urdu-text" if lang == "ur" else ""
        st.markdown(f"<div class='advisory-box {rtl_class}'>\n\n{res['response_text']}\n\n</div>", unsafe_allow_html=True)
        
        # Citations
        if res.get("citations"):
            with st.expander(t["source_drawer"], expanded=False):
                for cit in res["citations"]:
                    st.markdown(f"""
                    <div class="source-card">
                        <div class="source-title">📄 {cit['title']} ({cit['year']})</div>
                        <div class="source-meta">🏛️ <b>Publisher:</b> {cit['publisher']} | <b>Authority:</b> {cit['authority_level']}</div>
                        <div class="source-meta">📖 <b>Section:</b> {cit['section']}</div>
                    </div>
                    """, unsafe_allow_html=True)

with tab2:
    st.subheader(t["ask_header"])
    chat_query = st.text_input(t["chat_ph"])
    chat_send = st.button(t["chat_send"], type="primary")
    
    if chat_send and chat_query:
        with st.spinner("Retrieving agricultural guidance & querying LLM..."):
            ans = workflow.run_pipeline(
                crop=crop,
                image_input=None,
                user_query=chat_query,
                language=lang,
                district=district,
                llm_client=st.session_state.active_llm_client
            )
            st.session_state.chat_history.append({
                "query": chat_query,
                "response": ans["response_text"],
                "model": ans.get("llm_model", "LLM"),
                "connected": ans.get("llm_connected", False),
                "citations": ans.get("citations", [])
            })
            
    for item in reversed(st.session_state.chat_history):
        with st.chat_message("user"):
            if lang == "ur":
                st.markdown(f"<div class='urdu-text' dir='rtl'>{item['query']}</div>", unsafe_allow_html=True)
            else:
                st.write(item["query"])
                
        with st.chat_message("assistant"):
            if item.get("connected"):
                st.caption(f"✨ Powered by {item.get('model')}")
            if lang == "ur":
                st.markdown(f"<div class='urdu-text' dir='rtl'>\n\n{item['response']}\n\n</div>", unsafe_allow_html=True)
            else:
                st.markdown(item["response"])
            if item.get("citations"):
                st.caption(f"Sources: {', '.join([c['title'] for c in item['citations'][:2]])}")
        st.divider()

with tab3:
    st.subheader("📚 Verified Authoritative Sources & Audit Manifest")
    
    manifest_csv = BASE_DIR / "knowledge_base" / "source_manifest.csv"
    if manifest_csv.exists():
        st.markdown("### Authoritative Knowledge Base Documents (Tier 1)")
        df_kb = pd.read_csv(manifest_csv)
        st.dataframe(df_kb[["source_id", "title", "crop", "publisher", "year", "authority_level"]], use_container_width=True)
        
    ds_manifest = BASE_DIR / "data" / "dataset_manifest.csv"
    if ds_manifest.exists():
        st.markdown("### Verified Dataset Manifest & Checksums")
        df_ds = pd.read_csv(ds_manifest)
        st.dataframe(df_ds[["crop", "name", "doi", "license", "expected_images", "sha256_verified"]], use_container_width=True)
