"""
Settings API router — /api/settings/* (logo upload, health check & email templates)

Email templates are stored in the `client_email_templates` table with
template_type SYSTEM (read-only default) or CUSTOM (user-created).
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


# ═══════════════════════════════════════════════════════════════════════════════
# Logo endpoints (unchanged)
# ═══════════════════════════════════════════════════════════════════════════════

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
    selected = next((l for l in _PREDEFINED_LOGOS if l["id"] == body.logo_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Predefined logo not found")

    src = os.path.join(_STATIC_DIR, selected["file"])
    if not os.path.isfile(src):
        raise HTTPException(status_code=404, detail="Logo file not found on disk")

    os.makedirs(_STATIC_DIR, exist_ok=True)
    for old_ext in ("png", "jpg", "jpeg"):
        old = os.path.join(_STATIC_DIR, f"company_logo.{old_ext}")
        if os.path.isfile(old):
            try:
                os.remove(old)
            except OSError:
                pass

    src_ext = os.path.splitext(selected["file"])[1]
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


# ═══════════════════════════════════════════════════════════════════════════════
# Email Template endpoints (DB-backed via client_email_templates table)
# ═══════════════════════════════════════════════════════════════════════════════

def _get_logo_block() -> str:
    """Return an <img> HTML block for the company logo if one exists."""
    for ext in ("png", "jpg", "jpeg"):
        p = os.path.join(_STATIC_DIR, f"company_logo.{ext}")
        if os.path.isfile(p):
            logo_url = (
                f"{app_settings.BASE_URL if hasattr(app_settings, 'BASE_URL') else 'http://localhost:8000'}"
                f"/static/company_logo.{ext}"
            )
            return (
                f'<div style="text-align:center;padding:24px 36px 0;">'
                f'<img src="{logo_url}" alt="Company Logo" '
                f'style="max-height:70px;max-width:220px;object-fit:contain;" /></div>'
            )
    return ""


def wrap_in_professional_layout(content: str, logo_block: str = "", subtitle: str = "") -> str:
    """Wraps a message in the system's professional purple-themed HTML layout."""
    if "<p" not in content and "<div" not in content:
        content = content.replace("\n", "<br>")

    return f"""
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f8f9fc;font-family:'Segoe UI',Arial,sans-serif;">
    <div style="padding: 20px 0; text-align: center;">
      {logo_block}
    </div>
    <div style="max-width:600px;margin:0 auto 40px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 10px 25px rgba(0,0,0,0.05);border:1px solid #eef0f5;">
      <div style="background:linear-gradient(135deg,#6366f1,#4f46e5);padding:40px;text-align:left;">
        <h1 style="color:#ffffff;margin:0;font-size:24px;font-weight:700;letter-spacing:-0.5px;">Proposal Ready</h1>
        {f'<p style="color:rgba(255,255,255,0.8);margin:8px 0 0;font-size:14px;font-weight:500;">{subtitle}</p>' if subtitle else ''}
      </div>
      <div style="padding:40px;font-size:16px;color:#334155;line-height:1.7;">
        {content}
      </div>
      <div style="background:#f1f5f9;padding:24px 40px;text-align:center;font-size:12px;color:#64748b;border-top:1px solid #e2e8f0;">
        <p style="margin:0;">This is an automated message from the <strong>Proposal Automation System</strong>.</p>
        <p style="margin:4px 0 0;">© 2026 All Rights Reserved.</p>
      </div>
    </div>
  </body>
</html>
"""


def _apply_placeholders(text: str, data: dict, mode: str = "html") -> str:
    """Replace {{placeholder}} tokens and wrap in the professional frame."""
    for key, value in data.items():
        # Handle {{key}}, {{ key }}, {{key }}, and {{ key}}
        for token in [f"{{{{{key}}}}}", f"{{{{ {key} }}}}", f"{{{{{key} }}}}", f"{{{{ {key}}}}}]".replace("]", "")]:
            text = text.replace(token, str(value))

    if mode == "html" and "<html>" not in text:
        logo_html = _get_logo_block()
        prop_num = data.get("proposal_number", "PROP-TEST-123")
        return wrap_in_professional_layout(text, logo_html, prop_num)

    return text


# ── Pydantic models ──────────────────────────────────────────────────────────

class CreateTemplateRequest(BaseModel):
    template_name: str
    subject: str
    body: str
    template_type: str = "CUSTOM"


class UpdateTemplateRequest(BaseModel):
    template_name: str
    subject: str
    body: str


class SetActiveTemplateRequest(BaseModel):
    template_id: int


class TestEmailRequest(BaseModel):
    to_email: str
    template_id: Optional[int] = None
    subject: Optional[str] = None
    body: Optional[str] = None


# ── CRUD endpoints ───────────────────────────────────────────────────────────

