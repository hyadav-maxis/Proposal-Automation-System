"""
Tests for ProposalService — uses a mock/fake DB connection.

Run:  pytest tests/test_proposal_service.py -v
"""

import pytest
from unittest.mock import MagicMock, patch, call

from app.schemas.proposal import ProposalCreate


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_fake_db():
    """Return a minimal fake psycopg2 connection."""
    fake_cursor = MagicMock()
    fake_cursor.fetchone.return_value = (42,)  # proposal id
    fake_db = MagicMock()
    fake_db.cursor.return_value = fake_cursor
    return fake_db, fake_cursor


def _basic_request(**overrides) -> ProposalCreate:
    defaults = dict(
        client_name="Acme Corp",
        client_email="acme@example.com",
        project_name="DB Migration",
        database_size_gb=50.0,
        number_of_runs=2,
        deployment_type="inhouse_vm",
        has_where_clauses=False,
        has_birt_reports=False,
    )
    defaults.update(overrides)
    return ProposalCreate(**defaults)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestProposalServiceCreate:
    def test_returns_proposal_response(self):
        """Happy path — creates a proposal and returns a ProposalResponse."""
        from app.services.proposal_service import ProposalService

        fake_db, fake_cursor = _make_fake_db()

        # Patch PricingConfigRepository so it doesn't query the DB
        with patch(
            "app.services.proposal_service.PricingConfigRepository"
        ) as MockConfigRepo:
            MockConfigRepo.return_value.get_raw_value.return_value = None

            svc = ProposalService(fake_db)
            response = svc.create_proposal(_basic_request())

        assert response.proposal_id == 42
        assert response.proposal_number.startswith("PROP-")
        assert response.total_price > 0

    def test_invalid_complexity_score_raises(self):
        """Complexity score outside 0-5 should raise HTTP 400."""
        from fastapi import HTTPException
        from app.services.proposal_service import ProposalService

        fake_db, _ = _make_fake_db()

        with patch("app.services.proposal_service.PricingConfigRepository"):
            svc = ProposalService(fake_db)
            with pytest.raises(HTTPException) as exc_info:
                svc.create_proposal(
                    _basic_request(
                        has_birt_reports=True,
                        birt_complexity_distribution={9: 5},  # invalid score
                    )
                )
        assert exc_info.value.status_code == 400

    def test_empty_complexity_distribution_raises(self):
        """An all-zero complexity distribution should raise HTTP 400."""
        from fastapi import HTTPException
        from app.services.proposal_service import ProposalService

        fake_db, _ = _make_fake_db()

        with patch("app.services.proposal_service.PricingConfigRepository"):
            svc = ProposalService(fake_db)
            with pytest.raises(HTTPException) as exc_info:
                svc.create_proposal(
                    _basic_request(
                        has_birt_reports=True,
                        birt_complexity_distribution={0: 0, 1: 0},
                    )
                )
        assert exc_info.value.status_code == 400

    def test_db_rollback_on_exception(self):
        """If the DB insert raises, rollback must be called."""
        from app.services.proposal_service import ProposalService

        fake_db = MagicMock()
        fake_db.cursor.side_effect = RuntimeError("DB exploded")

        with patch("app.services.proposal_service.PricingConfigRepository"):
            svc = ProposalService(fake_db)
            with pytest.raises(Exception):
                svc.create_proposal(_basic_request())

        fake_db.rollback.assert_called()


class TestProposalServiceGet:
    def test_not_found_raises_404(self):
        """get_proposal with unknown id should raise HTTP 404."""
        from fastapi import HTTPException
        from app.services.proposal_service import ProposalService

        fake_db, _ = _make_fake_db()

        with patch("app.services.proposal_service.PricingConfigRepository"), \
             patch(
                 "app.services.proposal_service.ProposalRepository"
             ) as MockRepo:
            MockRepo.return_value.get_proposal_by_id.return_value = None
            svc = ProposalService(fake_db)
            with pytest.raises(HTTPException) as exc_info:
                svc.get_proposal(9999)
        assert exc_info.value.status_code == 404
