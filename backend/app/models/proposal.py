"""Pydantic models for Proposals."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProposalCreate(BaseModel):
    """Request body for creating a new proposal."""

    client_name: str
    client_email: Optional[str] = None
    project_name: str
    database_size_gb: float = Field(..., gt=0)
    number_of_runs: int = Field(..., gt=0)
    deployment_type: str = Field(..., pattern="^(inhouse_vm|client_premises)$")
    # Resource location: 'standard' (default) or 'US_based' (+35%)
    resource_location: str = Field(default="standard", pattern="^(standard|US_based)$")
    has_where_clauses: bool = False
    has_birt_reports: bool = False
    num_birt_reports: int = 1
    # Bulk complexity distribution: {0: 50, 1: 30, 2: 100, …}
    birt_complexity_distribution: Optional[Dict[int, int]] = None
    has_maximo_upgrade: bool = False
    maximo_has_addon: bool = False
    # Add-On Installation Services
    addon_db2_installation: bool = False
    addon_birt_installation: bool = False
    addon_maximo_installation: bool = False
    source_dialect: Optional[str] = None
    target_dialect: Optional[str] = None
    sql_content: Optional[str] = None


class ProposalResponse(BaseModel):
    """Response body after creating a proposal."""

    proposal_id: int
    proposal_number: str
    total_price: float
    pricing_breakdown: Dict[str, Any]
    complexity_analysis: Optional[Dict[str, Any]] = None
