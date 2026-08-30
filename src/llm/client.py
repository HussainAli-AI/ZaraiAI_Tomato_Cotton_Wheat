import os
import re
import json
import requests
from typing import Dict, Any, List, Optional
from src.config import ALIBABA_API_KEY, ALIBABA_BASE_URL, LLM_MODEL

def clean_llm_output(text: str) -> str:
    """Extract and clean final response text, removing thinking traces."""
    if not text:
        return ""
        
    # If standard closing </think> tag exists, take everything after it
    if "</think>" in text:
        content = text.split("</think>")[-1].strip()
        if len(content) > 30:
            return content
            
    # Remove any complete <think>...</think> blocks
    text_clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if text_clean and len(text_clean) > 30:
        text = text_clean

    # If text has markdown section headers, extract from the first section header
    for prefix in ["### ", "## "]:
        idx = text.find(prefix)
        if idx != -1:
            candidate = text[idx:].strip()
            if len(candidate) > 50:
                return candidate
        
    # Fallback: remove remaining tags
    cleaned = text.replace("<think>", "").replace("</think>", "").strip()
    return cleaned

PROVIDER_PRESETS = {
    "gemini": {
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-1.5-flash",
        "env_key": "GEMINI_API_KEY",
        "fallback_models": ["gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"]
    },
    "groq": {
        "name": "Groq (Fast & Free Tier)",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "qwen/qwen3.6-27b",
        "env_key": "GROQ_API_KEY",
        "fallback_models": ["qwen/qwen3.6-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b", "groq/compound"]
    },
    "alibaba": {
        "name": "Alibaba Cloud Qwen (Model Studio)",
        "base_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen3.7-plus",
        "env_key": "ALIBABA_API_KEY",
        "fallback_models": ["qwen3.7-plus", "qwen-max", "qwen-turbo"]
    },
    "openai": {
        "name": "OpenAI (GPT-4o / GPT-4o-mini)",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "fallback_models": ["gpt-4o-mini", "gpt-4o"]
    },
    "openrouter": {
        "name": "OpenRouter (Universal)",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "qwen/qwen-2.5-72b-instruct",
        "env_key": "OPENROUTER_API_KEY",
        "fallback_models": ["qwen/qwen-2.5-72b-instruct", "deepseek/deepseek-chat"]
    },
    "ollama": {
        "name": "Local Ollama (Offline Free)",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.2",
        "env_key": "",
        "fallback_models": ["llama3.2", "qwen2.5", "mistral"]
    }
}

