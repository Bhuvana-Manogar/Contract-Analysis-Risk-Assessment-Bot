import streamlit as st
import os
import json
import pdfplumber
import docx
from typing import List, Optional
from pydantic import BaseModel, Field

# --- IMPORTS FOR GEMINI 2.5 & STRUCTURED OUTPUT ---
from google import genai
from google.genai import types

# --- 1. CONFIGURATION & SECURITY ---
# In production, this key comes from the environment variable.
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("🚨 Security Alert: GEMINI_API_KEY not found in environment variables.")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- 2. DATA MODELS (PYDANTIC) ---
# This acts as the "Schema" for Gemini 2.5 Flash.
# It guarantees the output is always valid JSON with these exact fields.

class EntityData(BaseModel):
    parties: List[str] = Field(description="Names of organizations or individuals signing the contract")
    dates: List[str] = Field(description="Key dates like start date, end date, payment deadlines")
    jurisdiction: str = Field(description="City and State of governing law (e.g., 'Mumbai, Maharashtra')")
    liabilities: List[str] = Field(description="Liability caps or indemnity limits")

class RiskFlags(BaseModel):
    penalty_clauses: bool = Field(description="Are there penalties for late payment/breach?")
    unilateral_termination: bool = Field(description="Can one party cancel without cause?")
    auto_renewal: bool = Field(description="Does the contract auto-renew without notice?")
    indemnity_risk: bool = Field(description="Is there uncapped indemnity?")
    arbitration: bool = Field(description="Is arbitration the dispute resolution mechanism?")

class ClauseAnalysis(BaseModel):
    header: str = Field(description="The title or number of the clause")
    text_summary: str = Field(description="Simplified explanation in plain English")
    category: str = Field(description="One of: Obligation, Right, Prohibition, Definition, Standard")
    risk_level: str = Field(description="High, Medium, or Low")
    ambiguity_detected: bool = Field(description="True if the language is vague")
    suggestion: Optional[str] = Field(description="Renegotiation advice if risk is High")

class ContractAudit(BaseModel):
    contract_type: str = Field(description="Type of agreement (e.g., NDA, SaaS, Employment)")
    risk_score: int = Field(description="Overall risk score 0-100")
    summary: str = Field(description="Executive summary of the contract")
    entities: EntityData
    risk_flags: RiskFlags
    clauses: List[ClauseAnalysis]

# --- 3. HELPER FUNCTIONS ---

def extract_text(file_obj):
    """Universal text extractor for PDF, DOCX, TXT"""
    fname = file_obj.name.lower()
    text = ""
    try:
        if fname.endswith('.pdf'):
            with pdfplumber.open(file_obj) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text += t + "\n"
        elif fname.endswith('.docx'):
            doc = docx.Document(file_obj)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            text = file_obj.getvalue().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text

def analyze_contract_optimized(text_content):
    """
    Uses Gemini 2.5 Flash with Native Structured Output (Pydantic).
    This is faster and 100% more reliable than JSON mode.
    """
    prompt = "Analyze this contract for an Indian SME. Be strict about risk detection."

    try:
        # The 'response_schema' argument forces Gemini to output data matching our Pydantic class
        response = client.models.generate_content(
            model='gemini-2.5-flash', # Optimized for your key
            contents=[prompt, text_content],
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=ContractAudit, # <--- The Magic Optimization
                temperature=0.1 # Low temp for precision
            )
        )
        
        # Parse the JSON response directly into our Pydantic object
        # (or simple dict if preferred for Streamlit)
        return json.loads(response.text)
        
    except Exception as e:
        st.error(f"Gemini API Error: {e}")
        return None

# --- 4. UI DASHBOARD ---

st.set_page_config(page_title="ContractGuardian AI", layout="wide", page_icon="⚖️")

st.title("⚖️ ContractGuardian Pro")
st.caption("Powered by Gemini 2.5 Flash • Optimized for Production")

# Sidebar
with st.sidebar:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Drop your contract here", type=['pdf', 'docx', 'txt'])
    st.markdown("---")
    st.info("🔒 Data processed in memory. No external storage.")

if uploaded_file:
    # Processing
    with st.spinner("Reading document..."):
        raw_text = extract_text(uploaded_file)

    if raw_text:
        # Analysis Button
        if st.button("Analyze Risks", type="primary", use_container_width=True):
            with st.spinner("⚡ Gemini 2.5 Flash is auditing (Structured Mode)..."):
                data = analyze_contract_optimized(raw_text)

            if data:
                # Top Metrics
                st.markdown("### 🛡️ Risk Assessment")
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric("Type", data.get('contract_type', 'Unknown'))
                
                r_score = data.get('risk_score', 0)
                r_color = "normal" if r_score < 40 else "inverse"
                col2.metric("Risk Score", f"{r_score}/100", delta_color=r_color)
                
                col3.metric("Jurisdiction", data['entities'].get('jurisdiction', 'N/A'))
                col4.metric("Clauses", len(data.get('clauses', [])))

                st.success(f"**Executive Summary:** {data.get('summary')}")

                # Main Content Tabs
                tab_risks, tab_clauses, tab_entities = st.tabs(["⚠️ Critical Flags", "📝 Clause Breakdown", "🏛️ Entities"])

                # --- Tab 1: Risk Flags (Visual Grid) ---
                with tab_risks:
                    flags = data['risk_flags']
                    
                    # Helper to display flags
                    def status_card(label, is_bad):
                        if is_bad:
                            st.error(f"🚩 **{label}**: DETECTED")
                        else:
                            st.success(f"✅ **{label}**: Safe")

                    c1, c2, c3 = st.columns(3)
                    with c1: status_card("Penalty Clauses", flags.get('penalty_clauses'))
                    with c2: status_card("Unilateral Termination", flags.get('unilateral_termination'))
                    with c3: status_card("Auto-Renewal", flags.get('auto_renewal'))
                    
                    c4, c5 = st.columns(2)
                    with c4: status_card("Indemnity Risk", flags.get('indemnity_risk'))
                    with c5: status_card("Arbitration", flags.get('arbitration'))

                # --- Tab 2: Detailed Clauses ---
                with tab_clauses:
                    filter_high = st.toggle("Show High Risk Only")
                    
                    for clause in data.get('clauses', []):
                        if filter_high and clause['risk_level'] != "High":
                            continue
                            
                        # Color coding
                        color = "red" if clause['risk_level'] == "High" else "orange" if clause['risk_level'] == "Medium" else "green"
                        
                        with st.expander(f"**{clause['header']}** - :{color}[{clause['risk_level']} Risk]"):
                            st.markdown(f"**Summary:** {clause['text_summary']}")
                            st.caption(f"Category: {clause['category']}")
                            
                            if clause.get('ambiguity_detected'):
                                st.warning("⚠️ Ambiguous language detected here.")
                                
                            if clause['risk_level'] == "High":
                                st.info(f"💡 **Negotiation Tip:** {clause.get('suggestion')}")

                # --- Tab 3: Entities ---
                with tab_entities:
                    ents = data['entities']
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.subheader("Parties")
                        for p in ents.get('parties', []): st.write(f"• {p}")
                        st.subheader("Financial Liabilities")
                        for l in ents.get('liabilities', []): st.warning(f"• {l}")
                    with ec2:
                        st.subheader("Key Dates")
                        for d in ents.get('dates', []): st.write(f"• {d}")

                # Export
                st.markdown("---")
                st.download_button(
                    label="📥 Download JSON Audit",
                    data=json.dumps(data, indent=2),
                    file_name="legal_audit.json",
                    mime="application/json"
                )