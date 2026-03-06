"""
Settings API router — /api/settings/* (logo upload, health check & email template)
"""

import json
import os
import shutil
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import get_db
from app.core.config import settings as app_settings
from app.repositories.pricing_config_repository import PricingConfigRepository
from app.services.email_service import EmailService

router = APIRouter(prefix="/api", tags=["Settings & Health"])

# Resolve static dir relative to project root at import time
# settings.py lives at app/api/v1/ → need 4× dirname to reach project root
_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)
_STATIC_DIR = os.path.join(_ROOT, "static")

# Predefined logos stored in /static/
_PREDEFINED_LOGOS = [
    {"id": "logo1", "name": "Logo 1", "file": "logo1.jpg"},
    {"id": "logo2", "name": "Logo 2", "file": "logo2.jpg"},
    {"id": "logo3", "name": "Logo 3", "file": "logo3.jpg"},
    {"id": "logo4", "name": "Logo 4", "file": "logo4.jpg"},
    {"id": "logo5", "name": "Logo 5", "file": "logo5.jpg"},
]


@router.get("/health")
def health_check(db=Depends(get_db)):
    """Health check — verifies the database connection is alive."""
    try:
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database health check failed: {exc}",
        ) from exc


@router.get("/settings/logo")
def get_logo_status():
    """Return whether a company logo is uploaded and its preview URL."""
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(_STATIC_DIR, f"company_logo.{ext}")
        if os.path.isfile(p):
            return {
                "has_logo": True,
                "url": f"/static/company_logo.{ext}?t={os.path.getmtime(p)}",
            }
    return {"has_logo": False, "url": None}


@router.get("/settings/predefined-logos")
def get_predefined_logos():
    """Return list of predefined logos with their preview URLs."""
    logos = []
    for logo in _PREDEFINED_LOGOS:
        file_path = os.path.join(_STATIC_DIR, logo["file"])
        if os.path.isfile(file_path):
            logos.append({
                "id": logo["id"],
                "name": logo["name"],
                "url": f"/static/{logo['file']}?t={os.path.getmtime(file_path)}",
                "file": logo["file"],
            })
    return {"logos": logos}


class SelectLogoRequest(BaseModel):
    logo_id: str


