"""Unit Tests for Weather Advisory, Spray Suitability, Safety, and Multilingual Support."""
import sys
from pathlib import Path
import pytest

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.weather.client import WeatherAdvisor
from src.safety.validator import SafetyValidator
from src.workflow.graph import ZaraiWorkflow

def test_weather_client_live_or_fallback():
    """Verify weather fetching for key Pakistani agricultural districts."""
    advisor = WeatherAdvisor()
    res = advisor.get_weather("faisalabad")
    
    assert res["status"] in ["success", "unavailable"]
    assert "spray_suitability" in res
    assert "spray_advice_en" in res
    assert "spray_advice_ur" in res

def test_weather_spray_warning_rules():
    """Verify spray safety warnings trigger on rain probability >40% or wind >15km/h."""
    advisor = WeatherAdvisor()
    eval_res = advisor._evaluate_spray_conditions(temp=32.0, humidity=85.0, wind_speed=18.0, rain_prob=60)
    
    assert eval_res["suitability"] == "Caution / Suboptimal"
    assert "wind" in eval_res["advice_en"].lower() or "rain" in eval_res["advice_en"].lower()

def test_safety_validator_low_confidence():
    """Verify safety validator catches uncertain detections."""
    validator = SafetyValidator(confidence_threshold=0.65)
    sample_response = {
        "vision_confidence_score": 0.45,
        "is_uncertain": True,
        "weather": {"rain_probability": 10}
    }
    validated = validator.validate_response(sample_response, retrieved_evidence=[{"mock": 1}])
    assert len(validated["safety_warnings"]) > 0
    assert "Low vision confidence" in validated["safety_warnings"][0]

def test_end_to_end_multilingual_workflow():
    """Verify complete end-to-end pipeline execution across English, Urdu, and Roman Urdu."""
    workflow = ZaraiWorkflow()
    
    # 1. Urdu Query
    ur_res = workflow.run_pipeline(
        crop="tomato",
        image_input=None,
        user_query="میرے ٹماٹر کے پودوں پر ابتدائی جھلسائو ہے، کیا سپرے کروں؟",
        language="ur",
        district="multan"
    )
    assert ur_res["crop"] == "tomato"
    assert "زرعی رہنمائی" in ur_res["response_text"] or "تجویز کردہ" in ur_res["response_text"] or "مشاہدہ" in ur_res["response_text"] or "ٹماٹر" in ur_res["response_text"]
    assert len(ur_res["citations"]) > 0

    # 2. Roman Urdu Query
    roman_res = workflow.run_pipeline(
        crop="cotton",
        image_input=None,
        user_query="Kapas par safed makhi ka hamla hai, whitefly control spray bataein",
        language="roman_ur",
        district="shaheed_benazirabad"
    )
    assert roman_res["crop"] == "cotton"
    assert "Cotton" in roman_res["response_text"] or "Spray" in roman_res["response_text"] or "Tadbeer" in roman_res["response_text"] or "Tajweez" in roman_res["response_text"]
    assert len(roman_res["citations"]) > 0

    # 3. English Query
    en_res = workflow.run_pipeline(
        crop="wheat",
        image_input=None,
        user_query="Yellow rust stripes observed on wheat leaves",
        language="en",
        district="faisalabad"
    )
    assert en_res["crop"] == "wheat"
    assert len(en_res["citations"]) > 0
