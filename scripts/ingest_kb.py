"""Ingestion pipeline to index all raw agricultural documents into vector store."""
import sys
from pathlib import Path
import json
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.rag.chunking import DocumentChunker
from src.rag.embeddings import MultilingualEmbedder
from src.rag.retriever import AgriculturalRetriever
from src.config import KB_DIR, KB_RAW_DIR, KB_PROCESSED_DIR

def ingest_knowledge_base():
    print("Starting Knowledge Base Ingestion Pipeline...")
    manifest_path = KB_DIR / "source_manifest.csv"
    
    if not manifest_path.exists():
        print(f"[ERROR] Source manifest not found at {manifest_path}. Run scripts/download_kb.py first.")
        return
        
    manifest_df = pd.read_csv(manifest_path)
    print(f"Found {len(manifest_df)} registered documents in source manifest.")
    
    chunker = DocumentChunker(target_chunk_size=500, chunk_overlap=80)
    embedder = MultilingualEmbedder()
    all_chunks = []
    
    for _, row in manifest_df.iterrows():
        file_path = KB_DIR.parent / row["local_path"]
        if not file_path.exists():
            print(f"[WARNING] Document file missing: {file_path}")
            continue
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        doc_metadata = {
            "source_id": row["source_id"],
            "document_title": row["title"],
            "crop": row["crop"],
            "publisher": row["publisher"],
            "country": row["country"],
            "year": int(row["year"]),
            "language": row["language"],
            "authority_level": row["authority_level"],
            "source_url": row["source_url"]
        }
        
        chunks = chunker.chunk_document(content, doc_metadata)
        print(f"  Processed '{row['title'][:40]}...' -> {len(chunks)} semantic chunks")
        all_chunks.extend(chunks)
        
    print(f"\nTotal generated chunks across all documents: {len(all_chunks)}")
    
    # Compute embeddings
    print("Computing multilingual embeddings for all chunks...")
    chunk_texts = [c["content"] for c in all_chunks]
    embeddings = embedder.embed_texts(chunk_texts)
    
    # Save into index
    retriever = AgriculturalRetriever(embedder=embedder)
    retriever.save_index(all_chunks, embeddings)
    print("Knowledge base ingestion complete.")

if __name__ == "__main__":
    ingest_knowledge_base()