@router.post("/settings/logo/select")
def select_predefined_logo(body: SelectLogoRequest):
    """Select a predefined logo and set it as the active company logo."""
    # Find the logo in our predefined list
    selected = next((l for l in _PREDEFINED_LOGOS if l["id"] == body.logo_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Predefined logo not found")

    src = os.path.join(_STATIC_DIR, selected["file"])
    if not os.path.isfile(src):
        raise HTTPException(status_code=404, detail="Logo file not found on disk")

    os.makedirs(_STATIC_DIR, exist_ok=True)

    # Remove any existing company_logo files
    for old_ext in ("png", "jpg", "jpeg"):
        old = os.path.join(_STATIC_DIR, f"company_logo.{old_ext}")
        if os.path.isfile(old):
            try:
                os.remove(old)
            except OSError:
                pass

    # Determine destination extension from source
    src_ext = os.path.splitext(selected["file"])[1]  # e.g. ".jpg"
    dest = os.path.join(_STATIC_DIR, f"company_logo{src_ext}")
    shutil.copy2(src, dest)

    return {
        "success": True,
        "url": f"/static/company_logo{src_ext}?t={os.path.getmtime(dest)}",
        "selected_id": body.logo_id,
        "name": selected["name"],
    }


@router.post("/settings/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload (or replace) the company logo. Accepts PNG or JPEG."""
    allowed = ("image/png", "image/jpeg", "image/jpg")
    if not file.content_type or file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File must be PNG or JPEG")

    os.makedirs(_STATIC_DIR, exist_ok=True)
    ext = ".png" if file.content_type == "image/png" else ".jpg"

    # Remove any existing logo (different extension)
    for old_ext in ("png", "jpg", "jpeg"):
        old = os.path.join(_STATIC_DIR, f"company_logo.{old_ext}")
        if os.path.isfile(old):
            try:
                os.remove(old)
            except OSError:
                pass

    dest = os.path.join(_STATIC_DIR, f"company_logo{ext}")
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)

    return {"success": True, "url": f"/static/company_logo{ext}"}


# ── Default email template values ────────────────────────────────────────────
_DEFAULT_SUBJECT = "Proposal {{proposal_number}} — {{project_name}}"
_DEFAULT_BODY = """<html>
  <body style="margin:0;padding:0;background:#f5f6fa;font-family:Arial,sans-serif;">
    {{logo_block}}
    <div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
      <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:32px 36px;">
        <h1 style="color:#fff;margin:0;font-size:1.4rem;font-weight:700;">Proposal Ready</h1>
        <p style="color:rgba(255,255,255,0.85);margin:6px 0 0;font-size:0.9rem;">{{proposal_number}}</p>
      </div>
      <div style="padding:32px 36px;">
        <p style="font-size:1rem;color:#1e2433;margin:0 0 16px;">Dear <strong>{{client_name}}</strong>,</p>
        <p style="color:#4b5563;line-height:1.7;margin:0 0 16px;">Please find attached the proposal for the project <strong>{{project_name}}</strong>.</p>
        <p style="color:#4b5563;line-height:1.7;margin:0;">If you have any questions, feel free to reply to this email.</p>
      </div>
      <div style="background:#f8f9fc;padding:20px 36px;border-top:1px solid #e8eaf0;">
        <p style="margin:0;font-size:0.85rem;color:#9ca3af;">Best regards,<br><strong style="color:#6366f1;">Proposal Automation System</strong></p>
      </div>
    </div>
  </body>
</html>"""

_DEFAULT_PLAIN_BODY = """Dear {{client_name}},

Please find attached the proposal for the project {{project_name}}. 

Reference Number: {{proposal_number}}

If you have any questions or need further clarification, please feel free to reach out.

Best regards,
Proposal Automation Team"""



class EmailTemplateRequest(BaseModel):
    subject: str
    body: str
    mode: str = "html"  # 'html' or 'plain'


class TestEmailRequest(BaseModel):
    to_email: str
    subject: Optional[str] = None
    body: Optional[str] = None


class ClientTemplateRequest(BaseModel):
    client_email: str
    subject: str
    body: str


@router.get("/settings/client-templates")
def list_client_templates(db=Depends(get_db)):
    """Return all client-specific email template overrides."""
    repo = PricingConfigRepository(db)
    return {"templates": repo.list_client_templates()}


@router.post("/settings/client-templates")
def save_client_template(body: ClientTemplateRequest, db=Depends(get_db)):
    """Create or update a template override for a specific client."""
    repo = PricingConfigRepository(db)
    repo.upsert_client_template(body.client_email, body.subject, body.body)
    repo.commit()
    return {"success": True, "message": f"Template for {body.client_email} saved"}


@router.delete("/settings/client-templates/{client_email}")
def delete_client_template(client_email: str, db=Depends(get_db)):
    """Remove a client-specific template override."""
    repo = PricingConfigRepository(db)
    deleted = repo.delete_client_template(client_email)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template override not found")
    repo.commit()
    return {"success": True, "message": f"Template for {client_email} removed"}


def _get_logo_block() -> str:
    """Return an <img> HTML block for the company logo if one exists, else empty string."""
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(_STATIC_DIR, f"company_logo.{ext}")
        if os.path.isfile(p):
            logo_url = f"{app_settings.BASE_URL if hasattr(app_settings, 'BASE_URL') else 'http://localhost:8000'}/static/company_logo.{ext}"
            return (
                f'<div style="text-align:center;padding:24px 36px 0;">'
                f'<img src="{logo_url}" alt="Company Logo" '
                f'style="max-height:70px;max-width:220px;object-fit:contain;" /></div>'
            )
    return ""


def _apply_placeholders(text: str, data: dict, mode: str = "html") -> str:
    """Replace {{placeholder}} tokens in text with actual values and handle wrapping if plain."""
    # 1. Replace tokens
    for key, value in data.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))

    # 2. If mode is plain, wrap in a professional layout
    if mode == "plain":
        # Convert newlines to <br> for HTML preview/send
        safe_msg = text.replace("\n", "<br>")
        logo_html = _get_logo_block()
        
        return f"""<html>
  <body style="margin:0;padding:0;background:#f8f9fc;font-family:'Segoe UI',Arial,sans-serif;">
    {logo_html}
    <div style="max-width:600px;margin:20px auto;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.05);border:1px solid #eef0f5;">
      <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:left;">
        <h1 style="color:#ffffff;margin:0;font-size:22px;font-weight:700;">Proposal Update</h1>
      </div>
      <div style="padding:40px;font-size:16px;color:#1e293b;line-height:1.6;">
        {safe_msg}
      </div>
      <div style="background:#f1f5f9;padding:20px 40px;text-align:center;font-size:12px;color:#94a3b8;">
        This is an automated message from the Proposal Automation System.
      </div>
    </div>
  </body>
</html>"""
        
    return text


