"""
RAG Pipeline Module for Contract Analysis Bot
Handles PDF text extraction, chunking, embeddings with google-genai,
vector indexing with ChromaDB, and legal clause risk analysis with Gemini.
"""

import os
import re
import time
import warnings
from typing import List, Dict, Any, Optional

warnings.filterwarnings("ignore")

from pypdf import PdfReader
import chromadb
from google import genai
from google.genai import types

DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_GENAI_MODEL = "gemini-3-flash-preview"
FALLBACK_GENAI_MODELS = ["gemini-3-flash-preview", "gemini-3.5-flash", "gemini-2.5-flash"]
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def extract_text_chunks_from_pdf(
    file_or_path, 
    chunk_size: int = CHUNK_SIZE, 
    chunk_overlap: int = CHUNK_OVERLAP
) -> List[Dict[str, Any]]:
    """
    Extracts text from a PDF file and splits it into overlapping chunks with page metadata.
    Supports file paths, BytesIO, or Streamlit UploadedFile objects.
    """
    reader = PdfReader(file_or_path)
    total_pages = len(reader.pages)
    
    chunks = []
    chunk_counter = 0
    
    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        cleaned_text = re.sub(r'\r\n', '\n', raw_text)
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text).strip()
        
        if not cleaned_text:
            continue
            
        start = 0
        text_len = len(cleaned_text)
        
        while start < text_len:
            end = min(start + chunk_size, text_len)
            
            # Snap to sentence or word boundary if not at end
            if end < text_len:
                boundary = cleaned_text.rfind('. ', start + chunk_size // 2, end)
                if boundary != -1:
                    end = boundary + 1
                else:
                    space_boundary = cleaned_text.rfind(' ', start + chunk_size // 2, end)
                    if space_boundary != -1:
                        end = space_boundary
            
            chunk_content = cleaned_text[start:end].strip()
            if len(chunk_content) > 25:
                chunk_counter += 1
                chunks.append({
                    "id": f"chunk_{chunk_counter}",
                    "text": chunk_content,
                    "metadata": {
                        "chunk_id": chunk_counter,
                        "page_number": page_num,
                        "total_pages": total_pages,
                        "char_length": len(chunk_content)
                    }
                })
            
            if end >= text_len:
                break
            start = max(start + 1, end - chunk_overlap)
            
    return chunks


class ContractVectorStore:
    """
    Manages embedding generation via google-genai and vector indexing via ChromaDB.
    """
    def __init__(self, api_key: str, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.client = genai.Client(api_key=api_key)
        self.chroma_client = chromadb.EphemeralClient()
        self.collection = None
        self.collection_name = f"contracts_{int(time.time() * 1000)}"

    def embed_texts(self, texts: List[str], batch_size: int = 25) -> List[List[float]]:
        """
        Embeds a list of texts using Gemini's embedding model.
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.models.embed_content(
                model=self.embedding_model,
                contents=batch,
            )
            for emb in response.embeddings:
                embeddings.append(emb.values)
        return embeddings

    def embed_single_query(self, query: str) -> List[float]:
        """
        Embeds a single query string for vector similarity retrieval.
        """
        response = self.client.models.embed_content(
            model=self.embedding_model,
            contents=query,
        )
        return response.embeddings[0].values

    def build_index(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Computes embeddings for all chunks and inserts them into ChromaDB.
        """
        if not chunks:
            return 0
            
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        embeddings = self.embed_texts(texts)
        
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant chunks using cosine similarity.
        """
        if not self.collection:
            raise ValueError("Vector collection has not been initialized.")
            
        query_embedding = self.embed_single_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        retrieved_items = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                similarity = max(0.0, 1.0 - dist)
                retrieved_items.append({
                    "text": doc,
                    "metadata": meta,
                    "similarity": round(similarity * 100, 1)
                })
        return retrieved_items


def format_context_for_prompt(retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Formats retrieved chunks with citations for Gemini prompt."""
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        page = chunk.get("metadata", {}).get("page_number", "Unknown")
        context_blocks.append(
            f"--- EXCERPT {i} (Page {page}) ---\n{chunk['text']}"
        )
    return "\n\n".join(context_blocks)


def parse_ai_response(raw_text: str) -> Dict[str, Any]:
    """Parses markdown sections from Gemini's response into structured fields."""
    quote = ""
    explanation = ""
    risk_level = "LOW"
    risk_reason = ""
    recommendation = ""
    
    upper_text = raw_text.upper()
    if "🔴 HIGH" in raw_text or "RISK LEVEL**: HIGH" in upper_text or "RISK LEVEL**: 🔴 HIGH" in upper_text or "RISK LEVEL: HIGH" in upper_text:
        risk_level = "HIGH"
    elif "🟡 MEDIUM" in raw_text or "RISK LEVEL**: MEDIUM" in upper_text or "RISK LEVEL**: 🟡 MEDIUM" in upper_text or "RISK LEVEL: MEDIUM" in upper_text:
        risk_level = "MEDIUM"
    elif "⚪ NOT FOUND" in raw_text or "NOT FOUND IN THE CONTRACT" in upper_text or "NOT FOUND" in upper_text:
        risk_level = "NOT_FOUND"
    elif "🟢 LOW" in raw_text or "RISK LEVEL**: LOW" in upper_text or "RISK LEVEL**: 🟢 LOW" in upper_text or "RISK LEVEL: LOW" in upper_text:
        risk_level = "LOW"

    q_match = re.search(r'### 1\. Quoted Clause\s*(.*?)(?=### 2|$)', raw_text, re.DOTALL | re.IGNORECASE)
    if q_match:
        quote = q_match.group(1).strip()
        
    e_match = re.search(r'### 2\. Plain English Explanation\s*(.*?)(?=### 3|$)', raw_text, re.DOTALL | re.IGNORECASE)
    if e_match:
        explanation = e_match.group(1).strip()
        
    r_match = re.search(r'### 3\. Risk Assessment\s*(.*?)(?=### 4|$)', raw_text, re.DOTALL | re.IGNORECASE)
    if r_match:
        risk_reason = r_match.group(1).strip()
        
    rec_match = re.search(r'### 4\. Key Takeaways & Recommendations\s*(.*?)$', raw_text, re.DOTALL | re.IGNORECASE)
    if rec_match:
        recommendation = rec_match.group(1).strip()

    return {
        "quote": quote,
        "explanation": explanation,
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "recommendation": recommendation
    }


def analyze_clause_with_gemini(
    query: str,
    retrieved_chunks: List[Dict[str, Any]],
    api_key: str,
    model_name: str = DEFAULT_GENAI_MODEL
) -> Dict[str, Any]:
    """
    Sends retrieved contract context and query to Gemini with grounded legal prompt.
    Returns parsed structured result and raw response.
    """
    client = genai.Client(api_key=api_key)
    context_text = format_context_for_prompt(retrieved_chunks)

    prompt = f"""You are an elite corporate legal analyst AI assisting an executive in reviewing a contract.
Analyze the following retrieved contract excerpts to answer the inquiry with strict precision.

=== RETRIEVED CONTRACT CONTEXT ===
{context_text}
=== END OF CONTEXT ===

USER QUESTION:
"{query}"

RULES:
1. Grounding: Answer strictly using the contract excerpts above. Do NOT assume terms not stated.
2. If the excerpts do not contain the answer or no relevant clause is present, state "Not found in the contract" for Quoted Clause, explain that the uploaded excerpts do not contain this clause, and set Risk Level to "⚪ Not Found".
3. Evaluate risk from the perspective of the client / signing counterparty.
4. Output your response using the EXACT markdown structure below:

### 1. Quoted Clause
> "[Verbatim quote from the excerpt, or 'Not found in the contract']"
*(Page citation)*

### 2. Plain English Explanation
[Provide a clear, simple breakdown of what this clause means. Explain obligations, deadlines, or triggers.]

### 3. Risk Assessment
- **Risk Level**: [🟢 Low | 🟡 Medium | 🔴 High | ⚪ Not Found]
- **Reason**: [Explain the practical business or legal exposure.]

### 4. Key Takeaways & Recommendations
[Actionable negotiation advice or redline point.]

---
EXAMPLE FORMAT:
### 1. Quoted Clause
> "Either party may terminate this Agreement without cause upon thirty (30) days prior written notice." (Page 1)

### 2. Plain English Explanation
Either party may cancel the contract at any time for any reason by providing 30 days written notice.

### 3. Risk Assessment
- **Risk Level**: 🟡 Medium
- **Reason**: 30-day termination for convenience is standard, but check if work-in-progress fees are reimbursed.

### 4. Key Takeaways & Recommendations
- Confirm prorated payment applies for work done prior to termination.
"""

    candidate_models = [model_name] + [m for m in FALLBACK_GENAI_MODELS if m != model_name]
    raw_text = ""
    last_err = None
    for candidate in candidate_models:
        try:
            chat = client.chats.create(model=candidate)
            response = chat.send_message(prompt)
            raw_text = response.text or ""
            if raw_text:
                break
        except Exception as err:
            last_err = err
            continue

    if not raw_text and last_err:
        raise last_err

    parsed = parse_ai_response(raw_text)

    return {
        "query": query,
        "risk_level": parsed["risk_level"],
        "quote": parsed["quote"],
        "explanation": parsed["explanation"],
        "risk_reason": parsed["risk_reason"],
        "recommendation": parsed["recommendation"],
        "raw_response": raw_text,
        "retrieved_chunks": retrieved_chunks
    }


def generate_contract_risk_scorecard(
    vector_store: ContractVectorStore,
    api_key: str,
    model_name: str = DEFAULT_GENAI_MODEL
) -> List[Dict[str, Any]]:
    """
    Automated scan across 5 critical contract pillars:
    - Termination & Notice
    - Limitation of Liability & Caps
    - Payment Terms & Late Penalties
    - Confidentiality & Trade Secrets
    - IP Rights & Restrictive Covenants
    """
    key_pillars = [
        {"category": "Termination & Notice", "query": "What are the termination terms, notice period, and termination for convenience?"},
        {"category": "Liability & Indemnity", "query": "What is the limitation of liability, liability cap, consequential damages waiver, and indemnification?"},
        {"category": "Payment Terms & Penalties", "query": "What are the payment deadlines, invoicing schedules, and late payment interest or fees?"},
        {"category": "Confidentiality & Trade Secrets", "query": "What are the confidentiality obligations, exclusions, and how long does confidentiality survive?"},
        {"category": "IP Rights & Restrictive Covenants", "query": "Who owns intellectual property and work product, and is there a non-compete or non-solicitation clause?"}
    ]

    scorecard = []
    for pillar in key_pillars:
        chunks = vector_store.retrieve(pillar["query"], top_k=4)
        analysis = analyze_clause_with_gemini(
            query=pillar["query"],
            retrieved_chunks=chunks,
            api_key=api_key,
            model_name=model_name
        )
        scorecard.append({
            "category": pillar["category"],
            "query": pillar["query"],
            "risk_level": analysis["risk_level"],
            "quote": analysis["quote"],
            "explanation": analysis["explanation"],
            "risk_reason": analysis["risk_reason"],
            "recommendation": analysis["recommendation"],
            "raw_response": analysis["raw_response"],
            "retrieved_chunks": chunks
        })
    return scorecard
