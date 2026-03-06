"""
Export API router — /api/export/*
"""

import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.deps import get_db
from app.services.export_service import ExportService
from app.services.proposal_service import ProposalService

router = APIRouter(prefix="/api/export", tags=["Exports"])

_export_svc = ExportService()


def _content_disposition(disposition: str, filename: str) -> str:
    """
    Build a Content-Disposition header value with both a plain ASCII fallback
    (for old clients) and an RFC 5987 encoded filename* parameter (for modern
    browsers).  Example output:
        attachment; filename="proposal_PROP-20260226-171127.pdf"; filename*=UTF-8''proposal_PROP-20260226-171127.pdf
    """
    encoded = urllib.parse.quote(filename, safe="")
    return f'{disposition}; filename="{filename}"; filename*=UTF-8\'\'{encoded}'


@router.get("/proposal/{proposal_id}/pdf")
def export_proposal_pdf(proposal_id: int, db=Depends(get_db)):
    """Download proposal as a PDF file."""
    data = ProposalService(db).get_for_export(proposal_id)
    if not data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    try:
        pdf_bytes = _export_svc.generate_pdf(data)
        filename = f"proposal_{data['proposal_number']}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": _content_disposition("attachment", filename),
                "Content-Type": "application/pdf",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/proposal/{proposal_id}/excel")
def export_proposal_excel(proposal_id: int, db=Depends(get_db)):
    """Download proposal as an Excel (.xlsx) file."""
    data = ProposalService(db).get_for_export(proposal_id)
    if not data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    try:
        excel_bytes = _export_svc.generate_excel(data)
        filename = f"proposal_{data['proposal_number']}.xlsx"
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": _content_disposition("attachment", filename),
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "X-Content-Type-Options": "nosniff",
            },
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