@router.get("/settings/email-template")
def get_email_template(db=Depends(get_db)):
    """Return the saved email template (subject + body + mode) from pricing_config."""
    repo = PricingConfigRepository(db)
    subject = repo.get_raw_value("email_template_subject")
    body = repo.get_raw_value("email_template_body")
    mode = repo.get_raw_value("email_template_mode") or "html"
    
    if not body:
        body = _DEFAULT_PLAIN_BODY if mode == "plain" else _DEFAULT_BODY
        
    return {
        "subject": subject if subject else _DEFAULT_SUBJECT,
        "body": body,
        "mode": mode,
        "placeholders": [
            {"key": "{{client_name}}", "label": "Client Name"},
            {"key": "{{proposal_number}}", "label": "Proposal Number"},
            {"key": "{{project_name}}", "label": "Project Name"},
            {"key": "{{logo_block}}", "label": "Company Logo (auto)"},
        ],
    }


@router.post("/settings/email-template")
def save_email_template(body: EmailTemplateRequest, db=Depends(get_db)):
    """Save the email template subject, body, and mode to pricing_config."""
    repo = PricingConfigRepository(db)

    # Upsert subject
    repo.upsert("email_template_subject", body.subject, "Subject line for proposal emails.")

    # Upsert body
    repo.upsert("email_template_body", body.body, "Email body/message content.")

    # Upsert mode
    repo.upsert("email_template_mode", body.mode, "Editor mode: plain or html.")

    repo.commit()
    return {"success": True, "message": "Email template saved successfully"}


@router.post("/settings/email-template/test")
def send_test_email(body: TestEmailRequest, db=Depends(get_db)):
    """Send a test email using the saved (or provided) template."""
    repo = PricingConfigRepository(db)

    subject_tpl = body.subject or repo.get_raw_value("email_template_subject") or _DEFAULT_SUBJECT
    body_tpl = body.body or repo.get_raw_value("email_template_body") or _DEFAULT_BODY
    mode = repo.get_raw_value("email_template_mode") or "html"

    # Sample data for placeholder replacement
    sample_data = {
        "client_name": "John Doe",
        "proposal_number": "PROP-20240305-120000",
        "project_name": "My Test Project",
        "logo_block": _get_logo_block(),
    }

    rendered_subject = _apply_placeholders(subject_tpl, sample_data)
    # If testing, prioritize current UI state but use mode logic
    rendered_body = _apply_placeholders(body_tpl, sample_data, mode=mode)

    svc = EmailService()
    # We need a tiny placeholder PDF for the test
    try:
        dummy_pdf = b"%PDF-1.4 1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj xref 0 4 0000000000 65535 f 0000000009 00000 n 0000000058 00000 n 0000000115 00000 n trailer<</Size 4/Root 1 0 R>>startxref 195 %%EOF"
        success = svc.send_email_with_attachment(
            to_email=body.to_email,
            subject=rendered_subject,
            body=rendered_body,
            attachment_bytes=dummy_pdf,
            attachment_filename="test_proposal.pdf",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {exc}") from exc

    if not success:
        raise HTTPException(status_code=500, detail="Email sending failed. Check SMTP settings.")

    return {"success": True, "message": f"Test email sent to {body.to_email}"}
