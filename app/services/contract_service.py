"""
Contract Service — generates PDF contract and PO documents.

Migrated from contract_generator.py.
"""

import os
from datetime import datetime
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_OUTPUT_DIR = "contracts"


def _logo_path() -> str | None:
    """Find the company logo, if any."""
    base = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(base))  # app/services → app → root
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(root, "static", f"company_logo.{ext}")
        if os.path.isfile(p):
            return p
    return None


class ContractService:
    """Generates contract and PO documents as PDFs."""

    def __init__(self, output_dir: str = _OUTPUT_DIR) -> None:
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_proposal_document(self, proposal_data: Dict[str, Any]) -> str:
        """Generate a PDF proposal contract and return the file path."""
        filename = f"proposal_{proposal_data.get('proposal_number', 'unknown')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        logo = _logo_path()
        if logo:
            try:
                story.append(RLImage(logo, width=2 * inch, height=0.75 * inch))
                story.append(Spacer(1, 0.2 * inch))
            except Exception:
                pass

        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
        )
        story.append(Paragraph("PROPOSAL AGREEMENT", title_style))
        story.append(Spacer(1, 0.2 * inch))

        for label, key in [
            ("Proposal Number", "proposal_number"),
            ("Client Name", "client_name"),
            ("Project Name", "project_name"),
        ]:
            story.append(
                Paragraph(f"<b>{label}:</b> {proposal_data.get(key, '')}", styles["Normal"])
            )
        story.append(
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles["Normal"])
        )
        story.append(Spacer(1, 0.3 * inch))

        pricing = proposal_data.get("pricing_breakdown", {})
        total = pricing.get("total_price", proposal_data.get("total_price", 0))
        story.append(Paragraph(f"<b>Total Amount:</b> ${float(total):,.2f}", styles["Normal"]))

        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("<b>Terms and Conditions</b>", styles["Heading2"]))
        story.append(
            Paragraph(
                "This proposal is valid for 30 days from the date above. "
                "Payment terms: 50% upfront, 50% upon completion.",
                styles["Normal"],
            )
        )

        doc.build(story)
        return filepath

    def generate_po_document(self, po_data: Dict[str, Any]) -> str:
        """Generate a PDF purchase order and return the file path."""
        filename = f"po_{po_data.get('po_number', 'unknown')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        logo = _logo_path()
        if logo:
            try:
                story.append(RLImage(logo, width=2 * inch, height=0.75 * inch))
                story.append(Spacer(1, 0.2 * inch))
            except Exception:
                pass

        title_style = ParagraphStyle(
            "POTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
        )
        story.append(Paragraph("PURCHASE ORDER", title_style))
        story.append(Spacer(1, 0.2 * inch))

        story.append(
            Paragraph(f"<b>PO Number:</b> {po_data.get('po_number', '')}", styles["Normal"])
        )
        story.append(
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles["Normal"])
        )
        story.append(
            Paragraph(f"<b>Client:</b> {po_data.get('client_name', '')}", styles["Normal"])
        )
        story.append(Spacer(1, 0.3 * inch))

        total_amount = po_data.get("total_amount", 0)
        data = [
            ["Description", "Amount"],
            ["Migration Services", f"${float(total_amount):,.2f}"],
            ["TOTAL", f"${float(total_amount):,.2f}"],
        ]
        table = Table(data, colWidths=[4 * inch, 2 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 1), (-1, -2), colors.beige),
                ]
            )
        )
        story.append(table)
        doc.build(story)
        return filepath
