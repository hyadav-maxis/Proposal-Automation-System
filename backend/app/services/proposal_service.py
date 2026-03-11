"""
Proposal Service — orchestrates proposal creation business logic.

This layer knows about both the PricingService and the
ProposalRepository, but does NOT import from FastAPI.
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException

from app.repositories.proposal_repository import ProposalRepository
from app.repositories.pricing_config_repository import PricingConfigRepository
from app.models.proposal import ProposalCreate, ProposalResponse
from app.services.pricing_service import PricingService
from app.services.export_service import ExportService
from app.services.email_service import EmailService


class ProposalService:
    """Handles all business logic related to proposals."""

    def __init__(self, db) -> None:
        self._repo = ProposalRepository(db)
        config_repo = PricingConfigRepository(db)
        self._pricing = PricingService(config_repo=config_repo)
        self._export = ExportService()
        self._email = EmailService()

    # ── Create ────────────────────────────────────────────────────────────────

    def create_proposal(self, request: ProposalCreate) -> ProposalResponse:
        """Validate input, calculate pricing, persist, and return response."""

        # Validate complexity distribution
        if request.birt_complexity_distribution:
            total_reports = sum(request.birt_complexity_distribution.values())
            if total_reports == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Complexity distribution must have at least one report",
                )
            for score in request.birt_complexity_distribution:
                if score < 0 or score > 5:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Complexity score must be 0-5, got {score}",
                    )

        proposal_number = (
            f"PROP-{datetime.now().strftime('%Y%m%d')}-"
            f"{datetime.now().strftime('%H%M%S')}"
        )

        try:
            # Calculate pricing
            pricing = self._pricing.calculate_total_price(
                database_size_gb=request.database_size_gb,
                num_runs=request.number_of_runs,
                deployment_type=request.deployment_type,
                has_where_clauses=request.has_where_clauses,
                has_birt_reports=request.has_birt_reports,
                complexity_score=0,
                num_birt_reports=request.num_birt_reports,
                birt_complexity_distribution=request.birt_complexity_distribution,
                has_maximo_upgrade=request.has_maximo_upgrade,
                maximo_has_addon=request.maximo_has_addon,
                addon_db2_installation=request.addon_db2_installation,
                addon_birt_installation=request.addon_birt_installation,
                addon_maximo_installation=request.addon_maximo_installation,
                us_based_resources=(request.resource_location == "US_based"),
            )

            proposal_id = self._repo.insert_proposal(
                proposal_number=proposal_number,
                client_name=request.client_name,
                client_email=request.client_email,
                project_name=request.project_name,
                total_price=pricing["total_price"],
            )

            complexity_reason = (
                "Complexity factored into BIRT pricing"
                if request.birt_complexity_distribution
                else None
            )
            self._repo.insert_proposal_details(
                proposal_id=proposal_id,
                database_size_gb=request.database_size_gb,
                number_of_runs=request.number_of_runs,
                deployment_type=request.deployment_type,
                has_where_clauses=request.has_where_clauses,
                has_birt_reports=request.has_birt_reports,
                complexity_score=0,
                complexity_reason=complexity_reason,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                sql_content=request.sql_content,
                resource_location=request.resource_location,
            )

            # Pricing components
            db_sz = pricing["database_size_price"]
            runs_p = pricing["runs_price"]
            dep_p = pricing["deployment_price"]

            self._repo.insert_pricing_component(
                proposal_id, "database_size", "Database Size",
                request.database_size_gb,
                db_sz / request.database_size_gb if request.database_size_gb > 0 else 0,
                db_sz,
            )
            self._repo.insert_pricing_component(
                proposal_id, "runs", "Number of Runs",
                request.number_of_runs,
                runs_p / request.number_of_runs if request.number_of_runs > 0 else 0,
                runs_p,
            )
            self._repo.insert_pricing_component(
                proposal_id, "deployment", "Deployment Type",
                1, dep_p, dep_p,
            )
            if request.has_where_clauses:
                wc_p = pricing["where_clauses_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "where_clauses", "WHERE Clauses", 1, wc_p, wc_p,
                )

            if request.has_birt_reports:
                if request.birt_complexity_distribution:
                    for score, count in request.birt_complexity_distribution.items():
                        if count > 0:
                            bkd = pricing.get("birt_complexity_breakdown", {}).get(score, {})
                            self._repo.insert_complexity_breakdown(
                                proposal_id, score, count,
                                bkd.get("price_per_report", 0),
                                bkd.get("total_price", 0),
                            )
                    total_birt = sum(request.birt_complexity_distribution.values())
                    self._repo.insert_pricing_component(
                        proposal_id, "birt_reports", "BIRT Reports (Complexity-Based)",
                        total_birt, 0, pricing["birt_reports_price"],
                    )
                else:
                    birt_p = pricing["birt_reports_price"]
                    ppr = birt_p / request.num_birt_reports if request.num_birt_reports > 0 else 0
                    self._repo.insert_pricing_component(
                        proposal_id, "birt_reports", "BIRT Reports",
                        request.num_birt_reports, ppr, birt_p,
                    )

            if request.has_maximo_upgrade:
                maximo_p = pricing["maximo_upgrade_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "maximo_upgrade", "Maximo Upgrade Feature",
                    1, maximo_p, maximo_p,
                )

            # Add-On Installation Services
            if request.addon_db2_installation:
                p = pricing["addon_db2_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_db2_installation", "Db2 Installation",
                    1, p, p,
                )
            if request.addon_birt_installation:
                p = pricing["addon_birt_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_birt_installation", "Birt Installation",
                    1, p, p,
                )
            if request.addon_maximo_installation:
                p = pricing["addon_maximo_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_maximo_installation", "Maximo Installation",
                    1, p, p,
                )

            # USA-based resources surcharge line item
            if request.resource_location == "US_based" and pricing.get("us_resources_surcharge"):
                sur = pricing["us_resources_surcharge"]
                self._repo.insert_pricing_component(
                    proposal_id, "us_resources_surcharge", "US-Based Resources (+35%)",
                    1, sur, sur,
                )

            self._repo.commit()

            complexity_analysis: Optional[Dict[str, Any]] = None
            if request.birt_complexity_distribution:
                complexity_analysis = {
                    "complexity_distribution": request.birt_complexity_distribution,
                    "birt_breakdown": pricing.get("birt_complexity_breakdown"),
                }

            return ProposalResponse(
                proposal_id=proposal_id,
                proposal_number=proposal_number,
                total_price=pricing["total_price"],
                pricing_breakdown=pricing,
                complexity_analysis=complexity_analysis,
            )

        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error creating proposal: {exc}"
            ) from exc

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_proposal(self, proposal_id: int) -> Dict[str, Any]:
        """Return a detailed proposal dict for the GET /api/proposals/{id} endpoint."""
        data = self._repo.get_proposal_by_id(proposal_id)
        if not data:
            raise HTTPException(status_code=404, detail="Proposal not found")

        proposal = data["proposal"]
        components = data["components"]
        complexity_breakdown = data["complexity_breakdown"]

        pricing_breakdown: Dict[str, Any] = {
            "database_size_price": 0, "runs_price": 0, "deployment_price": 0,
            "where_clauses_price": 0, "birt_reports_price": 0,
            "maximo_upgrade_price": 0,
            "addon_db2_installation_price": 0,
            "addon_birt_installation_price": 0,
            "addon_maximo_installation_price": 0,
            "subtotal": 0, "total_price": float(proposal.get("total_price") or 0),
        }
        _MAP = {
            "database_size": "database_size_price",
            "runs": "runs_price",
            "deployment": "deployment_price",
            "where_clauses": "where_clauses_price",
            "birt_reports": "birt_reports_price",
            "maximo_upgrade": "maximo_upgrade_price",
            "addon_db2_installation": "addon_db2_installation_price",
            "addon_birt_installation": "addon_birt_installation_price",
            "addon_maximo_installation": "addon_maximo_installation_price",
            "us_resources_surcharge": "us_resources_surcharge",
        }
        for c in components:
            key = _MAP.get(c["component_type"])
            if key:
                pricing_breakdown[key] = float(c.get("total_price") or 0)

        pricing_breakdown["subtotal"] = sum(
            pricing_breakdown[k]
            for k in [
                "database_size_price", "runs_price", "deployment_price",
                "where_clauses_price", "birt_reports_price", "maximo_upgrade_price",
                "addon_db2_installation_price", "addon_birt_installation_price",
                "addon_maximo_installation_price",
            ]
        )

        birt_breakdown: Dict[int, Any] = {}
        for cb in complexity_breakdown:
            score = cb["complexity_score"]
            birt_breakdown[score] = {
                "num_reports": cb["number_of_reports"],
                "price_per_report": float(cb.get("price_per_report") or 0),
                "total_price": float(cb.get("total_price") or 0),
                "description": "",
            }
        if birt_breakdown:
            pricing_breakdown["birt_complexity_breakdown"] = birt_breakdown

        proposal["pricing_components"] = components
        proposal["complexity_breakdown"] = complexity_breakdown
        proposal["pricing_breakdown"] = pricing_breakdown

        # Derive has_maximo_upgrade from component types
        comp_types = {c["component_type"] for c in components}
        proposal["has_maximo_upgrade"] = "maximo_upgrade" in comp_types
        # maximo_has_addon cannot be reconstructed from stored data reliably;
        # default to False (user can re-check if needed)
        proposal["maximo_has_addon"] = False

        # Reconstruct add-on installation flags from component types
        proposal["addon_db2_installation"] = "addon_db2_installation" in comp_types
        proposal["addon_birt_installation"] = "addon_birt_installation" in comp_types
        proposal["addon_maximo_installation"] = "addon_maximo_installation" in comp_types

        # Reconstruct birt_complexity_distribution from stored breakdown
        birt_dist: Dict[int, int] = {}
        for cb in complexity_breakdown:
            birt_dist[cb["complexity_score"]] = cb["number_of_reports"]
        proposal["birt_complexity_distribution"] = birt_dist if birt_dist else None

        return proposal

    def list_proposals(self, location: Optional[str] = None):
        return self._repo.list_proposals(location=location)

    def delete_proposal(self, proposal_id: int) -> dict:
        """Delete a proposal and all related data."""
        try:
            deleted = self._repo.delete_proposal(proposal_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Proposal not found")
            self._repo.commit()
            return {"message": "Proposal deleted successfully", "proposal_id": proposal_id}
        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error deleting proposal: {exc}"
            ) from exc

    def update_proposal(self, proposal_id: int, update_data: dict) -> dict:
        """Update editable fields of a proposal."""
        allowed_keys = {"client_name", "client_email", "project_name", "status"}
        filtered = {k: v for k, v in update_data.items() if k in allowed_keys}
        if not filtered:
            raise HTTPException(
                status_code=400, detail="No valid fields provided for update"
            )
        try:
            updated = self._repo.update_proposal(proposal_id, **filtered)
            if not updated:
                raise HTTPException(status_code=404, detail="Proposal not found")
            self._repo.commit()
            return {"message": "Proposal updated successfully", "proposal_id": proposal_id}
        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error updating proposal: {exc}"
            ) from exc

    def recalculate_proposal(self, proposal_id: int, request: ProposalCreate) -> ProposalResponse:
        """Recalculate pricing for an existing proposal and replace all related data."""
        # Validate that the proposal exists
        existing = self._repo.get_proposal_by_id(proposal_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # Validate complexity distribution
        if request.birt_complexity_distribution:
            total_reports = sum(request.birt_complexity_distribution.values())
            if total_reports == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Complexity distribution must have at least one report",
                )

        try:
            # Recalculate pricing
            pricing = self._pricing.calculate_total_price(
                database_size_gb=request.database_size_gb,
                num_runs=request.number_of_runs,
                deployment_type=request.deployment_type,
                has_where_clauses=request.has_where_clauses,
                has_birt_reports=request.has_birt_reports,
                complexity_score=0,
                num_birt_reports=request.num_birt_reports,
                birt_complexity_distribution=request.birt_complexity_distribution,
                has_maximo_upgrade=request.has_maximo_upgrade,
                maximo_has_addon=request.maximo_has_addon,
                addon_db2_installation=request.addon_db2_installation,
                addon_birt_installation=request.addon_birt_installation,
                addon_maximo_installation=request.addon_maximo_installation,
                us_based_resources=(request.resource_location == "US_based"),
            )

            # Update proposal basic fields + total_price
            self._repo.update_proposal(
                proposal_id,
                client_name=request.client_name,
                client_email=request.client_email,
                project_name=request.project_name,
            )
            self._repo.update_proposal_total_price(proposal_id, pricing["total_price"])

            # Replace proposal_details
            complexity_reason = (
                "Complexity factored into BIRT pricing"
                if request.birt_complexity_distribution
                else None
            )
            self._repo.replace_proposal_details(
                proposal_id=proposal_id,
                database_size_gb=request.database_size_gb,
                number_of_runs=request.number_of_runs,
                deployment_type=request.deployment_type,
                has_where_clauses=request.has_where_clauses,
                has_birt_reports=request.has_birt_reports,
                complexity_score=0,
                complexity_reason=complexity_reason,
                source_dialect=request.source_dialect,
                target_dialect=request.target_dialect,
                sql_content=request.sql_content,
                resource_location=request.resource_location,
            )

            # Clear and re-insert pricing components
            self._repo.delete_pricing_components(proposal_id)
            self._repo.delete_complexity_breakdown(proposal_id)

            db_sz = pricing["database_size_price"]
            runs_p = pricing["runs_price"]
            dep_p = pricing["deployment_price"]

            self._repo.insert_pricing_component(
                proposal_id, "database_size", "Database Size",
                request.database_size_gb,
                db_sz / request.database_size_gb if request.database_size_gb > 0 else 0,
                db_sz,
            )
            self._repo.insert_pricing_component(
                proposal_id, "runs", "Number of Runs",
                request.number_of_runs,
                runs_p / request.number_of_runs if request.number_of_runs > 0 else 0,
                runs_p,
            )
            self._repo.insert_pricing_component(
                proposal_id, "deployment", "Deployment Type",
                1, dep_p, dep_p,
            )
            if request.has_where_clauses:
                wc_p = pricing["where_clauses_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "where_clauses", "WHERE Clauses", 1, wc_p, wc_p,
                )

            if request.has_birt_reports:
                if request.birt_complexity_distribution:
                    for score, count in request.birt_complexity_distribution.items():
                        if count > 0:
                            bkd = pricing.get("birt_complexity_breakdown", {}).get(score, {})
                            self._repo.insert_complexity_breakdown(
                                proposal_id, score, count,
                                bkd.get("price_per_report", 0),
                                bkd.get("total_price", 0),
                            )
                    total_birt = sum(request.birt_complexity_distribution.values())
                    self._repo.insert_pricing_component(
                        proposal_id, "birt_reports", "BIRT Reports (Complexity-Based)",
                        total_birt, 0, pricing["birt_reports_price"],
                    )
                else:
                    birt_p = pricing["birt_reports_price"]
                    ppr = birt_p / request.num_birt_reports if request.num_birt_reports > 0 else 0
                    self._repo.insert_pricing_component(
                        proposal_id, "birt_reports", "BIRT Reports",
                        request.num_birt_reports, ppr, birt_p,
                    )

            if request.has_maximo_upgrade:
                maximo_p = pricing["maximo_upgrade_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "maximo_upgrade", "Maximo Upgrade Feature",
                    1, maximo_p, maximo_p,
                )

            # Add-On Installation Services
            if request.addon_db2_installation:
                p = pricing["addon_db2_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_db2_installation", "Db2 Installation",
                    1, p, p,
                )
            if request.addon_birt_installation:
                p = pricing["addon_birt_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_birt_installation", "Birt Installation",
                    1, p, p,
                )
            if request.addon_maximo_installation:
                p = pricing["addon_maximo_installation_price"]
                self._repo.insert_pricing_component(
                    proposal_id, "addon_maximo_installation", "Maximo Installation",
                    1, p, p,
                )

            # USA-based resources surcharge line item
            if request.resource_location == "US_based" and pricing.get("us_resources_surcharge"):
                sur = pricing["us_resources_surcharge"]
                self._repo.insert_pricing_component(
                    proposal_id, "us_resources_surcharge", "US-Based Resources (+35%)",
                    1, sur, sur,
                )

            self._repo.commit()

            complexity_analysis: Optional[Dict[str, Any]] = None
            if request.birt_complexity_distribution:
                complexity_analysis = {
                    "complexity_distribution": request.birt_complexity_distribution,
                    "birt_breakdown": pricing.get("birt_complexity_breakdown"),
                }

            return ProposalResponse(
                proposal_id=proposal_id,
                proposal_number=existing["proposal"]["proposal_number"],
                total_price=pricing["total_price"],
                pricing_breakdown=pricing,
                complexity_analysis=complexity_analysis,
            )

        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error recalculating proposal: {exc}"
            ) from exc

    def get_for_export(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Return proposal_data dict ready for PDF/Excel export."""
        raw = self._repo.get_proposal_for_export(proposal_id)
        if not raw:
            return None

        row = raw["row"]
        components = raw["components"]
        breakdown = raw["breakdown"]

        pricing: Dict[str, Any] = {
            "subtotal": 0,
            "total_price": float(row.get("total_price") or 0),
        }
        
        # Populate pricing from components
        for c in components:
            pricing[c["component_type"]] = {
                "name": c["component_name"],
                "quantity": float(c.get("quantity") or 0),
                "unit_price": float(c.get("unit_price") or 0),
                "total_price": float(c.get("total_price") or 0),
            }

        # Calculate subtotal (sum of everything except surcharge)
        subtotal = 0.0
        for c in components:
            if c["component_type"] != "us_resources_surcharge":
                subtotal += float(c.get("total_price") or 0)
        pricing["subtotal"] = subtotal

        birt_breakdown = {
            cb["complexity_score"]: {
                "num_reports": cb["number_of_reports"],
                "price_per_report": float(cb.get("price_per_report") or 0),
                "total_price": float(cb.get("total_price") or 0),
            }
            for cb in breakdown
        }
        if birt_breakdown:
            pricing["birt_complexity_breakdown"] = birt_breakdown

        return {
            "proposal_number": row["proposal_number"],
            "client_name": row["client_name"],
            "project_name": row.get("project_name") or "",
            "database_size_gb": row.get("database_size_gb"),
            "number_of_runs": row.get("number_of_runs"),
            "deployment_type": row.get("deployment_type"),
            "has_where_clauses": row.get("has_where_clauses"),
            "has_birt_reports": row.get("has_birt_reports"),
            "resource_location": row.get("resource_location"),
            "pricing_breakdown": pricing,
        }

    def send_proposal_via_email(self, proposal_id: int) -> bool:
        """Fetch proposal, generate PDF, and send via email using the saved template."""
        # 1. Get proposal data
        proposal_data = self.get_for_export(proposal_id)
        if not proposal_data:
            raise HTTPException(status_code=404, detail="Proposal not found")

        # 2. Get client email from repo
        raw_proposal = self._repo.get_proposal_by_id(proposal_id)
        client_email = raw_proposal["proposal"].get("client_email")

        if not client_email:
            raise HTTPException(
                status_code=400,
                detail="Client email is missing for this proposal. Please update the proposal first.",
            )

        # 3. Load template: Check for client-specific override first, then global config
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

        client_tpl = self._pricing._config_repo.get_client_template(client_email)
        
        if client_tpl:
            subject_tpl = client_tpl["subject"]
            body_tpl = client_tpl["body"]
            # Smart detection: defaults to plain if no obvious HTML tags found
            has_html = bool(re.search(r'<[a-z][\s\S]*>', body_tpl, re.IGNORECASE))
            mode = "html" if has_html else "plain"
        else:
            subject_tpl = self._pricing._config_repo.get_raw_value("email_template_subject") or _DEFAULT_SUBJECT
            mode = self._pricing._config_repo.get_raw_value("email_template_mode") or "html"
            body_tpl = self._pricing._config_repo.get_raw_value("email_template_body")
            
            if not body_tpl:
                body_tpl = _DEFAULT_PLAIN_BODY if mode == "plain" else _DEFAULT_BODY

        # 4. Build logo block (looks for company_logo.* in the static folder)
        import os as _os
        _ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
        _STATIC_DIR = _os.path.join(_ROOT, "static")
        logo_block = ""
        for _ext in ("png", "jpg", "jpeg"):
            _p = _os.path.join(_STATIC_DIR, f"company_logo.{_ext}")
            if _os.path.isfile(_p):
                logo_url = "http://localhost:8000"  # Fallback
                logo_block = (
                    f'<div style="text-align:center;padding:24px 36px 0;">'
                    f'<img src="{logo_url}/static/company_logo.{_ext}" '
                    f'alt="Company Logo" style="max-height:70px;max-width:220px;object-fit:contain;" /></div>'
                )
                break

        # 5. Replace placeholders
        replacements = {
            "client_name": proposal_data["client_name"],
            "proposal_number": proposal_data["proposal_number"],
            "project_name": proposal_data["project_name"],
            "logo_block": logo_block,
        }
        for key, val in replacements.items():
            subject_tpl = subject_tpl.replace(f"{{{{{key}}}}}", str(val))
            body_tpl = body_tpl.replace(f"{{{{{key}}}}}", str(val))

        # 6. Apply professional layout if in plain text mode
        if mode == "plain":
            safe_msg = body_tpl.replace("\n", "<br>")
            body_tpl = f"""<html>
  <body style="margin:0;padding:0;background:#f8f9fc;font-family:'Segoe UI',Arial,sans-serif;">
    {logo_block}
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

        # 7. Generate PDF
        pdf_bytes = self._export.generate_pdf(proposal_data)

        # 8. Send Email
        filename = f"Proposal_{proposal_data['proposal_number']}.pdf"
        success = self._email.send_email_with_attachment(
            to_email=client_email,
            subject=subject_tpl,
            body=body_tpl,
            attachment_bytes=pdf_bytes,
            attachment_filename=filename,
        )

        if success:
            self._repo.update_proposal(proposal_id, status="sent")
            self._repo.commit()
            return True

        return False
