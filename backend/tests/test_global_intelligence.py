"""Tests for Global Intelligence: World Bank Connector, Search, Validation, Persistence, Timeouts, and API Endpoints."""
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

import requests
from fastapi.testclient import TestClient

from app.main import app, global_intelligence, store, trust_ledger
from app.global_intelligence import WorldBankConnector, GlobalIntelligenceManager, WorldBankTimeoutError


class TestWorldBankConnector(unittest.TestCase):
    def setUp(self):
        self.connector = WorldBankConnector(timeout_seconds=5.0)

    def test_validation_success(self):
        # Should not raise exception
        self.connector.validate_params("USA", "NY.GDP.MKTP.CD", 2000, 2020)
        self.connector.validate_params("in", "SP.POP.TOTL", 1990, 1995)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            self.connector.validate_params("", "SP.POP.TOTL", 2000, 2020)

        with self.assertRaises(ValueError):
            self.connector.validate_params("TOOLONGCODE", "SP.POP.TOTL", 2000, 2020)

        with self.assertRaises(ValueError):
            self.connector.validate_params("USA", "", 2000, 2020)

        with self.assertRaises(ValueError):
            self.connector.validate_params("USA", "SP.POP.TOTL", 2025, 2010)  # start > end

        with self.assertRaises(ValueError):
            self.connector.validate_params("USA", "SP.POP.TOTL", 1950, 2020)  # < 1960

        with self.assertRaises(ValueError):
            self.connector.validate_params("USA", "SP.POP.TOTL", 2000, 2040)  # > 2030

    def test_country_search_unit(self):
        # Empty query returns catalog
        all_countries = self.connector.search_countries("", limit=10)
        self.assertGreaterEqual(len(all_countries), 10)

        # Exact ISO3 match
        india = self.connector.search_countries("IND")
        self.assertTrue(any(c["code"] == "IND" for c in india))

        # Exact ISO2 match
        usa = self.connector.search_countries("US")
        self.assertTrue(any(c["code"] == "USA" for c in usa))

        # Name match
        germany = self.connector.search_countries("germany")
        self.assertTrue(any(c["name"] == "Germany" for c in germany))

        # Region match
        asia = self.connector.search_countries("South Asia")
        self.assertTrue(any(c["code"] == "IND" for c in asia))

    def test_indicator_search_unit(self):
        # Empty query returns catalog
        all_indicators = self.connector.search_indicators("", limit=15)
        self.assertGreaterEqual(len(all_indicators), 10)

        # Code match
        gdp = self.connector.search_indicators("NY.GDP.MKTP.CD")
        self.assertTrue(any(i["id"] == "NY.GDP.MKTP.CD" for i in gdp))

        # Keyword match
        pop = self.connector.search_indicators("population")
        self.assertTrue(any(i["id"] == "SP.POP.TOTL" for i in pop))

        # Category filter
        healthcare = self.connector.search_indicators("", category="Healthcare")
        self.assertTrue(all("Healthcare" in i["category"] for i in healthcare))

    @patch("app.global_intelligence.requests.get")
    def test_fetch_observations_distinguishes_missing_from_zero(self, mock_get):
        # Mock World Bank response: year 2021 has value 0.0 (non-missing), year 2022 has null (missing), year 2023 has 100.0
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "page": 1,
                "pages": 1,
                "per_page": 1000,
                "total": 3,
                "sourceid": "2",
                "sourcename": "World Development Indicators",
                "lastupdated": "2024-03-28",
            },
            [
                {
                    "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"},
                    "country": {"id": "IN", "value": "India"},
                    "countryiso3code": "IND",
                    "date": "2023",
                    "value": 100.0,
                    "unit": "",
                    "obs_status": "",
                    "decimal": 1,
                },
                {
                    "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"},
                    "country": {"id": "IN", "value": "India"},
                    "countryiso3code": "IND",
                    "date": "2022",
                    "value": None,  # MISSING: NEVER FABRICATE
                    "unit": "",
                    "obs_status": "",
                    "decimal": 1,
                },
                {
                    "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"},
                    "country": {"id": "IN", "value": "India"},
                    "countryiso3code": "IND",
                    "date": "2021",
                    "value": 0.0,  # ACTUAL ZERO (NOT MISSING)
                    "unit": "",
                    "obs_status": "",
                    "decimal": 1,
                },
            ],
        ]
        mock_get.return_value = mock_response

        res = self.connector.fetch_observations("IND", "FP.CPI.TOTL.ZG", 2021, 2023)

        self.assertEqual(res["country"]["code"], "IND")
        self.assertEqual(res["country"]["name"], "India")
        self.assertEqual(res["meta"]["last_updated"], "2024-03-28")
        self.assertEqual(res["meta"]["total_observations"], 3)
        self.assertEqual(res["meta"]["valid_observations"], 2)
        self.assertEqual(res["meta"]["missing_observations"], 1)

        obs = res["observations"]
        # Ensure chronological ordering: 2021, 2022, 2023
        self.assertEqual(obs[0]["year"], 2021)
        self.assertEqual(obs[0]["value"], 0.0)
        self.assertFalse(obs[0]["is_missing"])

        self.assertEqual(obs[1]["year"], 2022)
        self.assertIsNone(obs[1]["value"])
        self.assertTrue(obs[1]["is_missing"])

        self.assertEqual(obs[2]["year"], 2023)
        self.assertEqual(obs[2]["value"], 100.0)
        self.assertFalse(obs[2]["is_missing"])

        # Analytics checks: computed strictly over non-missing values (0.0 and 100.0)
        self.assertEqual(res["analytics"]["min_value"], 0.0)
        self.assertEqual(res["analytics"]["max_value"], 100.0)
        self.assertEqual(res["analytics"]["avg_value"], 50.0)
        self.assertEqual(res["analytics"]["latest_value"], 100.0)
        self.assertEqual(res["analytics"]["latest_year"], 2023)

    @patch("app.global_intelligence.requests.get")
    def test_world_bank_error_response_handling(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"message": [{"id": "120", "key": "Invalid indicator", "value": "The provided parameter value is not valid"}]}
        ]
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            self.connector.fetch_observations("USA", "INVALID.INDICATOR.CODE", 2000, 2020)
        self.assertIn("World Bank API returned error", str(ctx.exception))

    @patch("app.global_intelligence.requests.get")
    def test_connection_error_handling(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectTimeout("Network timed out")

        with self.assertRaises(ConnectionError):
            self.connector.fetch_observations("USA", "SP.POP.TOTL", 2000, 2020)

    @patch("app.global_intelligence.requests.get")
    def test_timeout_error_handling(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out after 5.0s")

        with self.assertRaises(WorldBankTimeoutError):
            self.connector.fetch_observations("USA", "SP.POP.TOTL", 2000, 2020)


class TestGlobalIntelligenceAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_indicators_catalog(self):
        res = self.client.get("/api/global/indicators")
        self.assertEqual(res.status_code, 200)
        indicators = res.json()
        self.assertIsInstance(indicators, list)
        self.assertTrue(len(indicators) >= 10)
        ids = [i["id"] for i in indicators]
        self.assertIn("NY.GDP.MKTP.CD", ids)
        self.assertIn("SP.POP.TOTL", ids)
        self.assertIn("SP.DYN.LE00.IN", ids)

    def test_get_indicators_search_endpoint(self):
        # Query param on main endpoint
        res1 = self.client.get("/api/global/indicators?q=GDP")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertTrue(any("GDP" in i["name"] for i in data1))

        # Dedicated search endpoint
        res2 = self.client.get("/api/global/indicators/search?q=population")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertTrue(any("Population" in i["name"] for i in data2))

        # Category search
        res3 = self.client.get("/api/global/indicators/search?category=Economy")
        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertTrue(all("Economy" in i["category"] for i in data3))

    def test_get_countries_catalog(self):
        res = self.client.get("/api/global/countries")
        self.assertEqual(res.status_code, 200)
        countries = res.json()
        self.assertIsInstance(countries, list)
        codes = [c["code"] for c in countries]
        self.assertIn("IND", codes)
        self.assertIn("USA", codes)
        self.assertIn("DEU", codes)

    def test_get_countries_search_endpoint(self):
        # Query param on main endpoint
        res1 = self.client.get("/api/global/countries?q=india")
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertTrue(any(c["code"] == "IND" for c in data1))

        # Dedicated search endpoint
        res2 = self.client.get("/api/global/countries/search?q=japan")
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertTrue(any(c["code"] == "JPN" for c in data2))

        # Code search
        res3 = self.client.get("/api/global/countries/search?q=DEU")
        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertTrue(any(c["code"] == "DEU" for c in data3))

    @patch("app.global_intelligence.WorldBankConnector.fetch_observations")
    def test_get_observations_endpoint(self, mock_fetch):
        mock_fetch.return_value = {
            "country": {"code": "IND", "name": "India"},
            "indicator": {"code": "SP.POP.TOTL", "name": "Total Population", "unit": "People"},
            "meta": {
                "source": "World Development Indicators",
                "source_id": "2",
                "last_updated": "2024-03-28",
                "total_observations": 2,
                "valid_observations": 2,
                "missing_observations": 0,
                "fetched_at": "2026-10-15T12:00:00Z",
            },
            "analytics": {
                "latest_value": 1400000000.0,
                "latest_year": 2023,
                "oldest_value": 1380000000.0,
                "oldest_year": 2022,
                "min_value": 1380000000.0,
                "max_value": 1400000000.0,
                "avg_value": 1390000000.0,
                "overall_change_pct": 1.45,
            },
            "observations": [
                {
                    "year": 2022,
                    "value": 1380000000.0,
                    "is_missing": False,
                    "country_code": "IND",
                    "country_name": "India",
                    "indicator_code": "SP.POP.TOTL",
                    "indicator_name": "Total Population",
                    "unit": "People",
                    "source": "World Bank Indicators API",
                    "last_updated": "2024-03-28",
                },
                {
                    "year": 2023,
                    "value": 1400000000.0,
                    "is_missing": False,
                    "country_code": "IND",
                    "country_name": "India",
                    "indicator_code": "SP.POP.TOTL",
                    "indicator_name": "Total Population",
                    "unit": "People",
                    "source": "World Bank Indicators API",
                    "last_updated": "2024-03-28",
                },
            ],
        }

        res = self.client.get("/api/global/observations?country=IND&indicator=SP.POP.TOTL&start_year=2022&end_year=2023")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["country"]["code"], "IND")
        self.assertEqual(len(data["observations"]), 2)
        self.assertEqual(data["analytics"]["latest_value"], 1400000000.0)

        # Verify entity stored in graph
        nodes = store.graph_data().get("nodes", [])
        country_node = next((n for n in nodes if n.get("label") == "India"), None)
        self.assertIsNotNone(country_node)
        self.assertEqual(country_node["kind"], "Country")

        # Verify Trust Ledger received provenance audit entry
        ledger_entries = trust_ledger.list_entries(limit=5)
        wb_entry = next((e for e in ledger_entries if "World Bank" in e.get("query", "") or "World Bank" in e.get("conclusion", "")), None)
        self.assertIsNotNone(wb_entry)
        self.assertEqual(wb_entry["verification_status"], "VERIFIED")

    def test_observations_validation_error(self):
        res = self.client.get("/api/global/observations?country=INVALID_CODE_123&indicator=SP.POP.TOTL&start_year=2020&end_year=2024")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid country code", res.json()["detail"])

    @patch("app.global_intelligence.WorldBankConnector.fetch_observations")
    def test_observations_timeout_returns_504(self, mock_fetch):
        mock_fetch.side_effect = WorldBankTimeoutError("World Bank API request timed out after 12.0s.")
        res = self.client.get("/api/global/observations?country=USA&indicator=NY.GDP.MKTP.CD&start_year=2020&end_year=2024&refresh=true")
        self.assertEqual(res.status_code, 504)
        self.assertIn("timed out", res.json()["detail"])

    @patch("app.global_intelligence.WorldBankConnector.fetch_observations")
    def test_observations_connection_error_returns_502(self, mock_fetch):
        mock_fetch.side_effect = ConnectionError("Failed to connect to World Bank API: DNS resolution failed")
        res = self.client.get("/api/global/observations?country=USA&indicator=NY.GDP.MKTP.CD&start_year=2020&end_year=2024&refresh=true")
        self.assertEqual(res.status_code, 502)
        self.assertIn("Failed to connect", res.json()["detail"])

    @patch("app.global_intelligence.GlobalIntelligenceManager.get_series")
    def test_compare_countries_endpoint(self, mock_get_series):
        def fake_get_series(country, indicator, start_year, end_year, force_refresh=False, timeout=None):
            val = 100.0 if country == "USA" else 80.0
            return {
                "country": {"code": country, "name": f"Country {country}"},
                "indicator": {"code": indicator, "name": "GDP", "unit": "USD"},
                "meta": {
                    "source": "WDI",
                    "last_updated": "2024",
                    "valid_observations": 1,
                    "missing_observations": 0,
                    "total_observations": 1,
                },
                "analytics": {
                    "latest_value": val,
                    "latest_year": 2023,
                    "min_value": val,
                    "max_value": val,
                },
                "observations": [
                    {"year": 2023, "value": val, "is_missing": False}
                ],
            }

        mock_get_series.side_effect = fake_get_series

        res = self.client.post("/api/global/compare", json={
            "country_codes": ["USA", "IND"],
            "indicator": "NY.GDP.MKTP.CD",
            "start_year": 2023,
            "end_year": 2023,
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("USA", data["countries"])
        self.assertIn("IND", data["countries"])
        self.assertEqual(len(data["latest_rankings"]), 2)
        # USA (100) should be ranked #1
        self.assertEqual(data["latest_rankings"][0]["country_code"], "USA")
        self.assertEqual(data["latest_rankings"][0]["rank"], 1)

    def test_compare_countries_validation(self):
        # Empty country_codes list
        res = self.client.post("/api/global/compare", json={
            "country_codes": [],
            "indicator": "NY.GDP.MKTP.CD",
            "start_year": 2020,
            "end_year": 2024,
        })
        self.assertEqual(res.status_code, 422)  # Pydantic min_length=1 validation error

    def test_get_stored_series(self):
        res = self.client.get("/api/global/stored")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)


if __name__ == "__main__":
    unittest.main()
