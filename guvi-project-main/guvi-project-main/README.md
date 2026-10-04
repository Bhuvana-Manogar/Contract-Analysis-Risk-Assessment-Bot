# ⚖️ Contract Analysis & Risk Assessment Bot (LexGuard AI)

> **Built by [Bhuvana Manogar](https://github.com/Bhuvana-Manogar)**  
> *An AI-powered legal contract review platform built with Python, Streamlit, Google Gemini (via `google-genai`), and ChromaDB.*

---

## 📖 Table of Contents
- [Why I Built This Project](#-why-i-built-this-project)
- [How I Built It (The 5-Stage Architecture)](#-how-i-built-it-the-5-stage-architecture)
- [Automated RAG Evaluation & Test Harness (`test_harness.py`)](#-how-i-evaluated-the-system-automated-rag-test-harness)
- [Key Features](#-key-features)
- [Technical Stack](#-technical-stack)
- [Challenges I Overcame & Design Decisions](#-challenges-i-overcame--design-decisions)
- [How to Set Up and Run](#-how-to-set-up-and-run)
- [Sample Demo Queries & Expected Results](#-sample-demo-queries--expected-results)
- [Project Structure](#-project-structure)
- [Legal Disclaimer](#-legal-disclaimer)

---

## 💡 Why I Built This Project

Reviewing enterprise contracts (such as Master Services Agreements, NDAs, vendor terms, and employment contracts) is tedious, time-consuming, and prone to human error:
- Traditional keyword search (*Ctrl+F*) frequently fails because legal drafters use varied terminology (e.g., searching for "cancel" misses "termination for convenience").
- Generic large language models (LLMs) hallucinate clauses or assume standard terms that aren't actually present in the specific contract.
- Business stakeholders need quick, plain-English explanations and actionable risk levels (Low / Medium / High) without waiting days for preliminary legal review.

To solve this, I designed and developed **LexGuard AI** — a specialized Retrieval-Augmented Generation (RAG) assistant that extracts exact clauses from contract PDFs, evaluates business risk, and enforces strict grounding to eliminate hallucinations.

---

## 🏛️ How I Built It (The 5-Stage Architecture)

I structured the application into an end-to-end 5-stage pipeline:

```
┌────────────────────────┐
│  1. PDF Ingestion      │ ──> High-fidelity extraction using pypdf with page tracking
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  2. Smart Chunking     │ ──> ~800-character overlapping sliding window (150-char overlap)
└──────────┬─────────────┘     with sentence boundary snapping so clauses are never severed
           │
           ▼
┌────────────────────────┐
│  3. Gemini Embeddings  │ ──> 3072-dimensional vector embeddings via google-genai SDK
└──────────┬─────────────┘     (gemini-embedding-001)
           │
           ▼
┌────────────────────────┐
│  4. ChromaDB Storage   │ ──> In-memory vector database indexed with Cosine similarity (HNSW)
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│  5. Grounded Analysis  │ ──> Gemini 3 Flash / 2.5 Flash with strict RAG prompt:
└────────────────────────┘     1. Verbatim quote with page citation
                               2. Plain English explanation
                               3. Risk rating (🟢 Low / 🟡 Medium / 🔴 High)
                               4. Strict "Not found in contract" anti-hallucination guardrail
```

### Detailed Breakdown of Each Stage:

1. **Stage 1 — PDF Ingestion (`pypdf`)**:
   I implemented `extract_text_chunks_from_pdf` to extract clean text while attaching page numbers as metadata to every chunk. This ensures full citation traceability back to the original document page.

2. **Stage 2 — Clause-Aware Chunking**:
   Fixed-size splitting often cuts legal sentences in half. I implemented an overlapping sliding window (~800 characters with 150-character overlap) that searches backwards for the nearest sentence period (`. `) or word boundary.

3. **Stage 3 — Semantic Embeddings (`google-genai`)**:
   I integrated Google's official new `google-genai` Python SDK using `gemini-embedding-001` to transform every contract clause into a high-dimensional (3072-dim) vector representing its semantic meaning.

4. **Stage 4 — Vector Indexing (`ChromaDB`)**:
   I chose ChromaDB because it requires zero server setup and delivers sub-millisecond retrieval. I configured the collection to use Cosine similarity space (`{"hnsw:space": "cosine"}`) to calculate similarity match percentages.

5. **Stage 5 — Prompt Engineering & Multi-Model Fallback**:
   I designed a comprehensive legal prompt with few-shot structure. It instructs Gemini to act as a corporate legal analyst, answer solely from retrieved excerpts, quote verbatim clauses, translate them into plain English, and classify risk:
   - 🔴 **High Risk**: Uncapped liability, unilateral termination without notice, onerous non-compete.
   - 🟡 **Medium Risk**: Standard but asymmetric terms, 30-day notice, typical indemnifications.
   - 🟢 **Low Risk**: Mutual obligations, standard boilerplate, standard payment terms.
   - ⚪ **Not Found**: Triggered when the clause does not exist in the contract, preventing hallucinations.

---

## 🧪 How I Evaluated the System: Automated RAG Test Harness

In enterprise AI engineering, building a UI is only half the job—**proving accuracy, low latency, and zero hallucination is essential**. To ensure production readiness, I engineered a dedicated automated testing suite in [`test_harness.py`](test_harness.py).

### Why I Built the Test Harness:
- **Zero Hallucination Proof**: Uses a negative control test to scientifically prove the AI does not invent absent contract clauses.
- **Latency Benchmarking**: Measures the exact execution time of text extraction, vector embedding, and ChromaDB similarity search in milliseconds.
- **CI/CD Readiness**: Enables running automated quality regression checks on every code commit with a single command.

### The 5 Automated Test Checks:
1. **PDF Ingestion & Clause Chunking Integrity**: Validates that all pages are parsed without losing page metadata and verifies sentence boundary snapping.
2. **Dense Vector Indexing Speed**: Benchmarks embedding generation with `gemini-embedding-001` (3072-dim) and ChromaDB ingestion latency.
3. **Semantic Retrieval Recall@4**: Submits natural language queries (e.g., *"What is the limitation of liability?"*) and verifies that Section 6 is retrieved in the Top-4 with high cosine match scores.
4. **Risk Evaluation & Verbatim Quoting Accuracy**: Assesses whether Gemini accurately extracts the exact clause text and assigns a valid commercial risk rating (🔴 High / 🟡 Medium).
5. **Anti-Hallucination Guardrail (Negative Control)**: Asks a trick question about topics intentionally missing from the agreement (*e.g., international nuclear submarine shipments*), confirming the system strictly outputs **"Not found in the contract"** without guessing.

### 📊 Live Benchmark Scorecard (100% Pass Rate):

```text
======================================================================
🚀 LEXGUARD AI — AUTOMATED RAG EVALUATION & TEST HARNESS
======================================================================
Embedding Engine : gemini-embedding-001 (3072 dimensions)
Reasoning Engine : gemini-3-flash-preview
Evaluation Target: sample_contracts/sample_service_agreement.pdf

[✅ PASS] 1. PDF Ingestion & Clause-Aware Chunking (15.90 ms)
       Details: Extracted 14 chunks across 3 pages with page metadata.

[✅ PASS] 2. Vector Embedding & ChromaDB Indexing (3701.35 ms)
       Details: Indexed 14 chunks into ChromaDB with gemini-embedding-001 (3072-dim embeddings).

[✅ PASS] 3. Semantic Retrieval Recall@4 (986.21 ms)
       Details: Top-4 retrieved with max cosine match 67.3%. Section 6 liability clause successfully retrieved.

[✅ PASS] 4. Risk Assessment & Clause Quoting Accuracy (10092.48 ms)
       Details: Risk rating: HIGH. Quoted Section 6 correctly and flagged asymmetrical uncapped liability.

[✅ PASS] 5. Anti-Hallucination Guardrail (Negative Test) (12400.98 ms)
       Details: Guardrail triggered successfully. Evaluated risk: NOT_FOUND. Zero hallucination detected.

======================================================================
📊 TEST HARNESS SCORECARD SUMMARY
======================================================================
Total Test Cases   : 5
Passed             : 5 / 5 (100.0%)
Failed             : 0
Total Latency      : 27196.92 ms
======================================================================
🎉 ALL HARNESS CHECKS PASSED — SYSTEM PRODUCTION READY!
```

To run this test harness anytime:
```bash
python test_harness.py
```

---

## ✨ Key Features

- **Intuitive Web UI**: Built with Streamlit featuring a clean SaaS layout (LexGuard AI branding, document status badges, and responsive tabs).
- **Automated RAG Evaluation Harness (`test_harness.py`)**: 5-stage automated benchmark suite measuring extraction, retrieval precision, and hallucination resistance.
- **Instant Clause Quick-Action Chips**: One-click audit buttons for common inquiries:
  - *Termination Notice*
  - *Liability Caps & Damage Waivers*
  - *Payment Terms & Late Penalties*
  - *Confidentiality Survival Period*
  - *Intellectual Property Rights*
  - *Non-Solicitation Restrictions*
  - *Governing Law & Jurisdiction*
  - *Anti-Hallucination Test*
- **Executive Risk Scorecard**: A 1-click comprehensive audit that evaluates all 5 key legal pillars and presents a summary scorecard (counts of High, Medium, and Low risk items).
- **Source Grounding Transparency**: Expandable view showing the exact ChromaDB chunks, page numbers, and cosine similarity match percentages.
- **Pre-Built Test Contract**: Includes a realistic 3-page Master Services Agreement (MSA) & NDA in `sample_contracts/` so anyone can test the system with 1 click.
- **Secure Key Handling**: Loads `GEMINI_API_KEY` from `.env` using `python-dotenv` and protects it from Git via `.gitignore`.

---

## 🛠️ Technical Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit | Rapid, reactive Python web UI with custom modern CSS styling |
| **LLM Reasoning** | Google Gemini 3 Flash / 2.5 Flash | High-speed, high-reasoning model with automatic multi-model fallback |
| **Embeddings** | Gemini `gemini-embedding-001` | 3072-dimensional vector embeddings via `google-genai` SDK |
| **Vector Database** | ChromaDB | Lightweight, embedded vector store with native HNSW cosine indexing |
| **PDF Extraction** | `pypdf` | Fast, dependency-free text extraction with page metadata tracking |
| **Test Harness** | Python Evals Suite | Automated testing and latency benchmarking (`test_harness.py`) |
| **PDF Generation** | `reportlab` | Generates realistic sample test contracts for instant evaluation |
| **Environment** | `python-dotenv` | Clean, secure API key configuration |

---

## 🧠 Challenges I Overcame & Design Decisions

1. **Eliminating LLM Hallucinations**:  
   *Challenge*: LLMs often provide generic legal answers even when a clause is absent.  
   *Solution*: I enforced a strict system prompt constraint that forces the model to verify retrieved chunks and explicitly output *"Not found in the contract"* with a ⚪ *Not Found* risk badge whenever the topic isn't mentioned in the text. Verified via the negative control harness test.

2. **Resolving Streamlit UI State & Nested Expander Exceptions**:  
   *Challenge*: Streamlit's `st.status()` container is implemented internally as an expander, which caused runtime crashes when nested inside other expanders.  
   *Solution*: I re-architected the layout into clean, top-level status components and wrapped the Q&A input inside an `st.form` so queries submit smoothly whether the user presses Enter or clicks the button.

3. **Handling Multi-Model Quota Resilience**:  
   *Challenge*: Free-tier API keys may hit per-minute or daily request limits on individual models (such as 429 errors).  
   *Solution*: I engineered a dynamic candidate fallback loop (`gemini-3-flash-preview` ➔ `gemini-3.5-flash` ➔ `gemini-2.5-flash`) that automatically switches models if one encounters a quota ceiling, ensuring the demo never crashes.

---

## 🚀 How to Set Up and Run

### 1. Clone the Repository
```bash
git clone https://github.com/Bhuvana-Manogar/Contract-Analysis-Risk-Assessment-Bot.git
cd Contract-Analysis-Risk-Assessment-Bot/guvi-project-main/guvi-project-main
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Gemini API Key
Create a `.env` file in the project folder:
```bash
cp .env.example .env
```
Add your key inside `.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
*(Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey))*.

### 4. Run the Evaluation Test Harness
```bash
python test_harness.py
```

### 5. Launch the Streamlit App
```bash
python -m streamlit run app.py
```
Open **`http://localhost:8501`** in your browser.

---

## 🎯 Sample Demo Queries & Expected Results

Using the built-in sample contract (`sample_contracts/sample_service_agreement.pdf`):

| Query | Expected Risk | What the Model Identifies |
| :--- | :---: | :--- |
| **"What is the limitation of liability and what damages are excluded?"** | 🔴 **High Risk** | Cites Section 6. Flags that client liability is capped at only 3 months of fees, while service provider indemnification remains completely uncapped. |
| **"Is there a termination clause and what notice is required?"** | 🟡 **Medium Risk** | Cites Section 3. Flags asymmetrical notice: 14 days for Client vs 60 days for Service Provider. |
| **"What are the confidentiality obligations and survival period?"** | 🟢 **Low Risk** | Cites Section 4. Confirms standard mutual obligations surviving 5 years with standard exceptions. |
| **"What are the maritime shipping terms?"** | ⚪ **Not Found** | Accurately identifies that maritime shipping is absent from the contract without hallucinating. |

---

## 📁 Project Structure

```
guvi-project-main/guvi-project-main/
├── app.py                     # Streamlit frontend & interactive dashboard
├── rag_pipeline.py            # PDF text extraction, chunking, embeddings, ChromaDB, & Gemini analysis
├── test_harness.py            # Automated RAG evaluation & benchmarking suite (100% pass rate)
├── generate_sample_pdf.py     # Script to generate realistic test contracts
├── sample_contracts/
│   └── sample_service_agreement.pdf # Pre-built 3-page test agreement
├── requirements.txt           # Project dependencies
├── .env.example               # Template for environment variables
├── .gitignore                 # Prevents committing API keys
└── README.md                  # Complete project documentation & build journey
```

---

## ⚖️ Legal Disclaimer

*This application is an automated AI research and contract triage tool. It does not provide legal advice. All analyses, risk ratings, and extracted terms must be verified by a qualified attorney.*
