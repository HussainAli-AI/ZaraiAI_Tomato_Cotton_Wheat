"""Citation formatting and evidence grounding for ZaraiAI."""
from typing import List, Dict, Any

def format_citations(retrieved_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format unique citations from retrieved knowledge chunks.
    """
    seen_sources = set()
    citations = []
    
    for chunk in retrieved_chunks:
        meta = chunk.get("metadata", {})
        source_id = meta.get("source_id", "unknown")
        
        if source_id not in seen_sources:
            seen_sources.add(source_id)
            citations.append({
                "source_id": source_id,
                "title": meta.get("document_title", meta.get("title", "Agricultural Advisory")),
                "publisher": meta.get("publisher", "Agricultural Extension Department"),
                "year": meta.get("year", 2025),
                "authority_level": meta.get("authority_level", "Tier 1 (Authoritative Extension)"),
                "section": meta.get("section_title", "General Guidance"),
                "url": meta.get("source_url", "")
            })
            
    return citations

def build_evidence_context(retrieved_chunks: List[Dict[str, Any]], max_chunks: int = 4) -> str:
    """
    Construct formatted context string for LLM prompting.
    """
    if not retrieved_chunks:
        return "No authoritative agricultural documents found for this query."
        
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks[:max_chunks], start=1):
        meta = chunk.get("metadata", {})
        title = meta.get("document_title", meta.get("title", "Document"))
        publisher = meta.get("publisher", "Government/Extension")
        section = meta.get("section_title", "Section")
        
        block = f"--- [EVIDENCE SOURCE {i}]: {title} ({publisher}) ---\n"
        block += f"Section: {section}\n"
        block += f"Content:\n{chunk['content'].strip()}\n"
        context_blocks.append(block)
        
    return "\n\n".join(context_blocks)
