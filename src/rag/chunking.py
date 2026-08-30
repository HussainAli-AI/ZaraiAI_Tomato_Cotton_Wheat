"""Semantic and heading-aware chunking pipeline for agricultural documents in ZaraiAI."""
import re
from pathlib import Path
from typing import List, Dict, Any

class DocumentChunker:
    """
    Structure-preserving chunker for agricultural manuals and decision guides.
    Maintains section headers, symptom lists, and treatment instructions intact.
    """
    def __init__(self, target_chunk_size=700, chunk_overlap=100):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split document text into semantic chunks with attached metadata.
        """
        chunks = []
        
        # Split by major sections (numbered sections or double newlines)
        sections = re.split(r'\n(?=[0-9]+\.\s+[A-Z\s]+:|\n[A-Z\s]{4,}:)', text)
        
        chunk_index = 0
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
                
            # If section is small enough, keep as single chunk
            words = sec_clean.split()
            if len(words) <= self.target_chunk_size:
                # Extract section title from first line
                first_line = sec_clean.split("\n")[0].strip()
                chunk_meta = metadata.copy()
                chunk_meta.update({
                    "chunk_id": f"{metadata.get('source_id', 'doc')}_{chunk_index}",
                    "section_title": first_line[:120],
                    "word_count": len(words)
                })
                chunks.append({
                    "content": sec_clean,
                    "metadata": chunk_meta
                })
                chunk_index += 1
            else:
                # Split large section into overlapping windows
                start = 0
                while start < len(words):
                    end = min(start + self.target_chunk_size, len(words))
                    sub_text = " ".join(words[start:end])
                    
                    first_line = sec_clean.split("\n")[0].strip()
                    chunk_meta = metadata.copy()
                    chunk_meta.update({
                        "chunk_id": f"{metadata.get('source_id', 'doc')}_{chunk_index}",
                        "section_title": f"{first_line[:100]} (Part {chunk_index + 1})",
                        "word_count": len(words[start:end])
                    })
                    chunks.append({
                        "content": sub_text,
                        "metadata": chunk_meta
                    })
                    chunk_index += 1
                    
                    if end == len(words):
                        break
                    start += (self.target_chunk_size - self.chunk_overlap)
                    
        return chunks
