"""
Pricing Service — business logic for calculating proposal prices.

Migrated from pricing_engine.py with the same calculation logic,
but now receives dynamic DB config via PricingConfigRepository.
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from app.repositories.pricing_config_repository import PricingConfigRepository


# ── Default configuration (used when no DB config exists) ─────────────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "database_size_pricing": {
        "base_price": 100,
        "price_per_gb": 50,
        "tiers": [
            {"max_gb": 100, "price_per_gb": 50},
            {"max_gb": 500, "price_per_gb": 40},
            {"max_gb": 1000, "price_per_gb": 30},
            {"max_gb": None, "price_per_gb": 20},
        ]
    },
    "runs_pricing": {
        "base_price": 200,
        "price_per_run": 100,
        "bulk_discount": {
            "min_runs": 10,
            "discount_percent": 10
        }
    },
    "deployment_pricing": {
        "inhouse_vm": 2000,
        "client_premises": 3000,
    },
    "where_clauses_pricing": {"base_price": 500},
    "birt_reports_pricing": {
        "complexity_pricing": {
            0: {"price_per_report": 100, "description": "Simple"},
            1: {"price_per_report": 200, "description": "Low"},
            2: {"price_per_report": 350, "description": "Medium"},
            3: {"price_per_report": 500, "description": "High"},
            4: {"price_per_report": 750, "description": "Very High"},
            5: {"price_per_report": 1000, "description": "Complex"},
        }
    },
    "complexity_pricing": {
        "multipliers": {
            0: 1.0, 1: 1.1, 2: 1.25, 3: 1.5, 4: 1.75, 5: 2.0
        }
    },
    "usa_resource_pricing": {
        "surcharge_multiplier": 1.35
    },
    "maximo_upgrade_pricing": {
        "base_price": 1500,
        "price_per_feature": 500
    },
    "addon_installation_pricing": {
        "db2_installation": 500,
        "birt_installation": 500,
        "maximo_installation": 500,
    },
}


class PricingService:
    """
    Calculates all pricing components for a proposal.

    Pass a *PricingConfigRepository* (which wraps the db connection)
    to enable dynamic config loaded from the database.
    """

    def __init__(self, config_repo: Optional[PricingConfigRepository] = None) -> None:
        self._config_repo = config_repo

    # ── Config helpers ────────────────────────────────────────────────────────

    def _get_config(self, key: str) -> Any:
        """Return config value from DB if available, else use hardcoded defaults."""
        if self._config_repo:
            value = self._config_repo.get_raw_value(key)
            if value is not None:
                return value
        return DEFAULT_CONFIG.get(key, {})

    # ── Component calculators ─────────────────────────────────────────────────

    def calculate_database_size_price(self, size_gb: float) -> float:
        config = self._get_config("database_size_pricing")
        defaults = DEFAULT_CONFIG["database_size_pricing"]
        
        base_price = float(config.get("base_price", defaults["base_price"]))
        tiers = config.get("tiers", defaults["tiers"])
        default_ppg = float(config.get("price_per_gb", defaults["price_per_gb"]))
        
        variable_price = 0.0
        if tiers:
            found_tier = False
            for tier in tiers:
                if tier["max_gb"] is None or size_gb <= tier["max_gb"]:
                    variable_price = float(Decimal(str(size_gb)) * Decimal(str(tier["price_per_gb"])))
                    found_tier = True
                    break
            if not found_tier and tiers:
                variable_price = float(Decimal(str(size_gb)) * Decimal(str(tiers[-1]["price_per_gb"])))
        else:
            variable_price = float(Decimal(str(size_gb)) * Decimal(str(default_ppg)))
            
        return base_price + variable_price

    def calculate_runs_price(self, num_runs: int) -> float:
        config = self._get_config("runs_pricing")
        defaults = DEFAULT_CONFIG["runs_pricing"]
        
        base_price = float(config.get("base_price", defaults["base_price"]))
        ppr = float(config.get("price_per_run", defaults["price_per_run"]))
        
        total_runs_price = float(Decimal(str(num_runs)) * Decimal(str(ppr)))
        
        # Apply bulk discount
        discount_config = config.get("bulk_discount", defaults["bulk_discount"])
        min_runs = int(discount_config.get("min_runs", 10))
        discount_pct = float(discount_config.get("discount_percent", 0))
        
        if num_runs >= min_runs and discount_pct > 0:
            multiplier = Decimal(str(1 - (discount_pct / 100)))
            total_runs_price = float(Decimal(str(total_runs_price)) * multiplier)
            
        return base_price + total_runs_price

    def calculate_deployment_price(self, deployment_type: str) -> float:
        config = self._get_config("deployment_pricing")
        return float(config.get(deployment_type, 0))

    def calculate_where_clauses_price(self, has_where_clauses: bool) -> float:
        if not has_where_clauses:
            return 0.0
        config = self._get_config("where_clauses_pricing")
        return float(config.get("base_price", 500))

    def calculate_birt_reports_price_bulk(
        self, complexity_distribution: Dict[int, int]
    ) -> Dict[str, Any]:
        """
        Calculate BIRT price from a {complexity_score: report_count} dict.

        Returns a breakdown dict AND the total price.
        """
        config = self._get_config("birt_reports_pricing")
        defaults = DEFAULT_CONFIG["birt_reports_pricing"]
        
        complexity_pricing = config.get(
            "complexity_pricing",
            defaults["complexity_pricing"],
        )
        # Normalise keys to int (JSON serialises them as strings)
        complexity_pricing = {int(k): v for k, v in complexity_pricing.items()}

        breakdown: Dict[int, Dict[str, Any]] = {}
        total = 0.0
        for score, count in complexity_distribution.items():
            if count <= 0:
                continue
            score = int(score)
            pricing = complexity_pricing.get(score, {"price_per_report": 100, "description": "Unknown"})
            ppr = float(pricing.get("price_per_report", 100))
            sub = ppr * count
            total += sub
            breakdown[score] = {
                "num_reports": count,
                "price_per_report": ppr,
                "total_price": sub,
                "description": pricing.get("description", ""),
            }
        return {"breakdown": breakdown, "total": total}

    def calculate_birt_reports_price(
        self,
        has_birt_reports: bool,
        num_reports: int = 1,
        complexity_distribution: Optional[Dict[int, int]] = None,
    ) -> float:
        if not has_birt_reports:
            return 0.0
        if complexity_distribution:
            result = self.calculate_birt_reports_price_bulk(complexity_distribution)
            return result["total"]
        # Fallback: treat all reports as complexity-0
        dist = {0: num_reports}
        result = self.calculate_birt_reports_price_bulk(dist)
        return result["total"]

    def get_complexity_multiplier(self, complexity_score: int) -> float:
        config = self._get_config("complexity_pricing")
        defaults = DEFAULT_CONFIG["complexity_pricing"]
        multipliers = config.get("multipliers", defaults["multipliers"])
        # JSON keys are strings
        return float(multipliers.get(str(complexity_score), multipliers.get(complexity_score, 1.0)))

    def calculate_maximo_upgrade_price(
        self,
        has_maximo_upgrade: bool = False,
        has_addon: bool = False,
    ) -> float:
        """Return Maximo upgrade price based on selection flags.

        Rules:
          - Not checked       -> 0
          - Checked, no addon -> base_price
          - Checked + addon   -> base_price + price_per_feature
        """
        if not has_maximo_upgrade:
            return 0.0
        config = self._get_config("maximo_upgrade_pricing")
        defaults = DEFAULT_CONFIG["maximo_upgrade_pricing"]
        
        base = float(config.get("base_price", defaults["base_price"]))
        per_feature = float(config.get("price_per_feature", defaults["price_per_feature"])) if has_addon else 0.0
        return base + per_feature

    def calculate_addon_installation_price(
        self,
        addon_db2: bool = False,
        addon_birt: bool = False,
        addon_maximo: bool = False,
    ) -> Dict[str, float]:
        """Return a dict with individual and combined add-on installation prices."""
        config = self._get_config("addon_installation_pricing")
        defaults = DEFAULT_CONFIG["addon_installation_pricing"]
        
        db2_price = float(config.get("db2_installation", defaults["db2_installation"])) if addon_db2 else 0.0
        birt_price = float(config.get("birt_installation", defaults["birt_installation"])) if addon_birt else 0.0
        maximo_price = float(config.get("maximo_installation", defaults["maximo_installation"])) if addon_maximo else 0.0
        return {
            "db2_installation_price": db2_price,
            "birt_installation_price": birt_price,
            "maximo_installation_price": maximo_price,
            "total": db2_price + birt_price + maximo_price,
        }

    # ── Main entry point ──────────────────────────────────────────────────────

    def calculate_total_price(
        self,
        database_size_gb: float,
        num_runs: int,
        deployment_type: str,
        has_where_clauses: bool,
        has_birt_reports: bool,
        complexity_score: int = 0,
        num_birt_reports: int = 1,
        birt_complexity_distribution: Optional[Dict[int, int]] = None,
        has_maximo_upgrade: bool = False,
        maximo_has_addon: bool = False,
        addon_db2_installation: bool = False,
        addon_birt_installation: bool = False,
        addon_maximo_installation: bool = False,
        usa_based_resources: bool = False,
    ) -> Dict[str, Any]:
        """
        Compute all price components and return a full breakdown dict.
        """
        db_price = self.calculate_database_size_price(database_size_gb)
        runs_price = self.calculate_runs_price(num_runs)
        deployment_price = self.calculate_deployment_price(deployment_type)
        where_price = self.calculate_where_clauses_price(has_where_clauses)
        maximo_price = self.calculate_maximo_upgrade_price(has_maximo_upgrade, maximo_has_addon)

        # Add-On Installation Services
        addon_prices = self.calculate_addon_installation_price(
            addon_db2=addon_db2_installation,
            addon_birt=addon_birt_installation,
            addon_maximo=addon_maximo_installation,
        )
        addon_total = addon_prices["total"]

        birt_breakdown_data: Optional[Dict[str, Any]] = None
        if has_birt_reports and birt_complexity_distribution:
            birt_result = self.calculate_birt_reports_price_bulk(birt_complexity_distribution)
            birt_price = birt_result["total"]
            birt_breakdown_data = birt_result["breakdown"]
        else:
            birt_price = self.calculate_birt_reports_price(
                has_birt_reports, num_birt_reports
            )

        subtotal = (
            db_price + runs_price + deployment_price + where_price
            + birt_price + maximo_price + addon_total
        )
        total_price = subtotal  # extend here if tax / discount needed

        result: Dict[str, Any] = {
            "database_size_price": db_price,
            "runs_price": runs_price,
            "deployment_price": deployment_price,
            "where_clauses_price": where_price,
            "birt_reports_price": birt_price,
            "maximo_upgrade_price": maximo_price,
            "addon_db2_installation_price": addon_prices["db2_installation_price"],
            "addon_birt_installation_price": addon_prices["birt_installation_price"],
            "addon_maximo_installation_price": addon_prices["maximo_installation_price"],
            "subtotal": subtotal,
            "total_price": total_price,
        }
        if birt_breakdown_data:
            result["birt_complexity_breakdown"] = birt_breakdown_data

        # ── USA-based resources surcharge (+35% default) ───────────────────
        if usa_based_resources:
            usa_config = self._get_config("usa_resource_pricing")
            defaults = DEFAULT_CONFIG["usa_resource_pricing"]
            multiplier_val = float(usa_config.get("surcharge_multiplier", defaults["surcharge_multiplier"]))
            
            surcharge_multiplier = Decimal(str(multiplier_val))
            surchargeified_total = float(Decimal(str(total_price)) * surcharge_multiplier)
            
            surcharge_amount = float(Decimal(str(total_price)) * (surcharge_multiplier - 1))
            result["usa_resources_surcharge"] = round(surcharge_amount, 2)
            result["usa_resources_multiplier"] = multiplier_val
            result["total_price"] = surchargeified_total

        return result
