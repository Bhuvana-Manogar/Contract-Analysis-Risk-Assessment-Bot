"""
Sample PDF Contract Generator
Creates a realistic Master Services Agreement (MSA) & NDA for testing the Contract Analysis Bot.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib import colors

def generate_sample_contract(output_path="sample_contracts/sample_service_agreement.pdf"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=18
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8
    )
    
    elements = []
    
    # Title
    elements.append(Paragraph("MASTER PROFESSIONAL SERVICES AGREEMENT", title_style))
    elements.append(Paragraph("Contract Reference: MSA-2026-0889 | Effective Date: October 1, 2026", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))
    
    # Preamble
    elements.append(Paragraph(
        "This Master Professional Services Agreement (the 'Agreement') is entered into as of October 1, 2026 (the 'Effective Date'), "
        "by and between <b>Acme Enterprise Solutions Inc.</b>, a Delaware corporation ('Client'), and <b>Apex Cloud Technologies LLC</b>, "
        "a California limited liability company ('Service Provider'). Client and Service Provider may individually be referred to as a "
        "'Party' and collectively as the 'Parties'.",
        body_style
    ))
    
    # Section 1
    elements.append(Paragraph("1. SCOPE OF SERVICES & DELIVERABLES", section_style))
    elements.append(Paragraph(
        "1.1 <b>Services</b>: Service Provider shall perform software engineering, architecture review, and AI integration services "
        "as described in Statements of Work ('SOW') executed pursuant to this Agreement.<br/>"
        "1.2 <b>Changes</b>: Any modifications to project scope, timeline, or deliverables must be documented in a written Change Order "
        "duly signed by authorized representatives of both Parties.",
        body_style
    ))
    
    # Section 2
    elements.append(Paragraph("2. COMPENSATION, INVOICING & PAYMENT TERMS", section_style))
    elements.append(Paragraph(
        "2.1 <b>Fees</b>: Client shall pay Service Provider the professional fees specified in each SOW, totaling a baseline of $45,000 per month.<br/>"
        "2.2 <b>Invoicing and Payment</b>: Service Provider shall invoice Client monthly in arrears. Client shall remit payment within "
        "thirty (30) calendar days from the invoice date (Net 30).<br/>"
        "2.3 <b>Late Payment Interest</b>: Undisputed amounts outstanding past thirty (30) days shall accrue interest at a rate of 1.5% per month "
        "(18% per annum) or the maximum legal rate allowed under applicable law, whichever is lower.<br/>"
        "2.4 <b>Taxes</b>: All fees exclude applicable sales, value-added, or withholding taxes, which shall be the sole responsibility of Client.",
        body_style
    ))
    
    # Section 3
    elements.append(Paragraph("3. TERM AND TERMINATION", section_style))
    elements.append(Paragraph(
        "3.1 <b>Term</b>: This Agreement commences on the Effective Date and continues for an initial period of twelve (12) months, "
        "automatically renewing for successive one-year terms unless either Party provides sixty (60) days prior written notice.<br/>"
        "3.2 <b>Termination for Convenience by Client</b>: Client may terminate this Agreement or any SOW at any time, with or without cause, "
        "upon giving fourteen (14) calendar days prior written notice to Service Provider.<br/>"
        "3.3 <b>Termination for Convenience by Service Provider</b>: Service Provider may terminate this Agreement only upon sixty (60) calendar "
        "days prior written notice to Client.<br/>"
        "3.4 <b>Termination for Cause</b>: Either Party may terminate this Agreement immediately upon written notice if the other Party commits "
        "a material breach and fails to cure such breach within fifteen (15) business days of receiving written notice.<br/>"
        "3.5 <b>Effect of Termination</b>: Upon termination, Client shall pay Service Provider for all completed work and non-cancelable commitments "
        "incurred prior to the effective date of termination.",
        body_style
    ))
    
    # Section 4
    elements.append(Paragraph("4. CONFIDENTIALITY AND NON-DISCLOSURE", section_style))
    elements.append(Paragraph(
        "4.1 <b>Definition</b>: 'Confidential Information' includes all non-public proprietary business, technical, financial, and operational "
        "data disclosed by one Party ('Disclosing Party') to the other ('Receiving Party').<br/>"
        "4.2 <b>Obligations</b>: Receiving Party shall protect Disclosing Party's Confidential Information with the same degree of care it uses for "
        "its own sensitive information, but not less than reasonable care. Receiving Party shall not disclose Confidential Information to any third "
        "party without prior written consent.<br/>"
        "4.3 <b>Exclusions</b>: Confidential Information does not include information that: (a) is or becomes publicly available without breach, "
        "(b) was already known to Receiving Party prior to disclosure, or (c) is independently developed without reference to the Disclosing Party's data.<br/>"
        "4.4 <b>Survival</b>: Confidentiality obligations under this Section 4 shall survive termination or expiration of this Agreement for a period "
        "of five (5) years, except for trade secrets which shall remain protected indefinitely.",
        body_style
    ))
    
    # Section 5
    elements.append(Paragraph("5. INTELLECTUAL PROPERTY RIGHTS & OWNERSHIP", section_style))
    elements.append(Paragraph(
        "5.1 <b>Work Product</b>: All custom code, algorithms, and documentation developed specifically for Client under an SOW ('Work Product') "
        "shall be deemed 'works made for hire'. Ownership thereof shall vest in Client immediately upon full and final payment of all applicable fees.<br/>"
        "5.2 <b>Pre-existing IP</b>: Service Provider retains all right, title, and interest in its pre-existing tools, libraries, and background IP. "
        "Service Provider grants Client a perpetual, royalty-free, worldwide license to use such background IP solely as embedded in the Work Product.",
        body_style
    ))
    
    # Section 6
    elements.append(Paragraph("6. LIMITATION OF LIABILITY & DAMAGES", section_style))
    elements.append(Paragraph(
        "6.1 <b>Consequential Damages Waiver</b>: NEITHER PARTY SHALL BE LIABLE TO THE OTHER FOR ANY INDIRECT, INCIDENTAL, SPECIAL, PUNITIVE, "
        "OR CONSEQUENTIAL DAMAGES, INCLUDING LOSS OF PROFITS, REVENUE, OR DATA.<br/>"
        "6.2 <b>Aggregate Liability Cap</b>: EXCEPT FOR BREACH OF CONFIDENTIALITY UNDER SECTION 4 AND INDEMNIFICATION UNDER SECTION 7, EACH PARTY'S "
        "TOTAL AGGREGATE LIABILITY ARISING UNDER THIS AGREEMENT SHALL BE STRICTLY LIMITED TO THE TOTAL FEES PAID OR PAYABLE BY CLIENT UNDER THE "
        "SPECIFIC SOW IN THE THREE (3) MONTHS PRECEDING THE CLAIM.<br/>"
        "6.3 <b>Carve-outs</b>: LIABILITY FOR SERVICE PROVIDER'S GROSS NEGLIGENCE, WILLFUL MISCONDUCT, OR INDEMNIFICATION OBLIGATIONS SHALL REMAIN "
        "UNCAPPED.",
        body_style
    ))
    
    # Section 7
    elements.append(Paragraph("7. INDEMNIFICATION", section_style))
    elements.append(Paragraph(
        "7.1 <b>Service Provider Indemnity</b>: Service Provider shall defend, indemnify, and hold harmless Client from and against any third-party "
        "claims alleging that the Work Product infringes any valid patent, copyright, or trademark, provided Client promptly notifies Service Provider in writing.<br/>"
        "7.2 <b>Client Indemnity</b>: Client shall indemnify Service Provider against third-party claims arising from Client-provided data or materials.",
        body_style
    ))
    
    # Section 8
    elements.append(Paragraph("8. NON-SOLICITATION OF PERSONNEL", section_style))
    elements.append(Paragraph(
        "8.1 During the term of this Agreement and for a period of twelve (12) months following its termination, neither Party shall directly or "
        "indirectly solicit, recruit, or hire any employee or contractor of the other Party who was directly involved in the performance of Services "
        "without prior written consent. A buyout fee equal to 50% of the candidate's first-year annualized salary shall apply upon violation.",
        body_style
    ))
    
    # Section 9
    elements.append(Paragraph("9. GOVERNING LAW AND DISPUTE RESOLUTION", section_style))
    elements.append(Paragraph(
        "9.1 <b>Governing Law</b>: This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware, "
        "without regard to its conflict of law principles.<br/>"
        "9.2 <b>Arbitration</b>: Any dispute arising out of this Agreement shall be resolved through binding arbitration administered by the American "
        "Arbitration Association (AAA) in Wilmington, Delaware, before a single arbitrator. Each party shall bear its own legal fees.",
        body_style
    ))
    
    # Section 10
    elements.append(Paragraph("10. MISCELLANEOUS", section_style))
    elements.append(Paragraph(
        "10.1 <b>Entire Agreement</b>: This Agreement supersedes all prior proposals, agreements, and representations.<br/>"
        "10.2 <b>Severability</b>: If any provision is deemed unenforceable, remaining provisions remain in full effect.<br/>"
        "10.3 <b>Force Majeure</b>: Neither Party shall be liable for delays resulting from acts of God, war, pandemic, or government action.",
        body_style
    ))
    
    doc.build(elements)
    print(f"Sample PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    generate_sample_contract()
