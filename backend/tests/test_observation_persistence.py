"""Tests for Historical Observation Persistence, Deduplication, Provenance Tracking, and Data Integrity."""
import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.graph_store import GraphStore
from app.schema import EntityKind, RelationType, validate_relation
from app.global_intelligence import GlobalIntelligenceManager
from app.trust_ledger import TrustLedgerManager


class TestObservationPersistenceAndIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = GraphStore()
        self.trust_ledger = TrustLedgerManager(self.store)
        self.manager = GlobalIntelligenceManager(
            graph_store=self.store,
            trust_ledger=self.trust_ledger,
            cache_dir=self.temp_dir,
        )
        self.client = TestClient(app)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_schema_allows_observation_relationships(self):
        """Verify schema defines Observation and allows Country->Observation and Observation->Indicator edges."""
        self.assertEqual(EntityKind.OBSERVATION.value, "Observation")
        self.assertEqual(RelationType.RECORDED_OBSERVATION.value, "RECORDED_OBSERVATION")
        self.assertEqual(RelationType.MEASURES_INDICATOR.value, "MEASURES_INDICATOR")

        self.assertTrue(validate_relation("Country", "RECORDED_OBSERVATION", "Observation"))
        self.assertTrue(validate_relation("Observation", "MEASURES_INDICATOR", "Indicator"))
        self.assertTrue(validate_relation("Observation", "BELONGS_TO_COUNTRY", "Country"))

    def test_store_single_observation_deterministic_id(self):
        """Verify observation gets deterministic composite ID."""
        obs = {
            "country_code": "IND",
            "country_name": "India",
            "indicator_code": "NY.GDP.PCAP.CD",
            "indicator_name": "GDP per capita",
            "year": 2020,
            "value": 1933.1,
            "is_missing": False,
            "unit": "current US$",
            "source": "World Bank Indicators API",
            "source_id": "2",
            "last_updated": "2024-03-28",
            "retrieved_at": "2026-10-15T10:00:00Z",
        }
        res = self.store.store_observation(obs)
        self.assertTrue(res["is_new"])
        self.assertEqual(res["id"], "obs_IND_NY_GDP_PCAP_CD_2020")
        stored = res["observation"]
        self.assertEqual(stored["value"], 1933.1)
        self.assertFalse(stored["is_missing"])
        self.assertEqual(stored["version"], 1)

    def test_deduplication_prevents_duplicate_records(self):
        """Storing the exact same observation twice updates the record without creating duplicates."""
        obs1 = {
            "country_code": "USA",
            "indicator_code": "SP.POP.TOTL",
            "year": 2022,
            "value": 333287557.0,
            "is_missing": False,
            "unit": "People",
            "source": "World Bank Indicators API",
            "source_id": "2",
            "last_updated": "2024-01-01",
            "retrieved_at": "2026-10-15T09:00:00Z",
        }
        res1 = self.store.store_observation(obs1)
        self.assertTrue(res1["is_new"])
        self.assertEqual(self.store.count_observations("USA", "SP.POP.TOTL"), 1)

        # Store second time with updated retrieval timestamp
        obs2 = {
            "country_code": "USA",
            "indicator_code": "SP.POP.TOTL",
            "year": 2022,
            "value": 333287557.0,
            "is_missing": False,
            "unit": "People",
            "source": "World Bank Indicators API",
            "source_id": "2",
            "last_updated": "2024-03-28",
            "retrieved_at": "2026-10-15T12:00:00Z",
        }
        res2 = self.store.store_observation(obs2)
        self.assertFalse(res2["is_new"])
        # Node count remains strictly 1
        self.assertEqual(self.store.count_observations("USA", "SP.POP.TOTL"), 1)

        stored = res2["observation"]
        self.assertEqual(stored["version"], 2)
        self.assertEqual(stored["retrieved_at"], "2026-10-15T12:00:00Z")
        self.assertEqual(stored["last_updated"], "2024-03-28")

    def test_historical_values_preservation_across_years(self):
        """Verify historical series spanning multiple years is preserved and sorted chronologically."""
        years_data = [
            (2018, 100.5),
            (2019, 105.2),
            (2020, 98.4),
            (2021, 112.1),
            (2022, 115.8),
        ]
        # Ingest out of chronological order
        for yr, val in reversed(years_data):
            self.store.store_observation({
                "country_code": "DEU",
                "indicator_code": "FP.CPI.TOTL.ZG",
                "year": yr,
                "value": val,
                "is_missing": False,
                "unit": "%",
            })

        # Query full range
        obs_list = self.store.get_observations("DEU", "FP.CPI.TOTL.ZG")
        self.assertEqual(len(obs_list), 5)
        # Verify strict ascending order
        for i, (expected_yr, expected_val) in enumerate(years_data):
            self.assertEqual(obs_list[i]["year"], expected_yr)
            self.assertEqual(obs_list[i]["value"], expected_val)

        # Query sub-window (2019 to 2021)
        sub_window = self.store.get_observations("DEU", "FP.CPI.TOTL.ZG", start_year=2019, end_year=2021)
        self.assertEqual(len(sub_window), 3)
        self.assertEqual([o["year"] for o in sub_window], [2019, 2020, 2021])

    def test_missing_data_integrity_zero_fabrication(self):
        """Ensure missing data remains strictly None, while numeric 0.0 is preserved accurately."""
        # Record with genuine 0.0 value
        obs_zero = {
            "country_code": "NOR",
            "indicator_code": "TEST.IND",
            "year": 2020,
            "value": 0.0,
            "is_missing": False,
        }
        res_zero = self.store.store_observation(obs_zero)
        self.assertEqual(res_zero["observation"]["value"], 0.0)
        self.assertFalse(res_zero["observation"]["is_missing"])

        # Record with missing data (None)
        obs_missing = {
            "country_code": "NOR",
            "indicator_code": "TEST.IND",
            "year": 2021,
            "value": None,
            "is_missing": True,
        }
        res_missing = self.store.store_observation(obs_missing)
        self.assertIsNone(res_missing["observation"]["value"])
        self.assertTrue(res_missing["observation"]["is_missing"])

        # Retrieve and verify distinction is completely maintained
        retrieved = self.store.get_observations("NOR", "TEST.IND")
        self.assertEqual(len(retrieved), 2)
        self.assertEqual(retrieved[0]["value"], 0.0)
        self.assertFalse(retrieved[0]["is_missing"])
        self.assertIsNone(retrieved[1]["value"])
        self.assertTrue(retrieved[1]["is_missing"])

    def test_provenance_and_relationship_linking(self):
        """Verify country and indicator nodes link to observations with provenance metadata."""
        c_node = self.store.add_entity(name="India", kind="Country", detail="ISO: IND")
        i_node = self.store.add_entity(name="GDP per capita", kind="Indicator", detail="Code: NY.GDP.PCAP.CD")
        c_id = c_node["node"]["id"]
        i_id = i_node["node"]["id"]

        obs = {
            "country_code": "IND",
            "country_name": "India",
            "indicator_code": "NY.GDP.PCAP.CD",
            "indicator_name": "GDP per capita",
            "year": 2023,
            "value": 2410.5,
            "source": "World Bank Indicators API",
            "source_id": "2",
            "last_updated": "2024-03-28",
            "retrieved_at": "2026-10-15T12:00:00Z",
        }
        res = self.store.store_observation(obs, country_id=c_id, indicator_id=i_id)
        obs_id = res["id"]

        edges = self.store.graph_data()["edges"]
        has_recorded_edge = any(
            e["source"] == c_id and e["target"] == obs_id and e["label"] == "RECORDED_OBSERVATION"
            for e in edges
        )
        has_measures_edge = any(
            e["source"] == obs_id and e["target"] == i_id and e["label"] == "MEASURES_INDICATOR"
            for e in edges
        )
        self.assertTrue(has_recorded_edge, "Expected RECORDED_OBSERVATION edge from Country to Observation")
        self.assertTrue(has_measures_edge, "Expected MEASURES_INDICATOR edge from Observation to Indicator")

    def test_disk_persistence_survives_reinitialization(self):
        """Verify observations persisted by manager are saved to disk and reloaded by a new instance."""
        series_payload = {
            "country": {"code": "JPN", "name": "Japan"},
            "indicator": {"code": "SP.POP.TOTL", "name": "Total Population", "category": "Demographics", "unit": "People"},
            "meta": {
                "source": "World Bank Indicators API",
                "source_id": "2",
                "last_updated": "2024-03-28",
                "valid_observations": 2,
                "missing_observations": 1,
                "total_observations": 3,
                "fetched_at": "2026-10-15T14:30:00Z",
            },
            "analytics": {
                "latest_value": 125000000.0,
                "latest_year": 2022,
                "oldest_value": 126000000.0,
                "oldest_year": 2020,
            },
            "observations": [
                {"year": 2020, "value": 126000000.0, "is_missing": False},
                {"year": 2021, "value": 125500000.0, "is_missing": False},
                {"year": 2022, "value": 125000000.0, "is_missing": False},
            ],
        }

        # Persist through manager
        self.manager._persist_to_graph_and_ledger(series_payload)

        # Check observation file exists on disk
        obs_file = os.path.join(self.temp_dir, "global_intelligence_observations.json")
        self.assertTrue(os.path.exists(obs_file))

        # Create fresh manager instance with new store pointing to same directory
        fresh_store = GraphStore()
        fresh_manager = GlobalIntelligenceManager(
            graph_store=fresh_store,
            trust_ledger=TrustLedgerManager(fresh_store),
            cache_dir=self.temp_dir,
        )

        loaded_obs = fresh_manager.get_stored_observations("JPN", "SP.POP.TOTL")
        self.assertEqual(len(loaded_obs), 3)
        self.assertEqual([o["year"] for o in loaded_obs], [2020, 2021, 2022])
        self.assertEqual(loaded_obs[0]["country_code"], "JPN")
        self.assertEqual(loaded_obs[0]["source"], "World Bank Indicators API")

    def test_api_stored_observations_endpoint(self):
        """Test GET /api/global/observations/stored endpoint."""
        res = self.client.get("/api/global/observations/stored?country=IND")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    def test_api_storage_stats_endpoint(self):
        """Test GET /api/global/storage/stats endpoint."""
        res = self.client.get("/api/global/storage/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_observations", data)
        self.assertIn("valid_observations", data)
        self.assertIn("missing_observations", data)
        self.assertIn("country_count", data)
        self.assertIn("indicator_count", data)
        self.assertEqual(data["integrity_status"], "VERIFIED_ZERO_FABRICATION")


if __name__ == "__main__":
    unittest.main()
