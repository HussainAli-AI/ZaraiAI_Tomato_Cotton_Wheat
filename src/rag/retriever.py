"""Agricultural RAG Vector Store and Retriever for ZaraiAI."""
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from src.rag.embeddings import MultilingualEmbedder
from src.config import KB_DIR, KB_PROCESSED_DIR

class AgriculturalRetriever:
    """
    Multilingual semantic search engine with metadata filtering by crop.
    Retains full document provenance, page/section headers, and authority tiers.
    """
    def __init__(self, index_path=None, embedder=None):
        self.index_path = Path(index_path) if index_path else KB_PROCESSED_DIR / "rag_index.json"
        self.embedder = embedder or MultilingualEmbedder()
        self.documents = []
        self.embeddings = None
        
        self.load_index()
        
    def load_index(self):
        """Load indexed chunks and embeddings from storage."""
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.documents = data.get("documents", [])
                raw_emb = data.get("embeddings", [])
                if raw_emb:
                    self.embeddings = np.array(raw_emb, dtype=np.float32)
            print(f"Loaded {len(self.documents)} knowledge chunks from {self.index_path}")
        else:
            print(f"[NOTE] RAG index not found at {self.index_path}. Build index via ingest_kb.py.")
            
    def save_index(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Save chunked documents and embeddings."""
        self.documents = documents
        self.embeddings = np.array(embeddings, dtype=np.float32)
        
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump({
                "documents": self.documents,
                "embeddings": embeddings
            }, f, indent=2)
        print(f"Saved RAG index with {len(self.documents)} chunks to {self.index_path}")

    def retrieve(self, query: str, crop: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant agricultural evidence chunks for a query.
        Filters by crop if provided.
        """
        if not self.documents or self.embeddings is None:
            return []
            
        query_emb = np.array(self.embedder.embed_query(query), dtype=np.float32)
        
        # Calculate cosine similarities
        dot_products = np.dot(self.embeddings, query_emb)
        doc_norms = np.linalg.norm(self.embeddings, axis=1)
        query_norm = np.linalg.norm(query_emb)
        
        if query_norm > 0:
            similarities = dot_products / (doc_norms * query_norm + 1e-8)
        else:
            similarities = np.zeros(len(self.documents))
            
        # Filter and rank
        scored_results = []
        for idx, (doc, score) in enumerate(zip(self.documents, similarities)):
            doc_crop = doc.get("metadata", {}).get("crop", "").lower()
            
            # Filter by crop if specified
            if crop and doc_crop and (crop.lower() != doc_crop) and (doc_crop != "general"):
                continue
                
            scored_results.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": float(score)
            })
            
        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_results[:top_k]
