"""End-to-End Decision Workflow and State Machine Orchestration for ZaraiAI."""
import os
import re
from typing import Dict, Any, Optional
from PIL import Image
from pathlib import Path

from src.vision.inference import CropVisionInference
from src.rag.retriever import AgriculturalRetriever
from src.rag.citations import format_citations, build_evidence_context
from src.weather.client import WeatherAdvisor
from src.llm.client import QwenClient
from src.llm.prompts import get_system_prompt, build_user_prompt
from src.safety.validator import SafetyValidator
from src.config import TAXONOMY

def is_relevant_agricultural_query(query: str) -> bool:
    """Check if query is relevant to agriculture, crops, diseases, sprays, farming, or weather."""
    if not query or len(query.strip()) < 3:
        return True
    
    q = query.lower()
    
    # Common obvious off-topic patterns
    off_topic_patterns = [
        "what is the capital", "capital of", "who is", "who was", "who founded",
        "2+2", "calculate", "solve", "math", "president", "prime minister",
        "tell me a joke", "write code", "python code", "movie", "song", "lyrics",
        "bitcoin", "crypto", "cricket", "football", "recipe for", "translate to"
    ]
    for otp in off_topic_patterns:
        if otp in q:
            return False
            
    # Key agriculture vocabulary (English, Urdu, Roman Urdu)
    agri_terms = [
        "crop", "plant", "leaf", "leaves", "disease", "fungus", "fungicide", "pesticide",
        "spray", "dose", "dosage", "fertilizer", "urea", "dap", "potash", "sop", "irrigation",
        "water", "seed", "variety", "varieties", "yield", "sowing", "harvest", "phi",
        "cotton", "wheat", "tomato", "kapas", "gandum", "tamatar", "patta", "patton",
        "bemari", "keera", "makhi", "whitefly", "rust", "blight", "spot", "wilt", "blast",
        "weather", "temperature", "rain", "hawa", "mausam", "sardi", "garmi", "kisaan", "kheti",
        "فصل", "پودا", "پتا", "پتے", "بیماری", "اسپرے", "سپرے", "کھاد", "پانی", "آبپاشی",
        "گندم", "کپاس", "ٹماٹر", "کنگی", "جھلسائو", "مرجھائو", "سفید مکھی", "زرعی"
    ]
    
    for term in agri_terms:
        if term in q:
            return True
            
    return len(q.split()) > 2

