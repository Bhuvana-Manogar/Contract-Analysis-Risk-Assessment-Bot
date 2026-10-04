"""
LexGuard AI - Contract Analysis Platform
Enterprise-grade legal contract review, semantic vector search with ChromaDB,
and clause risk evaluation powered by Google Gemini.
"""

import os
import io
import time
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

from rag_pipeline import (
    extract_text_chunks_from_pdf,
    ContractVectorStore,
    analyze_clause_with_gemini,
    generate_contract_risk_scorecard,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_GENAI_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

# Page configuration
st.set_page_config(
    page_title="LexGuard AI | Contract Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Enterprise Modern UI Styling
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Header Bar */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.6rem 0 1.2rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 1.2rem;
    }
    .brand-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-tagline {
        font-size: 0.92rem;
        color: #64748b;
        margin-top: 2px;
    }
    .compliance-pill {
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
    }
    
    /* Disclaimer Bar */
    .disclaimer-bar {
        background: linear-gradient(90deg, #f8fafc 0%, #f1f5f9 100%);
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0284c7;
        padding: 0.7rem 1rem;
        border-radius: 6px;
        font-size: 0.84rem;
        color: #334155;
        margin-bottom: 1.4rem;
    }
    
    /* Contract Status Bar */
    .status-panel {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        margin-bottom: 1.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .status-item {
        display: inline-block;
        margin-right: 2rem;
    }
    .status-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        font-weight: 600;
    }
    .status-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 2px;
    }
    
    /* Result Cards */
    .analysis-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .risk-banner-high {
        background: #fee2e2;
        border: 1px solid #f87171;
        color: #991b1b;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }
    .risk-banner-medium {
        background: #fef3c7;
        border: 1px solid #fcd34d;
        color: #92400e;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }
    .risk-banner-low {
        background: #dcfce7;
        border: 1px solid #86efac;
        color: #166534;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }
    .risk-banner-notfound {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #475569;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.95rem;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1rem;
    }
    
    .clause-quote-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #1e293b;
        margin: 1rem 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    .section-title {
        font-size: 0.88rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #475569;
        margin-top: 1.2rem;
        margin-bottom: 0.4rem;
    }
    
    .chunk-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        font-size: 0.88rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "current_doc_name" not in st.session_state:
    st.session_state.current_doc_name = None
if "doc_chunks" not in st.session_state:
    st.session_state.doc_chunks = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "scorecard_results" not in st.session_state:
    st.session_state.scorecard_results = None
if "active_query" not in st.session_state:
    st.session_state.active_query = ""


# Helper: Index a document safely
def index_document(file_bytes_or_path, doc_name: str, api_key: str):
    try:
        chunks = extract_text_chunks_from_pdf(
            file_bytes_or_path,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        if not chunks:
            st.error("No readable text could be extracted from this PDF. Please check if it contains selectable text.")
            return False

        v_store = ContractVectorStore(api_key=api_key, embedding_model=DEFAULT_EMBEDDING_MODEL)
        v_store.build_index(chunks)
        
        st.session_state.vector_store = v_store
        st.session_state.doc_chunks = chunks
        st.session_state.current_doc_name = doc_name
        st.session_state.scorecard_results = None
        st.session_state.chat_history = []
        return True
    except Exception as e:
        st.error(f"Error during contract indexing: {str(e)}")
        return False


# --- HEADER ---
st.markdown("""
<div class="brand-header">
    <div>
        <div class="brand-title">⚖️ LexGuard AI</div>
        <div class="brand-tagline">Enterprise Contract Risk Intelligence • Semantic Retrieval • Clause Grounding</div>
    </div>
    <div class="compliance-pill">
        🔒 Zero Data Retention • Gemini Grounded
    </div>
</div>
<div class="disclaimer-bar">
    🛡️ <b>Notice:</b> LexGuard AI provides automated legal triage and risk analysis. It does not replace professional legal counsel. Always consult a qualified attorney for legal decisions.
</div>
""", unsafe_allow_html=True)


# --- SIDEBAR (Settings & API Key) ---
with st.sidebar:
    st.header("⚙️ System Settings")
    
    # API Key Configuration
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key = st.text_input(
        "Gemini API Key",
        value=env_key,
        type="password",
        placeholder="Enter API Key...",
        help="Reads automatically from .env if configured."
    )
    
    if api_key:
        st.caption("✅ API Key active")
    else:
        st.warning("⚠️ Enter a Gemini API Key to run clause analysis.")
        
    st.markdown("---")
    st.subheader("🤖 Engine Parameters")
    st.caption(f"**Generation Model**: `{DEFAULT_GENAI_MODEL}`")
    st.caption(f"**Vector Embedding**: `{DEFAULT_EMBEDDING_MODEL}` (3072-dim)")
    st.caption(f"**Vector Database**: `ChromaDB HNSW`")
    
    top_k = st.slider("Top Chunks Retrieved", min_value=2, max_value=6, value=4, step=1)
    
    st.markdown("---")
    st.caption("LexGuard AI v2.4 Enterprise")


# --- STEP 1: DOCUMENT UPLOAD & INGESTION (Clean Card without Nested Expanders) ---
if st.session_state.vector_store is None:
    st.subheader("📄 Upload Contract Document")
    st.markdown("Upload any PDF agreement (NDA, MSA, Vendor Contract, Employment Agreement) to initiate automated clause parsing.")
    
    col_upload, col_demo = st.columns([3, 2])
    
    with col_upload:
        uploaded_pdf = st.file_uploader(
            "Choose a PDF Contract",
            type=["pdf"],
            help="Upload your contract PDF for vectorization."
        )
        
        if uploaded_pdf is not None:
            if not api_key:
                st.error("Please configure your Gemini API Key in the sidebar first.")
            else:
                with st.spinner(f"Indexing '{uploaded_pdf.name}' into ChromaDB with Gemini embeddings..."):
                    pdf_bytes = io.BytesIO(uploaded_pdf.read())
                    success = index_document(pdf_bytes, uploaded_pdf.name, api_key)
                    if success:
                        st.success(f"Successfully indexed '{uploaded_pdf.name}'!")
                        st.rerun()

    with col_demo:
        st.markdown("**Or test instantly with a pre-loaded agreement:**")
        sample_path = Path("sample_contracts/sample_service_agreement.pdf")
        if sample_path.exists():
            if st.button("📑 Load Sample Master Services Agreement (MSA)", type="secondary", use_container_width=True):
                if not api_key:
                    st.error("Please configure your Gemini API Key in the sidebar first.")
                else:
                    with st.spinner("Indexing Sample Services Agreement..."):
                        success = index_document(str(sample_path), "sample_service_agreement.pdf", api_key)
                        if success:
                            st.success("Sample contract loaded and indexed!")
                            st.rerun()

else:
    # --- ACTIVE DOCUMENT STATUS BAR ---
    pages = max([c["metadata"]["page_number"] for c in st.session_state.doc_chunks]) if st.session_state.doc_chunks else 1
    total_chunks = len(st.session_state.doc_chunks)
    
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns([3, 1, 1, 1.5])
    with col_stat1:
        st.markdown(f"**Active Contract**: 📑 `{st.session_state.current_doc_name}`")
    with col_stat2:
        st.markdown(f"**Pages**: `{pages}`")
    with col_stat3:
        st.markdown(f"**Clauses**: `{total_chunks}`")
    with col_stat4:
        if st.button("🔄 Upload New Contract", use_container_width=True):
            st.session_state.vector_store = None
            st.session_state.current_doc_name = None
            st.session_state.doc_chunks = []
            st.session_state.chat_history = []
            st.session_state.scorecard_results = None
            st.rerun()

    st.markdown("---")

    # --- MAIN FUNCTIONALITY TABS ---
    tab_qa, tab_audit, tab_library, tab_system = st.tabs([
        "🔍 Clause Intelligence & Q&A",
        "📊 Executive Risk Scorecard",
        "📑 Clause Library Explorer",
        "ℹ️ System Architecture"
    ])

    # =========================================================================
    # TAB 1: CLAUSE INTELLIGENCE & Q&A
    # =========================================================================
    with tab_qa:
        st.subheader("Contract Inquiry & Clause Risk Evaluation")
        st.markdown("Ask specific questions or click any standard clause pillar below for an instant audit:")

        # Quick Clause Action Chips
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        with col_q1:
            if st.button("🛑 Termination Notice", use_container_width=True):
                st.session_state.active_query = "What is the termination clause, notice period, and termination for convenience?"
        with col_q2:
            if st.button("🛡️ Liability Caps", use_container_width=True):
                st.session_state.active_query = "What is the limitation of liability, liability cap, and what damages are excluded?"
        with col_q3:
            if st.button("💳 Payment & Late Fees", use_container_width=True):
                st.session_state.active_query = "What are the payment deadlines, invoicing terms, and late payment interest fees?"
        with col_q4:
            if st.button("🔒 Confidentiality Term", use_container_width=True):
                st.session_state.active_query = "What are the confidentiality obligations and how long do they survive termination?"

        col_q5, col_q6, col_q7, col_q8 = st.columns(4)
        with col_q5:
            if st.button("💡 IP Ownership", use_container_width=True):
                st.session_state.active_query = "Who owns custom work product and intellectual property rights?"
        with col_q6:
            if st.button("🤝 Non-Solicitation", use_container_width=True):
                st.session_state.active_query = "Is there a non-compete or non-solicitation clause for personnel or contractors?"
        with col_q7:
            if st.button("⚖️ Governing Law", use_container_width=True):
                st.session_state.active_query = "What is the governing law jurisdiction and dispute resolution mechanism?"
        with col_q8:
            if st.button("❓ Anti-Hallucination Test", use_container_width=True):
                st.session_state.active_query = "What are the international maritime cargo shipping regulations?"

        st.markdown("")

        # Robust Q&A Form: Submits on Enter OR Button click!
        with st.form(key="contract_qa_form", clear_on_submit=False):
            query_input = st.text_input(
                "Enter your contract question:",
                value=st.session_state.active_query,
                placeholder="e.g. Is there a termination for convenience clause, and what notice is required?",
                label_visibility="collapsed"
            )
            col_sub1, col_sub2 = st.columns([1, 4])
            with col_sub1:
                submitted = st.form_submit_button("🔍 Analyze Clause", type="primary", use_container_width=True)

        # Trigger analysis if submitted or if a chip was clicked
        effective_query = query_input.strip()
        
        if submitted and effective_query:
            if not api_key:
                st.error("Please provide your Gemini API key in the sidebar.")
            else:
                with st.spinner("Retrieving clauses and performing legal risk evaluation..."):
                    try:
                        retrieved = st.session_state.vector_store.retrieve(effective_query, top_k=top_k)
                        analysis = analyze_clause_with_gemini(
                            query=effective_query,
                            retrieved_chunks=retrieved,
                            api_key=api_key,
                            model_name=DEFAULT_GENAI_MODEL
                        )
                        st.session_state.chat_history.insert(0, analysis)
                        st.session_state.active_query = effective_query
                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")

        # Render Latest Analysis Result
        if st.session_state.chat_history:
            latest = st.session_state.chat_history[0]
            risk = latest["risk_level"]
            
            # Risk Banner
            badge_html = {
                "HIGH": '<div class="risk-banner-high">🔴 HIGH RISK CLAUSE DETECTED</div>',
                "MEDIUM": '<div class="risk-banner-medium">🟡 MEDIUM RISK CLAUSE</div>',
                "LOW": '<div class="risk-banner-low">🟢 LOW RISK / STANDARD CLAUSE</div>',
                "NOT_FOUND": '<div class="risk-banner-notfound">⚪ NOT FOUND IN CONTRACT</div>'
            }.get(risk, '<div class="risk-banner-notfound">⚪ UNKNOWN RISK</div>')
            
            st.markdown(badge_html, unsafe_allow_html=True)
            st.markdown(f"#### Query: *\"{latest['query']}\"*")
            
            # Quoted Clause Box
            if latest["quote"]:
                st.markdown('<div class="section-title">1. Verbatim Quoted Clause</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="clause-quote-box">{latest["quote"]}</div>', unsafe_allow_html=True)
            
            # Plain English Explanation
            if latest["explanation"]:
                st.markdown('<div class="section-title">2. Plain English Translation</div>', unsafe_allow_html=True)
                st.markdown(latest["explanation"])
            
            # Risk Assessment & Reason
            if latest["risk_reason"]:
                st.markdown('<div class="section-title">3. Business Risk & Legal Exposure</div>', unsafe_allow_html=True)
                st.markdown(latest["risk_reason"])
            
            # Recommendations
            if latest["recommendation"]:
                st.markdown('<div class="section-title">4. Negotiation & Redline Recommendations</div>', unsafe_allow_html=True)
                st.markdown(latest["recommendation"])
                
            # If parsing failed to separate sections, fallback to raw response cleanly
            if not latest["quote"] and not latest["explanation"]:
                st.markdown(latest["raw_response"])

            # Grounding Verification (ChromaDB Citations)
            with st.expander(f"🔎 Source Grounding: {len(latest['retrieved_chunks'])} Excerpts Retrieved via ChromaDB"):
                for i, chunk in enumerate(latest["retrieved_chunks"], 1):
                    meta = chunk.get("metadata", {})
                    sim = chunk.get("similarity", 0)
                    st.markdown(f"""
                    <div class="chunk-card">
                        <b>Excerpt #{i}</b> &nbsp;|&nbsp; 
                        <b>Page:</b> {meta.get('page_number', 'N/A')} &nbsp;|&nbsp; 
                        <b>Cosine Match:</b> {sim}% &nbsp;|&nbsp; 
                        <b>Length:</b> {meta.get('char_length', 'N/A')} chars
                        <div style="margin-top: 6px; color: #334155;">{chunk['text']}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Historical Queries Accordion
            if len(st.session_state.chat_history) > 1:
                with st.expander(f"🕒 Previous Inquiries ({len(st.session_state.chat_history) - 1})"):
                    for prev in st.session_state.chat_history[1:]:
                        st.markdown(f"**Q: {prev['query']}** ({prev['risk_level']} Risk)")
                        if prev.get("quote"):
                            st.markdown(f"> *{prev['quote']}*")
                        if prev.get("explanation"):
                            st.markdown(prev["explanation"])
                        st.markdown("---")

    # =========================================================================
    # TAB 2: EXECUTIVE RISK SCORECARD
    # =========================================================================
    with tab_audit:
        st.subheader("📊 Executive Contract Risk Scorecard")
        st.markdown(
            "Performs a comprehensive automated audit across the **5 critical risk pillars** of commercial agreements: "
            "Termination Rights, Liability Caps, Invoicing Penalties, Confidentiality Survival, and Intellectual Property."
        )

        col_audit_btn, col_empty = st.columns([2, 3])
        with col_audit_btn:
            run_audit = st.button("🚀 Run Comprehensive 5-Pillar Audit", type="primary", use_container_width=True)

        if run_audit:
            if not api_key:
                st.error("Please configure your Gemini API Key in the sidebar.")
            else:
                with st.spinner("Executing 5-pillar risk audit across ChromaDB vector store..."):
                    try:
                        scorecard = generate_contract_risk_scorecard(
                            st.session_state.vector_store,
                            api_key=api_key,
                            model_name=DEFAULT_GENAI_MODEL
                        )
                        st.session_state.scorecard_results = scorecard
                    except Exception as e:
                        st.error(f"Error executing scorecard: {str(e)}")

        if st.session_state.scorecard_results:
            results = st.session_state.scorecard_results
            
            # Risk Distribution Summary
            high_count = sum(1 for r in results if r["risk_level"] == "HIGH")
            med_count = sum(1 for r in results if r["risk_level"] == "MEDIUM")
            low_count = sum(1 for r in results if r["risk_level"] == "LOW")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total Pillars Audited", len(results))
            with col_m2:
                st.metric("🔴 High Risk Items", high_count)
            with col_m3:
                st.metric("🟡 Medium Risk Items", med_count)
            with col_m4:
                st.metric("🟢 Standard / Low Risk", low_count)

            st.markdown("---")
            st.markdown("### Clause-by-Clause Findings")
            
            for item in results:
                cat = item["category"]
                risk = item["risk_level"]
                badge_text = {
                    "HIGH": "🔴 High Risk",
                    "MEDIUM": "🟡 Medium Risk",
                    "LOW": "🟢 Low Risk",
                    "NOT_FOUND": "⚪ Not Found"
                }.get(risk, "⚪ Unrated")
                
                with st.expander(f"**{cat}** — {badge_text}", expanded=(risk == "HIGH")):
                    if item.get("quote"):
                        st.markdown(f'<div class="clause-quote-box">{item["quote"]}</div>', unsafe_allow_html=True)
                    if item.get("explanation"):
                        st.markdown(f"**Explanation**: {item['explanation']}")
                    if item.get("risk_reason"):
                        st.markdown(f"**Risk Evaluation**: {item['risk_reason']}")
                    if item.get("recommendation"):
                        st.markdown(f"**Recommended Action**: {item['recommendation']}")

    # =========================================================================
    # TAB 3: CLAUSE LIBRARY EXPLORER
    # =========================================================================
    with tab_library:
        st.subheader("📑 Indexed Contract Clauses")
        st.markdown(f"Displaying **{len(st.session_state.doc_chunks)}** semantic chunks indexed from `{st.session_state.current_doc_name}`.")
        
        filter_term = st.text_input("Filter clauses by keyword:", placeholder="e.g. indemnity, liability, terminate, invoice...")
        
        filtered = st.session_state.doc_chunks
        if filter_term:
            filtered = [c for c in filtered if filter_term.lower() in c["text"].lower()]
            st.caption(f"Showing {len(filtered)} clauses matching '{filter_term}'")
            
        for chunk in filtered[:20]:
            meta = chunk["metadata"]
            st.markdown(f"""
            <div class="chunk-card">
                <b>Clause Chunk #{meta['chunk_id']}</b> &nbsp;|&nbsp; 
                <b>Page {meta['page_number']} of {meta['total_pages']}</b> &nbsp;|&nbsp; 
                <b>Size:</b> {meta['char_length']} characters
                <div style="margin-top: 6px; color: #1e293b; font-size: 0.9rem;">{chunk['text']}</div>
            </div>
            """, unsafe_allow_html=True)

    # =========================================================================
    # TAB 4: SYSTEM ARCHITECTURE
    # =========================================================================
    with tab_system:
        st.subheader("ℹ️ System Architecture & Reliability Design")
        st.markdown("""
        ### High-Precision Retrieval-Augmented Generation (RAG)
        
        1. **High-Fidelity Text Extraction**: Uses `pypdf` to parse legal text while tracking exact page numbers for auditable citations.
        2. **Clause-Aware Overlapping Chunking**: Splitting is bounded at ~800 characters with 150-character overlaps and sentence boundary snapping to ensure clauses are never severed mid-obligation.
        3. **Dense Vector Embeddings**: Utilizes Google's `gemini-embedding-001` producing 3072-dimensional vector representations.
        4. **Vector Retrieval via ChromaDB**: Local HNSW indexing using Cosine similarity metrics for instant sub-millisecond retrieval.
        5. **Strict Grounding Guardrails**: Enforces that the model only answers from retrieved context. When terms do not exist in the agreement, it reports *Not found in contract*, preventing hallucination.
        """)
