"""Unit Tests for Agricultural Knowledge Retrieval and Citations."""
import sys
from pathlib import Path
import pytest

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.rag.retriever import AgriculturalRetriever
from src.rag.citations import format_citations, build_evidence_context

def test_rag_retriever_crop_filtering():
    """Verify retriever correctly isolates documents by target crop."""
    retriever = AgriculturalRetriever()
    
    # Query for tomato disease
    tomato_chunks = retriever.retrieve("Early blight target spots Mancozeb spray", crop="tomato", top_k=3)
    assert len(tomato_chunks) > 0, "Expected to retrieve tomato evidence chunks"
    for c in tomato_chunks:
        assert c["metadata"]["crop"].lower() in ["tomato", "general"]

def test_citations_formatting():
    """Verify citations retain document titles and authority tiers."""
    retriever = AgriculturalRetriever()
    chunks = retriever.retrieve("Cotton Leaf Curl Virus Whitefly vector CCRI Multan", crop="cotton", top_k=2)
    citations = format_citations(chunks)
    
    assert len(citations) > 0
    cit = citations[0]
    assert "title" in cit
    assert "publisher" in cit
    assert "authority_level" in cit
    assert "Tier 1" in cit["authority_level"]