class ZaraiWorkflow:
    """Complete decision support pipeline for Pakistani farmers."""
    def __init__(self):
        self.vision_engines = {}
        self.retriever = AgriculturalRetriever()
        self.weather_advisor = WeatherAdvisor()
        self.llm_client = QwenClient()
        self.safety_validator = SafetyValidator(confidence_threshold=0.65)
        
    def _get_vision_engine(self, crop: str) -> CropVisionInference:
        crop_clean = crop.lower()
        if crop_clean not in self.vision_engines:
            self.vision_engines[crop_clean] = CropVisionInference(crop_name=crop_clean)
        return self.vision_engines[crop_clean]

    def run_pipeline(
        self,
        crop: str,
        image_input: Optional[Any] = None,
        user_query: str = "",
        language: str = "ur",
        district: str = "faisalabad",
        llm_client: Optional[QwenClient] = None
    ) -> Dict[str, Any]:
        """
        Execute full end-to-end ZaraiAI pipeline:
        validate -> vision -> retrieve -> weather -> llm -> safety -> response
        """
        crop_lower = crop.lower()
        if crop_lower not in ["tomato", "wheat", "cotton"]:
            return {
                "status": "error",
                "error": f"Unsupported crop '{crop}'. ZaraiAI MVP strictly supports Tomato, Wheat, and Cotton."
            }
            
        result = {
            "crop": crop_lower,
            "language": language,
            "district": district,
            "vision": None,
            "weather": None,
            "citations": [],
            "response_text": "",
            "is_uncertain": False,
            "llm_connected": False
        }
        
        # Step 1: Vision Inference (if image provided)
        search_query = user_query
        vision_res = None
        is_chat_mode = (image_input is None)
        prompt_mode = "chat" if is_chat_mode else "diagnosis"
        is_relevant = True
        
        if image_input is not None:
            vision_engine = self._get_vision_engine(crop_lower)
            vision_res = vision_engine.predict(image_input, generate_cam=True)
            result["vision"] = vision_res
            result["is_uncertain"] = vision_res["is_uncertain"]
            result["vision_confidence_score"] = vision_res.get("confidence", 1.0)
            
            # Formulate grounded search query from vision prediction
            pred_name = vision_res["canonical_name"]
            pathogen = vision_res.get("pathogen") or ""
            search_query = f"{crop_lower} {pred_name} {pathogen} management treatment symptoms Pakistan {user_query}".strip()
        else:
            is_relevant = is_relevant_agricultural_query(user_query)
            search_query = f"{crop_lower} {user_query} Pakistan agricultural extension guidance".strip()
            
        # Step 2: RAG Knowledge Retrieval
        retrieved_chunks = []
        evidence_context = "No relevant context needed for non-agricultural inquiry."
        
        if is_relevant:
            retrieved_chunks = self.retriever.retrieve(query=search_query, crop=crop_lower, top_k=4)
            evidence_context = build_evidence_context(retrieved_chunks)
            citations = format_citations(retrieved_chunks)
            result["citations"] = citations
            result["retrieved_chunks"] = retrieved_chunks
        else:
            result["citations"] = []
            result["retrieved_chunks"] = []
        
        # Step 3: Local Weather Assessment
        weather_data = self.weather_advisor.get_weather(district)
        result["weather"] = weather_data
        
        # Step 4: LLM Grounded Synthesis
        vision_pred_str = vision_res["canonical_name"] if vision_res else "No image provided (Text Consultation)"
        vision_conf_str = vision_res["confidence_percentage"] if vision_res else "N/A"
        
        user_prompt = build_user_prompt(
            crop=crop_lower,
            vision_prediction=vision_pred_str,
            vision_confidence=vision_conf_str,
            evidence_context=evidence_context,
            weather_info=weather_data,
            user_query=user_query,
            target_language=language,
            mode=prompt_mode
        )
        
        active_llm = llm_client or self.llm_client
        llm_output = active_llm.generate_response(
            system_prompt=get_system_prompt(language, mode=prompt_mode),
            user_prompt=user_prompt
        )
        
        raw_text = llm_output.get("content", "")
        result["llm_status"] = llm_output.get("status", "unknown")
        result["llm_model"] = llm_output.get("model", active_llm.model)
        result["llm_provider"] = active_llm.provider
        result["llm_connected"] = (llm_output.get("status") == "success")
        
        # Format dynamic grounded response if LLM is offline or in template fallback mode
        if llm_output.get("status") in ["fallback", "error"]:
            raw_text = self._build_deterministic_response(
                crop=crop_lower,
                vision_res=vision_res,
                retrieved_chunks=retrieved_chunks,
                weather_data=weather_data,
                language=language,
                is_chat=is_chat_mode,
                user_query=user_query,
                is_relevant=is_relevant
            )
            
        result["response_text"] = raw_text
        
        # Step 5: Safety Guardrails
        validated_result = self.safety_validator.validate_response(result, retrieved_chunks)
        
        return validated_result

    def _build_deterministic_response(
        self,
        crop: str,
        vision_res: dict,
        retrieved_chunks: list,
        weather_data: dict,
        language: str,
        is_chat: bool = False,
        user_query: str = "",
        is_relevant: bool = True
    ) -> str:
        """Dynamic grounded extraction from retrieved knowledge chunks when LLM API key is pending."""
        pred = vision_res["canonical_name"] if vision_res else "Crop Consultation"
        urdu_pred = vision_res["urdu_name"] if vision_res else pred
        roman_pred = vision_res["roman_urdu_name"] if vision_res else pred
        conf = vision_res["confidence_percentage"] if vision_res else "N/A"
        pathogen = vision_res.get("pathogen") if vision_res else None
        pathogen_str = f" ({pathogen})" if pathogen else ""
        
        # Off-topic / Non-Agricultural Refusal
        if is_chat and not is_relevant:
            if language == "ur":
                return "میں ایک زرعی معاون نظام ہوں، جو خاص طور پر پاکستان میں ٹماٹر، گندم اور کپاس کے کسانوں کی رہنمائی کے لیے بنایا گیا ہے۔ برائے مہربانی صرف فصلوں کی بیماریوں، کھاد، اسپرے یا کاشت کاری سے متعلق سوال پوچھیں۔"
            elif language == "roman_ur":
                return "Main ZaraiAI hoon, jo Pakistan mein Tamatar, Gandum aur Kapas ki zirat aur bemarion ke mashwaray ke liye banaya gaya hai. Barah-e-karam faslon ki bemarion, spray ya kheti ke mutaliq sawal poochein."
            else:
                return "I am ZaraiAI, dedicated exclusively to agricultural decision support for Tomato, Wheat, and Cotton in Pakistan. Please ask me about crop diseases, sprays, irrigation, seed varieties, or farming practices."

        # Extract specific recommendations from the top retrieved knowledge chunk
        top_chunk_text = retrieved_chunks[0]["content"] if retrieved_chunks else ""
        top_source = retrieved_chunks[0]["metadata"]["document_title"] if retrieved_chunks else "Government of Punjab Agriculture Department / CABI Pakistan"
        
        # Dynamic extraction of treatments
        chemical_lines = [line.strip() for line in top_chunk_text.split("\n") if ("WP" in line or "EC" in line or "Spray" in line or "@" in line or "g/L" in line)]
        cultural_lines = [line.strip() for line in top_chunk_text.split("\n") if ("Crop Rotation" in line or "Certified" in line or "Spacing" in line or "Resistant" in line or "Sowing" in line or "Prune" in line)]
        
        action_chem = chemical_lines[0].lstrip("-*• ") if chemical_lines else "Apply registered protective fungicide as per official extension schedule."
        action_cult = cultural_lines[0].lstrip("-*• ") if cultural_lines else "Prune lower infected foliage and destroy crop residues."
        
        # Conversational Chat Mode Fallback
        if is_chat:
            if language == "ur":
                return f"""### 💡 {crop.capitalize()} کے لیے زرعی رہنمائی
مستند زرعی حوالہ جات (*{top_source}*) کے مطابق:

- **تجویز کردہ زراعتی تدابیر:** {action_cult}
- **مصدقہ اسپرے و کیمیائی حل:** {action_chem}
- **موسم اور اسپرے کی حفاظت:** {weather_data.get('spray_advice_ur', 'اسپرے کے دوران حفاظتی تدابیر اور وقفے کا خیال رکھیں۔')}

ماخذ: *{top_source}*"""

            elif language == "roman_ur":
                return f"""### 💡 {crop.capitalize()} Ke Liye Agricultural Guidance
Official agricultural records (*{top_source}*) ke mutabiq:

- **Tadbeer & Prevention:** {action_cult}
- **Approved Spray & Treatment:** {action_chem}
- **Mausam Aur Hifazat:** {weather_data.get('spray_advice_roman_ur', 'Mausam ke mutabiq spray aur safety ka khayal rakhein.')}

Reference: *{top_source}*"""

            else:
                return f"""### 💡 Agricultural Guidance for {crop.capitalize()}
Based on official agricultural guidelines (*{top_source}*):

- **Recommended Cultural Practices:** {action_cult}
- **Approved Chemical Treatments:** {action_chem}
- **Weather & Field Application:** {weather_data.get('spray_advice_en', 'Adhere to official pre-harvest intervals and safe spray conditions.')}

Source: *{top_source}*"""

        # Visual Image Diagnosis Mode Fallback
        if language == "ur":
            return f"""### 🔍 پتے کا مشاہدہ اور علامات
فصل کے پتے پر بیماری کی علامات ظاہر ہو رہی ہیں۔ مستند زرعی گائیڈ لائنز کے مطابق تشخیصی جائزہ درج ذیل ہے۔

### 🛠️ تجویز کردہ زرعی و کیمیائی اقدامات
1. **زراعتی و حفاظتی تدابیر:** {action_cult}
2. **مصدقہ کیمیائی اسپرے:** {action_chem}
3. **حفاظتی وقفہ (PHI) اور احتیاط:** دوائی کے لیبل پر درج احتیاطی وقفے کا خیال رکھیں، ماسک اور دستانے استعمال کریں اور صاف پانی سے محلول بنائیں۔

### 🌦️ موسمی ہدایات برائے اسپرے
{weather_data.get('spray_advice_ur', 'موسمی حالات کا مشاہدہ کریں۔')}

### 👨‍🌾 ماہرین سے رجوع کرنے کی شرائط
اگر علامات 5 دن میں بہتر نہ ہوں یا بیماری زیادہ پھیلے تو قریبی فیلڈ ایگریکلچر افسر سے فوری رابطہ کریں۔

### 📚 مستند زرعی ماخذ
ماخذ: *{top_source}*"""

        elif language == "roman_ur":
            return f"""### 🔍 Patte Ka Mushahida (Observations)
Patton par bemari ki wazeh alamaat hain. Official agricultural extension data ke mutabiq action plan darj zail hai:

### 🛠️ Tajweez Karda Iqdaam (Action Plan)
1. **Kheti Ke Bachao Ki Tadbeer:** {action_cult}
2. **Approved Chemical Spray:** {action_chem}
3. **Spray Safety & PHI:** Spray ke baad katai ke darmiyani waqfe (PHI) ka khayal rakhein aur mask/gloves istemal karein.

### 🌦️ Mausam Aur Spray Rehnumai
{weather_data.get('spray_advice_roman_ur', 'Mausam check karein.')}

### 👨‍🌾 Expert Help Kab Lein?
Agar bemari 5 din mein control na ho to foran qareebi Agriculture Officer se rabta karein.

### 📚 Official Source
Reference: *{top_source}*"""

        else:
            return f"""### 🔍 What Was Observed
Leaf analysis indicates active disease symptoms matching official Pakistani extension pathology records.

### 🛠️ Recommended Action Plan
1. **Cultural & Preventive Hygiene:** {action_cult}
2. **Approved Chemical Treatment:** {action_chem}
3. **Safety & Pre-Harvest Interval (PHI):** Adhere strictly to the pre-harvest interval (PHI) on the product label. Always wear protective PPE and avoid application during high heat or high winds.

### 🌦️ Weather & Spray Advisory
{weather_data.get('spray_advice_en', 'Weather conditions evaluated.')}

### 👨‍🌾 When to Seek Extension Officer Help
Consult your local Agricultural Extension Officer if symptoms persist past 5 days or lesion coverage exceeds 10% of the field canopy.

### 📚 Official Knowledge Source
Grounded in: *{top_source}*"""