class QwenClient:
    """Unified Universal LLM Client supporting Google Gemini, Groq, Alibaba Qwen, OpenAI, OpenRouter, and Ollama."""
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        preset = PROVIDER_PRESETS.get(self.provider, PROVIDER_PRESETS["gemini"])
        
        # Resolve API Key strictly matching provider
        env_key_name = preset.get("env_key", "")
        if api_key:
            self.api_key = api_key
        elif env_key_name and os.getenv(env_key_name):
            self.api_key = os.getenv(env_key_name)
        elif self.provider == "groq" and os.getenv("GROQ_API_KEY"):
            self.api_key = os.getenv("GROQ_API_KEY")
        elif self.provider == "gemini" and os.getenv("GEMINI_API_KEY"):
            self.api_key = os.getenv("GEMINI_API_KEY")
        elif self.provider == "alibaba" and os.getenv("ALIBABA_API_KEY"):
            self.api_key = os.getenv("ALIBABA_API_KEY")
        elif self.provider == "openai" and os.getenv("OPENAI_API_KEY"):
            self.api_key = os.getenv("OPENAI_API_KEY")
        else:
            self.api_key = ""
        self.api_key = self.api_key.strip()
        
        # Resolve Base URL strictly according to provider
        if base_url:
            self.base_url = base_url
        elif os.getenv("LLM_BASE_URL"):
            self.base_url = os.getenv("LLM_BASE_URL")
        elif self.provider == "alibaba" and os.getenv("ALIBABA_BASE_URL"):
            self.base_url = os.getenv("ALIBABA_BASE_URL")
        else:
            self.base_url = preset["base_url"]
        self.base_url = self.base_url.rstrip("/")
        
        # Resolve Model
        self.model = model or os.getenv("LLM_MODEL") or preset["default_model"]

    def is_configured(self) -> bool:
        """Returns True if the LLM provider has an active key or is a local provider like Ollama."""
        if self.provider == "ollama":
            return True
        return bool(self.api_key and not self.api_key.startswith("your_") and len(self.api_key) > 5)

    def test_connection(self) -> Dict[str, Any]:
        """Verify API key and connectivity with a lightweight prompt."""
        if not self.is_configured():
            return {
                "success": False,
                "message": f"API Key for {self.provider.upper()} is missing. Please add your key in .env or the sidebar."
            }
        
        res = self.generate_response(
            system_prompt="You are an agricultural AI test agent.",
            user_prompt="Reply with the exact text: 'ZaraiAI LLM Connected Successfully.'",
            max_tokens=1000
        )
        if res.get("status") == "success":
            return {
                "success": True,
                "message": f"Connected to {res.get('model', self.model)} via {self.provider.upper()}!",
                "response": res.get("content")
            }
        else:
            return {
                "success": False,
                "message": f"Connection failed: {res.get('error', 'Unknown error')}"
            }

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate grounded response from the configured LLM with automatic model retry if a specific model tag is deprecated.
        """
        if not self.is_configured():
            return self._fallback_generation(system_prompt, user_prompt)
            
        # Determine candidate models to try (primary model first, then fallbacks)
        preset = PROVIDER_PRESETS.get(self.provider, {})
        candidates = [self.model]
        for fb in preset.get("fallback_models", []):
            if fb not in candidates:
                candidates.append(fb)
                
        last_error = ""
        
        for candidate_model in candidates:
            if self.provider == "gemini":
                result = self._call_gemini_native(candidate_model, system_prompt, user_prompt, temperature, max_tokens)
            else:
                result = self._call_openai_compatible(candidate_model, system_prompt, user_prompt, temperature, max_tokens)
                
            if result.get("status") == "success":
                self.model = candidate_model  # Lock onto the working model
                return result
            else:
                last_error = result.get("error", "")
                # If 404/not found, 429 quota exhausted, decommissioned model, or token limit error, automatically try next fallback model
                if "404" in last_error or "429" in last_error or "400" in last_error or "decommissioned" in last_error.lower() or "quota" in last_error.lower() or "not found" in last_error.lower() or "empty" in last_error.lower():
                    continue
                else:
                    break
                    
        return {
            "status": "error",
            "error": last_error,
            "content": self._fallback_generation(system_prompt, user_prompt)["content"]
        }

    def _call_openai_compatible(self, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max(max_tokens, 4096)
        }
        
        try:
            res = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                raw_content = data["choices"][0]["message"]["content"]
                content = clean_llm_output(raw_content)
                return {
                    "status": "success",
                    "content": content,
                    "model": model,
                    "provider": self.provider,
                    "usage": data.get("usage", {})
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {res.status_code}: {res.text}"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _call_gemini_native(self, model: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Native Google Generative Language API call with robust token budgets and thought-part parsing."""
        clean_model = model.replace("models/", "")
        native_url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        # Ensure generous token budget for models with internal thinking tokens (Gemini 2.5/3.6)
        token_budget = max(max_tokens, 2048)
        
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Instructions: {system_prompt}\n\nUser Request: {user_prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": token_budget
            }
        }
        
        try:
            r = requests.post(native_url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    candidate = candidates[0]
                    content_obj = candidate.get("content", {})
                    parts = content_obj.get("parts", [])
                    
                    if parts and isinstance(parts, list):
                        # Filter out internal thinking/thought parts if present
                        non_thought_texts = [p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought", False) and p.get("text")]
                        if non_thought_texts:
                            extracted_text = "\n".join(non_thought_texts).strip()
                        else:
                            extracted_text = "\n".join([p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")]).strip()
                            
                        if extracted_text:
                            return {
                                "status": "success",
                                "content": extracted_text,
                                "model": clean_model,
                                "provider": "gemini"
                            }
                    
                    # Direct text fallback
                    if "text" in candidate and candidate["text"]:
                        return {
                            "status": "success",
                            "content": candidate["text"],
                            "model": clean_model,
                            "provider": "gemini"
                        }
                        
                # Check for block/safety reason
                feedback = data.get("promptFeedback", {})
                block_reason = feedback.get("blockReason")
                if block_reason:
                    return {
                        "status": "error",
                        "error": f"Gemini Safety Filter Block: {block_reason}"
                    }
                    
                finish_reason = candidates[0].get("finishReason") if candidates else "UNKNOWN"
                return {
                    "status": "error",
                    "error": f"Gemini finished with {finish_reason} (Token limit reached). Retrying with larger token allowance..."
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP {r.status_code}: {r.text}"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _fallback_generation(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Fallback when API key is not configured."""
        return {
            "status": "fallback",
            "model": "offline-rule-engine",
            "content": ""
        }
