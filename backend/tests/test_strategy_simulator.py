"""
backend/tests/test_strategy_simulator.py

Unit tests for Strategy Engine and What-If Simulator endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.strategy.engine import recommend_strategy
from backend.simulation.simulator import compare_strategies

client = TestClient(app)


# ------------------------------------------------------------------ #
# Strategy Engine — Unit Level                                         #
# ------------------------------------------------------------------ #

class TestStrategyEngine:
    """Tests for the rule-based strategy engine."""

    def test_basic_recommendation_returns_keys(self):
        result = recommend_strategy(
            driver="VER",
            circuit="Bahrain Grand Prix",
            current_lap=20,
            total_laps=57,
            current_compound="MEDIUM",
            tire_age=20,
        )
        assert "recommended_pit_window" in result
        assert "suggested_compound" in result
        assert "estimated_stint_length" in result
        assert "urgency" in result
        assert "explanation" in result
        assert "disclaimer" in result

    def test_urgency_high_when_tire_life_critical(self):
        result = recommend_strategy(
            driver="HAM",
            circuit="Monaco Grand Prix",
            current_lap=40,
            total_laps=57,
            current_compound="SOFT",
            tire_age=24,   # SOFT max_stint=25 → life_ratio >= 0.90
        )
        assert result["urgency"] == "HIGH"

    def test_wet_weather_triggers_intermediate(self):
        result = recommend_strategy(
            driver="LEC",
            circuit="Spa-Francorchamps",
            current_lap=10,
            total_laps=44,
            current_compound="SOFT",
            tire_age=5,
            rainfall=True,
        )
        assert result["suggested_compound"] in ("INTERMEDIATE", "WET")
        assert result["urgency"] == "HIGH"

    def test_no_stop_alternative_when_tire_life_sufficient(self):
        """When remaining tire life exceeds remaining laps, alternative should mention no-stop."""
        result = recommend_strategy(
            driver="VER",
            circuit="Bahrain Grand Prix",
            current_lap=50,
            total_laps=57,
            current_compound="HARD",
            tire_age=5,   # Only 5 laps old, HARD max=50, remaining=7 laps
        )
        # Either alternative_strategy is set or urgency is LOW
        assert result["urgency"] in ("LOW", "MEDIUM") or result.get("alternative_strategy") is not None

    def test_disclaimer_is_honest(self):
        result = recommend_strategy(
            driver="VER",
            circuit="Monza",
            current_lap=30,
            total_laps=53,
            current_compound="HARD",
            tire_age=10,
        )
        disclaimer = result.get("disclaimer", "").lower()
        # Must not claim official/production use
        assert "official" not in disclaimer
        assert "rule-based" in disclaimer or "historical" in disclaimer


# ------------------------------------------------------------------ #
# Strategy Engine — API Level                                          #
# ------------------------------------------------------------------ #

class TestStrategyAPIEndpoint:
    """Tests for POST /strategy/recommend endpoint."""

    def test_strategy_recommend_returns_200(self):
        payload = {
            "driver": "VER",
            "circuit": "Bahrain Grand Prix",
            "current_lap": 20,
            "total_laps": 57,
            "current_compound": "MEDIUM",
            "tire_age": 18,
            "position": 1,
            "track_temp": 38.0,
            "rainfall": False,
        }
        res = client.post("/strategy/recommend", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recommended_pit_window" in data
        assert "suggested_compound" in data
        assert "urgency" in data

    def test_strategy_recommend_wet_weather(self):
        payload = {
            "driver": "HAM",
            "circuit": "Silverstone Circuit",
            "current_lap": 15,
            "total_laps": 52,
            "current_compound": "MEDIUM",
            "tire_age": 10,
            "rainfall": True,
        }
        res = client.post("/strategy/recommend", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["urgency"] == "HIGH"
        assert data["suggested_compound"] in ("INTERMEDIATE", "WET")

    def test_strategy_compounds_endpoint(self):
        res = client.get("/strategy/compounds")
        assert res.status_code == 200
        data = res.json()
        assert "compounds" in data
        assert "SOFT" in data["compounds"]
        assert "MEDIUM" in data["compounds"]
        assert "HARD" in data["compounds"]
        assert "disclaimer" in data

    def test_strategy_requires_driver_field(self):
        """Missing required field should return 422 Unprocessable Entity."""
        payload = {
            # missing 'driver'
            "circuit": "Monaco",
            "current_lap": 10,
            "total_laps": 78,
            "current_compound": "SOFT",
            "tire_age": 5,
        }
        res = client.post("/strategy/recommend", json=payload)
        assert res.status_code == 422


# ------------------------------------------------------------------ #
# What-If Simulator — Unit Level                                       #
# ------------------------------------------------------------------ #

class TestSimulatorEngine:
    """Tests for the what-if race simulator."""

    def test_compare_strategies_returns_keys(self):
        result = compare_strategies(
            circuit="Bahrain Grand Prix",
            total_laps=57,
            base_lap_time=93.0,
            pit_loss_seconds=22.0,
            strategy_a_name="1-Stop",
            strategy_a_stints=[
                {"compound": "SOFT", "stint_length": 22},
                {"compound": "HARD", "stint_length": 35},
            ],
            strategy_b_name="2-Stop",
            strategy_b_stints=[
                {"compound": "SOFT", "stint_length": 15},
                {"compound": "MEDIUM", "stint_length": 22},
                {"compound": "SOFT", "stint_length": 20},
            ],
        )
        assert "strategy_a" in result
        assert "strategy_b" in result
        assert "time_delta" in result
        assert "faster_strategy" in result
        assert "disclaimer" in result

    def test_total_race_time_is_positive(self):
        result = compare_strategies(
            circuit="Monaco Grand Prix",
            total_laps=78,
            base_lap_time=75.0,
            pit_loss_seconds=22.0,
            strategy_a_name="A",
            strategy_a_stints=[{"compound": "MEDIUM", "stint_length": 78}],
            strategy_b_name="B",
            strategy_b_stints=[{"compound": "SOFT", "stint_length": 78}],
        )
        assert result["strategy_a"]["total_race_time"] > 0
        assert result["strategy_b"]["total_race_time"] > 0

    def test_one_stop_pit_count(self):
        result = compare_strategies(
            circuit="Monza",
            total_laps=53,
            base_lap_time=82.0,
            pit_loss_seconds=21.0,
            strategy_a_name="1-Stop",
            strategy_a_stints=[
                {"compound": "SOFT", "stint_length": 25},
                {"compound": "HARD", "stint_length": 28},
            ],
            strategy_b_name="0-Stop",
            strategy_b_stints=[{"compound": "HARD", "stint_length": 53}],
        )
        assert result["strategy_a"]["pit_stops"] == 1
        assert result["strategy_b"]["pit_stops"] == 0

    def test_faster_strategy_label_is_valid(self):
        result = compare_strategies(
            circuit="Bahrain",
            total_laps=57,
            base_lap_time=93.0,
            pit_loss_seconds=22.0,
            strategy_a_name="Alpha",
            strategy_a_stints=[{"compound": "HARD", "stint_length": 57}],
            strategy_b_name="Beta",
            strategy_b_stints=[{"compound": "HARD", "stint_length": 57}],
        )
        assert result["faster_strategy"] in ("Alpha", "Beta")

    def test_disclaimer_present_and_accurate(self):
        result = compare_strategies(
            circuit="Bahrain",
            total_laps=57,
            base_lap_time=93.0,
            pit_loss_seconds=22.0,
            strategy_a_name="A",
            strategy_a_stints=[{"compound": "MEDIUM", "stint_length": 57}],
            strategy_b_name="B",
            strategy_b_stints=[{"compound": "MEDIUM", "stint_length": 57}],
        )
        disclaimer = result.get("disclaimer", "").lower()
        assert "model-based" in disclaimer or "estimate" in disclaimer


# ------------------------------------------------------------------ #
# What-If Simulator — API Level                                        #
# ------------------------------------------------------------------ #

class TestSimulatorAPIEndpoint:
    """Tests for POST /simulation/compare endpoint."""

    def test_simulation_compare_returns_200(self):
        payload = {
            "circuit": "Bahrain Grand Prix",
            "total_laps": 57,
            "base_lap_time": 93.0,
            "pit_loss_seconds": 22.0,
            "strategy_a": {
                "name": "1-Stop Soft-Hard",
                "stints": [
                    {"compound": "SOFT", "stint_length": 22},
                    {"compound": "HARD", "stint_length": 35},
                ],
            },
            "strategy_b": {
                "name": "2-Stop Soft-Medium-Soft",
                "stints": [
                    {"compound": "SOFT", "stint_length": 15},
                    {"compound": "MEDIUM", "stint_length": 25},
                    {"compound": "SOFT", "stint_length": 17},
                ],
            },
        }
        res = client.post("/simulation/compare", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "strategy_a" in data
        assert "strategy_b" in data
        assert data["strategy_a"]["total_race_time"] > 0
        assert data["strategy_b"]["total_race_time"] > 0
        assert data["faster_strategy"] in ("1-Stop Soft-Hard", "2-Stop Soft-Medium-Soft")

    def test_simulation_missing_stints_returns_422(self):
        """Empty stints list should fail Pydantic validation."""
        payload = {
            "circuit": "Monaco",
            "total_laps": 78,
            "base_lap_time": 75.0,
            "strategy_a": {"name": "A", "stints": []},  # empty
            "strategy_b": {"name": "B", "stints": [{"compound": "HARD", "stint_length": 78}]},
        }
        res = client.post("/simulation/compare", json=payload)
        assert res.status_code == 422

    def test_simulation_formatted_time_is_string(self):
        payload = {
            "circuit": "Silverstone",
            "total_laps": 52,
            "base_lap_time": 90.0,
            "pit_loss_seconds": 22.0,
            "strategy_a": {
                "name": "A",
                "stints": [{"compound": "MEDIUM", "stint_length": 52}],
            },
            "strategy_b": {
                "name": "B",
                "stints": [{"compound": "HARD", "stint_length": 52}],
            },
        }
        res = client.post("/simulation/compare", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data["strategy_a"]["total_race_time_formatted"], str)
        assert ":" in data["strategy_a"]["total_race_time_formatted"]
