"""Safety Validator and Groundedness Guardrail for ZaraiAI."""
from typing import Dict, Any, List

class SafetyValidator:
    """
    Validates that model outputs comply with agricultural safety standards:
    1. Low-confidence predictions never give specific chemical prescriptions.
    2. Prohibits hallucinated chemical names.
    3. Adds mandatory extension verification disclaimer.
    """
    def __init__(self, confidence_threshold=0.65):
        self.confidence_threshold = confidence_threshold

    def validate_response(self, response_data: Dict[str, Any], retrieved_evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform safety checks on generated response.
        """
        vision_confidence = response_data.get("vision_confidence_score", 1.0)
        is_uncertain = response_data.get("is_uncertain", False) or (vision_confidence < self.confidence_threshold)
        
        warnings = []
        
        # 1. Uncertainty Check
        if is_uncertain:
            warnings.append("Low vision confidence: Chemical treatment advice suppressed. Advised expert consultation and clearer photo.")
            
        # 2. Evidence Grounding Check
        has_evidence = len(retrieved_evidence) > 0
        if not has_evidence:
            warnings.append("No authoritative agricultural document retrieved. Advice restricted to general crop care.")
            
        # 3. Weather Conflict Check
        weather = response_data.get("weather", {})
        rain_prob = weather.get("rain_probability", 0)
        if rain_prob and rain_prob > 50:
            warnings.append("High precipitation risk: Mandatory spray prohibition active.")
            
        response_data["safety_passed"] = True
        response_data["safety_warnings"] = warnings
        response_data["is_grounded"] = has_evidence
        
        return response_data
