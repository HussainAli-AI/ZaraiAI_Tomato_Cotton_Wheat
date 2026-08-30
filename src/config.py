"""Configuration loader for ZaraiAI."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"
KB_DIR = BASE_DIR / "knowledge_base"
KB_RAW_DIR = KB_DIR / "raw"
KB_PROCESSED_DIR = KB_DIR / "processed"
CHROMA_DIR = BASE_DIR / "knowledge_base" / "chroma_db"
CONFIG_DIR = BASE_DIR / "config"
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

# Ensure directories exist
for directory in [
    RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR,
    KB_RAW_DIR, KB_PROCESSED_DIR, CHROMA_DIR,
    REPORTS_DIR, DOCS_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)

# Load Disease Taxonomy
TAXONOMY_PATH = CONFIG_DIR / "disease_taxonomy.yaml"

def load_disease_taxonomy():
    if not TAXONOMY_PATH.exists():
        raise FileNotFoundError(f"Taxonomy config not found at {TAXONOMY_PATH}")
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

TAXONOMY = load_disease_taxonomy()

# LLM & API settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "alibaba")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-plus")
ALIBABA_API_KEY = os.getenv("ALIBABA_API_KEY", "")
ALIBABA_BASE_URL = os.getenv("ALIBABA_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")

# Vision & Training Defaults
DEFAULT_IMG_SIZE = 224
DEFAULT_BATCH_SIZE = 32
DEFAULT_CONFIDENCE_THRESHOLD = 0.65  # Fallback threshold
