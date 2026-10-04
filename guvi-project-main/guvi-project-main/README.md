# ⚖️ Contract Analysis Bot

An AI-powered legal contract review assistant built with **Streamlit**, **Google Gemini** (via the official `google-genai` SDK), **ChromaDB**, and **pypdf**.

Upload any contract PDF (NDAs, MSAs, vendor agreements, leases) and ask questions in natural language. The system retrieves the exact clauses using semantic vector search and provides:
1. **Verbatim clause quote with page citations**
2. **Plain English translation**
3. **Risk level (🟢 Low / 🟡 Medium / 🔴 High) with practical business justification**
4. **Anti-hallucination guardrail ("Not found in the contract" when missing)**
5. **1-Click 5-Pillar Comprehensive Risk Scorecard**

---

## 🏛️ The 5-Stage RAG Pipeline

```
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────────┐
│ 1. User Uploads │ ----> │ 2. Text Extraction &   │ ----> │ 3. Gemini Embeddings     │
│    Contract PDF │       │    Overlapping Chunks  │       │    (gemini-embedding-001)│
└─────────────────┘       │    (~800 chars, pypdf) │       └────────────┬─────────────┘
                          └────────────────────────┘                    │
                                                                        ▼
┌─────────────────┐       ┌────────────────────────┐       ┌──────────────────────────┐
│ 5. Gemini 2.5   │ <---- │ User Question + Top 4  │ <---- │ 4. ChromaDB Vector Store │
│    Risk Rating  │       │ Relevant Chunks        │       │    (Cosine Similarity)   │
└─────────────────┘       └────────────────────────┘       └──────────────────────────┘
```

1. **Document Ingestion**: The user uploads a contract PDF. Text is extracted page-by-page using `pypdf`.
2. **Clause-Aware Chunking**: Text is split into overlapping chunks (~800 characters, 150 character overlap) with boundary snapping to preserve complete clauses and sentence structure. Page numbers are captured as metadata.
3. **Vector Embeddings**: Each chunk is embedded into a dense 3072-dimensional semantic vector using Google's `gemini-embedding-001` via the `google-genai` SDK.
4. **Vector Storage**: Embeddings and metadata are indexed in an in-memory / local ChromaDB collection using cosine similarity.
5. **Retrieval & Grounded Reasoning**: When a question is asked (e.g. *"Is there a termination clause?"*), ChromaDB retrieves the top 4 most relevant chunks. Gemini analyzes them using a strictly grounded prompt to quote verbatim text, explain in plain English, and score legal risk.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.11)
- A Gemini API Key ([Get a free key from Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Installation

Clone or open the project folder in your terminal:

```bash
cd C:\Users\admin\.gemini\antigravity\scratch\contract-analysis-bot
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure Your API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Open `.env` and add your API key:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

*(Note: You can also enter or override your API key directly in the Streamlit sidebar UI).*

### 4. Launch the App

```bash
streamlit run app.py
```
*(Or on Windows if `streamlit` is not in your PATH: `python -m streamlit run app.py`)*

The web app will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing with the Built-In Sample Contract

A realistic **Master Professional Services Agreement (MSA) & NDA** is included in `sample_contracts/sample_service_agreement.pdf`.

To test instantly:
1. Open the app in your browser.
2. In the sidebar, click **"📑 Load Sample Service Agreement"**.
3. Try any of the 3 demo queries below or click **"🚀 Run Comprehensive Risk Audit"** under the **Risk Scorecard** tab!

### 🎯 3 Demo Questions to Show Hackathon Judges:

| Query | Expected Risk | What to Look For |
| :--- | :---: | :--- |
| **"Is there a termination clause and what notice is required?"** | 🟡 **Medium** | Quoting Section 3 (14-day notice for Client, 60-day notice for Service Provider). Asymmetry creates moderate risk. |
| **"What is the liability cap and what damages are excluded?"** | 🔴 **High** | Quoting Section 6. Liability cap is limited to only 3 months of fees, and Service Provider indemnification is uncapped. Significant exposure! |
| **"What are the confidentiality obligations and survival period?"** | 🟢 **Low** | Quoting Section 4. Standard mutual confidentiality obligations surviving 5 years, with standard carve-outs. |
| **"Is there an international maritime shipping clause?"** | ⚪ **Not Found** | Prompt correctly states **"Not found in the contract"** without hallucinating! |

---

## 💡 Hackathon Cheatsheet & Presentation Tips

### Q: What are embeddings and why are they needed?
> **Answer**: *Embeddings convert unstructured text into multi-dimensional numerical vectors (768 dimensions in Gemini `text-embedding-004`). In this vector space, texts with similar meanings are close together. Unlike keyword search (which fails if the contract says "cancel" instead of "terminate"), embeddings capture semantic intent.*

### Q: Why does RAG reduce hallucination?
> **Answer**: *Standard LLMs generate text based solely on their internal training weights. In legal documents, this often leads to hallucinating terms that sound plausible but don't exist. RAG grounds the LLM strictly on retrieved excerpts and enforces that if the clause is missing, it outputs "Not found in the contract".*

### Q: Why use ChromaDB?
> **Answer**: *ChromaDB is a lightweight, embedded vector database. It requires zero server setup, runs completely in-memory or persisted locally, supports HNSW vector indexing, and integrates seamlessly with Python.*

---

## 📁 Project Structure

```
contract-analysis-bot/
├── app.py                     # Streamlit frontend & interactive dashboard
├── rag_pipeline.py            # Extraction, chunking, embeddings, ChromaDB, & Gemini analysis
├── generate_sample_pdf.py     # Script to generate realistic sample MSA & NDA contract
├── sample_contracts/
│   └── sample_service_agreement.pdf # Pre-built 3-page test agreement
├── requirements.txt           # Project dependencies
├── .env.example               # Template for environment variables
├── .gitignore                 # Prevents committing API keys
└── README.md                  # Documentation and pitch guide
```

---

## ⚠️ Legal Disclaimer
*This tool is an AI assistant intended solely for educational, informational, and triage purposes. It does not constitute formal legal advice. Always consult a qualified attorney for legal matters.*