@router.get("/settings/email-templates")
def list_email_templates(db=Depends(get_db)):
    """Return all templates from client_email_templates with active indicator."""
    repo = PricingConfigRepository(db)
    repo.ensure_system_template_exists()

    templates = repo.get_all_email_templates()
    active_id = repo.get_active_template_id()

    # If no active selection yet, default to the SYSTEM template
    if active_id is None and templates:
        system_tpl = next((t for t in templates if t["template_type"] == "SYSTEM"), None)
        if system_tpl:
            active_id = system_tpl["id"]

    return {
        "templates": templates,
        "active_template_id": active_id,
        "placeholders": [
            {"key": "{{client_name}}", "label": "Client Name"},
            {"key": "{{proposal_number}}", "label": "Proposal Number"},
            {"key": "{{project_name}}", "label": "Project Name"},
            {"key": "{{total_price}}", "label": "Total Price"},
            {"key": "{{logo_block}}", "label": "Company Logo (auto)"},
        ],
    }


@router.get("/settings/email-templates/active")
def get_active_template(db=Depends(get_db)):
    """Return the currently active (global) email template."""
    repo = PricingConfigRepository(db)
    repo.ensure_system_template_exists()
    tpl = repo.get_active_template()
    if not tpl:
        raise HTTPException(status_code=404, detail="No active template found")
    return tpl


@router.get("/settings/email-templates/{template_id}")
def get_template_by_id(template_id: int, db=Depends(get_db)):
    """Return a single template by its ID."""
    repo = PricingConfigRepository(db)
    tpl = repo.get_email_template_by_id(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl


@router.post("/settings/email-templates")
def create_email_template(body: CreateTemplateRequest, db=Depends(get_db)):
    """Create a new CUSTOM email template."""
    if not body.template_name.strip():
        raise HTTPException(status_code=400, detail="Template name is required")
    if not body.subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required")

    repo = PricingConfigRepository(db)
    new_id = repo.create_email_template(
        template_name=body.template_name.strip(),
        subject=body.subject.strip(),
        body=body.body,
        template_type="CUSTOM",  # Users can only create CUSTOM templates
    )
    repo.commit()
    return {"success": True, "id": new_id, "message": f"Template '{body.template_name}' created"}


@router.put("/settings/email-templates/{template_id}")
def update_email_template(template_id: int, body: UpdateTemplateRequest, db=Depends(get_db)):
    """Update an existing email template (name, subject, body)."""
    if not body.template_name.strip():
        raise HTTPException(status_code=400, detail="Template name is required")

    repo = PricingConfigRepository(db)
    existing = repo.get_email_template_by_id(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    updated = repo.update_email_template(
        template_id=template_id,
        template_name=body.template_name.strip(),
        subject=body.subject.strip(),
        body=body.body,
    )
    repo.commit()
    return {"success": updated, "message": "Template updated"}


@router.delete("/settings/email-templates/{template_id}")
def delete_email_template(template_id: int, db=Depends(get_db)):
    """Delete a CUSTOM email template. SYSTEM templates cannot be deleted."""
    repo = PricingConfigRepository(db)
    existing = repo.get_email_template_by_id(template_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")
    if existing["template_type"] == "SYSTEM":
        raise HTTPException(status_code=400, detail="Cannot delete the system default template")

    # If deleting the active template, reset to SYSTEM
    active_id = repo.get_active_template_id()
    deleted = repo.delete_email_template(template_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Could not delete template")

    if active_id == template_id:
        # Reset active to the first SYSTEM template
        templates = repo.get_all_email_templates()
        system = next((t for t in templates if t["template_type"] == "SYSTEM"), None)
        if system:
            repo.set_active_template_id(system["id"])

    repo.commit()
    return {"success": True, "message": "Template deleted"}


@router.post("/settings/email-templates/set-active")
def set_active_template(body: SetActiveTemplateRequest, db=Depends(get_db)):
    """Set the globally active email template by its ID."""
    repo = PricingConfigRepository(db)
    tpl = repo.get_email_template_by_id(body.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    repo.set_active_template_id(body.template_id)
    repo.commit()
    return {
        "success": True,
        "message": f"'{tpl['template_name']}' is now the global email template",
        "active_template_id": body.template_id,
    }


# ── Test email endpoint ─────────────────────────────────────────────────────

@router.post("/settings/email-templates/test")
def send_test_email(body: TestEmailRequest, db=Depends(get_db)):
    """Send a test email using the active (or specified) template."""
    repo = PricingConfigRepository(db)
    repo.ensure_system_template_exists()

    # Determine template content
    if body.subject and body.body:
        subject_tpl = body.subject
        body_tpl = body.body
    elif body.template_id:
        tpl = repo.get_email_template_by_id(body.template_id)
        if not tpl:
            raise HTTPException(status_code=404, detail="Template not found")
        subject_tpl = tpl["subject"]
        body_tpl = tpl["body"]
    else:
        tpl = repo.get_active_template()
        if not tpl:
            raise HTTPException(status_code=404, detail="No active template found")
        subject_tpl = tpl["subject"]
        body_tpl = tpl["body"]

    # Sample data for placeholder replacement
    sample_data = {
        "client_name": "John Doe",
        "proposal_number": "PROP-20240305-120000",
        "project_name": "My Test Project",
        "total_price": "$12,500.00",
        "logo_block": _get_logo_block(),
    }

    rendered_subject = f"Test Mail: {_apply_placeholders(subject_tpl, sample_data, mode='text')}"
    rendered_body = _apply_placeholders(body_tpl, sample_data, mode="html")

    svc = EmailService()
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
