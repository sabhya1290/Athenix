import os
import json
import faiss
import numpy as np
import fitz  # PyMuPDF
from typing import List, Dict, Any
import google.generativeai as genai
from utils.logger import get_logger

logger = get_logger("RAGService")

# Directories
UPLOADS_DIR = "uploads"
VECTOR_DB_DIR = "vector_db"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(VECTOR_DB_DIR, exist_ok=True)

# Configure API Key
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF file using PyMuPDF."""
    logger.info(f"Extracting text from PDF: {pdf_path}")
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {pdf_path}: {str(e)}")
        raise e
    return text

def split_text_into_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Splits text into overlapping chunks of a given character size."""
    logger.info("Splitting text into chunks...")
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap
    logger.info(f"Generated {len(chunks)} chunks.")
    return chunks

from sentence_transformers import SentenceTransformer

# Initialize SentenceTransformer local model (satisfies HuggingFace + Sentence Transformers)
logger.info("Initializing SentenceTransformer('all-MiniLM-L6-v2')...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
logger.info("SentenceTransformer model loaded.")

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generates embeddings for a list of texts using SentenceTransformer all-MiniLM-L6-v2."""
    logger.info(f"Generating local embeddings for {len(texts)} chunks using all-MiniLM-L6-v2...")
    try:
        # Encode returns a numpy array or list of lists
        embeddings = embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Failed to generate SentenceTransformer embeddings: {str(e)}")
        raise e

def build_faiss_index(doc_id: str, chunks: List[str], embeddings: List[List[float]]):
    """Builds and saves a FAISS index and chunk mappings for a doc_id."""
    logger.info(f"Building FAISS index for document: {doc_id}")
    
    # Dimension of all-MiniLM-L6-v2 is 384
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    
    # Convert embeddings to numpy array
    embeddings_np = np.array(embeddings).astype("float32")
    index.add(embeddings_np)
    
    # Paths
    index_path = os.path.join(VECTOR_DB_DIR, f"{doc_id}.index")
    mapping_path = os.path.join(VECTOR_DB_DIR, f"{doc_id}.json")
    
    # Write FAISS index
    faiss.write_index(index, index_path)
    
    # Write chunks mapping
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
        
    logger.info(f"FAISS index and chunks mapping successfully saved for doc: {doc_id}")

def retrieve_relevant_chunks(doc_id: str, query: str, k: int = 3) -> List[str]:
    """Retrieves top k relevant chunks from FAISS index matching the query."""
    logger.info(f"Retrieving top {k} relevant chunks for query: '{query}' in doc: {doc_id}")
    
    index_path = os.path.join(VECTOR_DB_DIR, f"{doc_id}.index")
    mapping_path = os.path.join(VECTOR_DB_DIR, f"{doc_id}.json")
    
    if not os.path.exists(index_path) or not os.path.exists(mapping_path):
        raise FileNotFoundError(f"FAISS Index or Chunk mapping not found for doc: {doc_id}")
        
    # Read FAISS Index
    index = faiss.read_index(index_path)
    
    # Read Chunks Mapping
    with open(mapping_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    try:
        query_emb = embedding_model.encode([query], show_progress_bar=False)[0]
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {str(e)}")
        raise e
        
    # Search in FAISS
    query_np = np.array([query_emb]).astype("float32")
    distances, indices = index.search(query_np, k)
    
    retrieved_chunks = []
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            retrieved_chunks.append(chunks[idx])
            
    logger.info(f"Retrieved {len(retrieved_chunks)} relevant chunks.")
    return retrieved_chunks
