"""
Tests for PricingService — no database required.

Run:  pytest tests/test_pricing_service.py -v
"""

import pytest
from app.services.pricing_service import PricingService


@pytest.fixture
def svc():
    """PricingService with default (hardcoded) config — no DB needed."""
    return PricingService(config_repo=None)


# ── Database size ─────────────────────────────────────────────────────────────

class TestDatabaseSizePrice:
    def test_small_db_first_tier(self, svc):
        price = svc.calculate_database_size_price(50)
        assert price == 50 * 50  # $50/GB for ≤100 GB

    def test_boundary_first_tier(self, svc):
        price = svc.calculate_database_size_price(100)
        assert price == 100 * 50

    def test_second_tier(self, svc):
        price = svc.calculate_database_size_price(200)
        assert price == 200 * 40  # $40/GB for 101-500 GB

    def test_third_tier(self, svc):
        price = svc.calculate_database_size_price(600)
        assert price == 600 * 30

    def test_large_db_last_tier(self, svc):
        price = svc.calculate_database_size_price(2000)
        assert price == 2000 * 20

    def test_zero_size_raises_or_zero(self, svc):
        # Should return 0 without crashing
        price = svc.calculate_database_size_price(0)
        assert price == 0


# ── Runs ──────────────────────────────────────────────────────────────────────

class TestRunsPrice:
    def test_first_tier(self, svc):
        assert svc.calculate_runs_price(2) == 2 * 500

    def test_boundary_first_tier(self, svc):
        assert svc.calculate_runs_price(3) == 3 * 500

    def test_second_tier(self, svc):
        assert svc.calculate_runs_price(5) == 5 * 400

    def test_last_tier(self, svc):
        assert svc.calculate_runs_price(20) == 20 * 300


# ── Deployment ────────────────────────────────────────────────────────────────

class TestDeploymentPrice:
    def test_inhouse_vm(self, svc):
        assert svc.calculate_deployment_price("inhouse_vm") == 2000

    def test_client_premises(self, svc):
        assert svc.calculate_deployment_price("client_premises") == 3000

    def test_unknown_type_returns_zero(self, svc):
        assert svc.calculate_deployment_price("unknown") == 0


# ── Where clauses ─────────────────────────────────────────────────────────────

class TestWhereClauses:
    def test_no_where_clauses(self, svc):
        assert svc.calculate_where_clauses_price(False) == 0.0

    def test_with_where_clauses(self, svc):
        assert svc.calculate_where_clauses_price(True) == 500.0


# ── BIRT reports ──────────────────────────────────────────────────────────────

class TestBirtReports:
    def test_no_birt(self, svc):
        assert svc.calculate_birt_reports_price(False) == 0.0

    def test_bulk_complexity(self, svc):
        dist = {0: 10, 2: 5}  # 10 × $100 + 5 × $350 = $2750
        result = svc.calculate_birt_reports_price_bulk(dist)
        assert result["total"] == pytest.approx(2750.0)

    def test_bulk_breakdown_keys(self, svc):
        dist = {1: 3, 3: 2}
        result = svc.calculate_birt_reports_price_bulk(dist)
        assert 1 in result["breakdown"]
        assert 3 in result["breakdown"]

    def test_string_keys_normalised(self, svc):
        """JSON deserialisation may produce string keys — must still work."""
        dist = {"0": 5, "1": 3}
        result = svc.calculate_birt_reports_price_bulk(dist)  # type: ignore[arg-type]
        assert result["total"] > 0


# ── Total price ───────────────────────────────────────────────────────────────

class TestCalculateTotalPrice:
    def test_basic_total(self, svc):
        result = svc.calculate_total_price(
            database_size_gb=50,
            num_runs=2,
            deployment_type="inhouse_vm",
            has_where_clauses=False,
            has_birt_reports=False,
        )
        expected = (50 * 50) + (2 * 500) + 2000
        assert result["total_price"] == pytest.approx(expected)

    def test_total_includes_all_components(self, svc):
        result = svc.calculate_total_price(
            database_size_gb=100,
            num_runs=3,
            deployment_type="client_premises",
            has_where_clauses=True,
            has_birt_reports=True,
            birt_complexity_distribution={0: 10},
        )
        assert "database_size_price" in result
        assert "runs_price" in result
        assert "deployment_price" in result
        assert "where_clauses_price" in result
        assert "birt_reports_price" in result
        assert "subtotal" in result
        assert "total_price" in result

    def test_subtotal_equals_component_sum(self, svc):
        result = svc.calculate_total_price(
            database_size_gb=200,
            num_runs=5,
            deployment_type="inhouse_vm",
            has_where_clauses=True,
            has_birt_reports=True,
            birt_complexity_distribution={2: 20},
        )
        expected_subtotal = (
            result["database_size_price"]
            + result["runs_price"]
            + result["deployment_price"]
            + result["where_clauses_price"]
            + result["birt_reports_price"]
        )
        assert result["subtotal"] == pytest.approx(expected_subtotal)
