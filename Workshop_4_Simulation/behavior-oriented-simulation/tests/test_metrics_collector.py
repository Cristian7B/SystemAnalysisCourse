import unittest
import pandas as pd
from src.model.food_waste_model import FoodWasteModel
from src.metrics.metrics_collector import MetricsCollector


class MinimalModel(FoodWasteModel):
    """Small deterministic model used as test fixture."""

    def __init__(self):
        super().__init__(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )


class TestMetricsCollectorInitialization(unittest.TestCase):
    """Tests for collector initialization and identity."""

    def setUp(self):
        self.model = MinimalModel()
        self.collector = MetricsCollector(self.model, scenario_name="test_scenario")

    def test_scenario_name_stored_correctly(self):
        self.assertEqual(self.collector.scenario_name, "test_scenario")

    def test_run_id_is_string(self):
        self.assertIsInstance(self.collector.run_id, str)

    def test_run_id_not_empty(self):
        self.assertGreater(len(self.collector.run_id), 0)

    def test_run_id_consistent_within_run(self):
        run_id_before = self.collector.run_id
        for _ in range(10):
            self.model.step()
            self.collector.record_tick()
        self.assertEqual(self.collector.run_id, run_id_before)

    def test_two_collectors_have_different_run_ids(self):
        import time
        time.sleep(0.01)
        collector2 = MetricsCollector(self.model, scenario_name="test_scenario")
        self.assertNotEqual(self.collector.run_id, collector2.run_id)

    def test_tick_records_initially_empty(self):
        self.assertEqual(self.collector.tick_records, [])

    def test_agent_records_initially_empty(self):
        self.assertEqual(self.collector.agent_records, [])


class TestMetricsCollectorTickRecording(unittest.TestCase):
    """Tests for tick-level metric recording."""

    def setUp(self):
        self.model = MinimalModel()
        self.collector = MetricsCollector(self.model, scenario_name="test_scenario")
        for _ in range(50):
            self.model.step()
            self.collector.record_tick()

    def test_tick_count_matches_steps(self):
        self.assertEqual(len(self.collector.tick_records), 50)

    def test_each_record_has_scenario_field(self):
        for record in self.collector.tick_records:
            self.assertEqual(record["scenario"], "test_scenario")

    def test_each_record_has_run_id(self):
        for record in self.collector.tick_records:
            self.assertEqual(record["run_id"], self.collector.run_id)

    def test_each_record_has_tick_field(self):
        for record in self.collector.tick_records:
            self.assertIn("tick", record)
            self.assertGreater(record["tick"], 0)

    def test_ticks_are_sequential(self):
        ticks = [r["tick"] for r in self.collector.tick_records]
        for i in range(1, len(ticks)):
            self.assertEqual(ticks[i], ticks[i - 1] + 1)

    def test_each_record_has_population_fields(self):
        for record in self.collector.tick_records:
            self.assertEqual(record["n_donors"], 3)
            self.assertEqual(record["n_beneficiaries"], 10)
            self.assertEqual(record["n_charities"], 2)
            self.assertEqual(record["n_volunteers"], 3)

    def test_each_record_has_metric_fields(self):
        expected_fields = {
            "total_surpluses_published",
            "total_collected",
            "total_expired",
            "total_reassigned",
            "active_surpluses",
            "recovery_rate",
            "avg_reassignment_count",
            "total_assignments",
            "pickup_completion_rate",
        }
        for record in self.collector.tick_records:
            for field in expected_fields:
                self.assertIn(field, record)

    def test_recovery_rate_in_valid_range(self):
        for record in self.collector.tick_records:
            self.assertGreaterEqual(record["recovery_rate"], 0.0)
            self.assertLessEqual(record["recovery_rate"], 1.0)


class TestMetricsCollectorDataFrame(unittest.TestCase):
    """Tests for to_dataframe() output structure."""

    def setUp(self):
        self.model = MinimalModel()
        self.collector = MetricsCollector(self.model, scenario_name="test_scenario")

    def test_empty_dataframe_before_recording(self):
        df = self.collector.to_dataframe()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 0)

    def test_empty_dataframe_has_expected_columns(self):
        df = self.collector.to_dataframe()
        expected_cols = {
            "scenario", "run_id", "tick",
            "n_donors", "n_beneficiaries", "n_charities", "n_volunteers",
            "total_surpluses_published", "total_collected", "total_expired",
            "total_reassigned", "active_surpluses", "recovery_rate",
            "avg_reassignment_count", "total_assignments",
            "pickup_completion_rate",
        }
        self.assertEqual(set(df.columns), expected_cols)

    def test_dataframe_row_count_matches_ticks(self):
        n_ticks = 100
        for _ in range(n_ticks):
            self.model.step()
            self.collector.record_tick()
        df = self.collector.to_dataframe()
        self.assertEqual(len(df), n_ticks)

    def test_dataframe_scenario_column_consistent(self):
        for _ in range(30):
            self.model.step()
            self.collector.record_tick()
        df = self.collector.to_dataframe()
        self.assertTrue((df["scenario"] == "test_scenario").all())

    def test_dataframe_run_id_column_consistent(self):
        for _ in range(30):
            self.model.step()
            self.collector.record_tick()
        df = self.collector.to_dataframe()
        self.assertEqual(df["run_id"].nunique(), 1)

    def test_dataframe_tick_column_is_monotonic(self):
        for _ in range(50):
            self.model.step()
            self.collector.record_tick()
        df = self.collector.to_dataframe()
        self.assertTrue(df["tick"].is_monotonic_increasing)


class TestMetricsCollectorAgentRecording(unittest.TestCase):
    """Tests for agent-level metric recording."""

    def setUp(self):
        self.model = MinimalModel()
        self.collector = MetricsCollector(self.model, scenario_name="test_scenario")
        for _ in range(200):
            self.model.step()
            self.collector.record_tick()
        self.collector.record_agents()

    def test_agent_count_matches_recipients(self):
        expected = (
            len(self.model.beneficiaries)
            + len(self.model.charities)
            + len(self.model.volunteers)
        )
        self.assertEqual(len(self.collector.agent_records), expected)

    def test_agents_dataframe_has_correct_shape(self):
        df = self.collector.agents_to_dataframe()
        expected_rows = (
            len(self.model.beneficiaries)
            + len(self.model.charities)
            + len(self.model.volunteers)
        )
        self.assertEqual(len(df), expected_rows)

    def test_agent_records_have_scenario_field(self):
        for record in self.collector.agent_records:
            self.assertEqual(record["scenario"], "test_scenario")

    def test_agent_records_have_run_id(self):
        for record in self.collector.agent_records:
            self.assertEqual(record["run_id"], self.collector.run_id)

    def test_charity_agents_flagged_correctly(self):
        charity_records = [
            r for r in self.collector.agent_records
            if r["agent_type"] == "CharityAgent"
        ]
        for record in charity_records:
            self.assertTrue(record["is_charity"])

    def test_beneficiary_agents_not_flagged_as_charity(self):
        beneficiary_records = [
            r for r in self.collector.agent_records
            if r["agent_type"] == "BeneficiaryAgent"
        ]
        for record in beneficiary_records:
            self.assertFalse(record["is_charity"])

    def test_no_show_rate_in_valid_range(self):
        for record in self.collector.agent_records:
            self.assertGreaterEqual(record["no_show_rate"], 0.0)
            self.assertLessEqual(record["no_show_rate"], 1.0)

    def test_reliability_scores_in_valid_range(self):
        for record in self.collector.agent_records:
            self.assertGreaterEqual(record["final_reliability_score"], 0.0)
            self.assertLessEqual(record["final_reliability_score"], 100.0)

    def test_agent_ids_are_unique(self):
        ids = [r["agent_id"] for r in self.collector.agent_records]
        self.assertEqual(len(ids), len(set(ids)))


class TestMetricsCollectorSummary(unittest.TestCase):
    """Tests for get_summary() output structure and values."""

    def setUp(self):
        self.model = MinimalModel()
        self.collector = MetricsCollector(self.model, scenario_name="test_scenario")
        for _ in range(200):
            self.model.step()
            self.collector.record_tick()
        self.collector.record_agents()
        self.summary = self.collector.get_summary()

    def test_summary_returns_dict(self):
        self.assertIsInstance(self.summary, dict)

    def test_summary_has_all_expected_keys(self):
        expected_keys = {
            "scenario",
            "run_id",
            "final_recovery_rate",
            "final_pickup_completion_rate",
            "total_surpluses_published",
            "total_collected",
            "total_expired",
            "total_assignments",
            "total_reassignments",
            "avg_no_show_rate",
            "charity_assignment_share",
        }
        self.assertEqual(set(self.summary.keys()), expected_keys)

    def test_summary_scenario_matches(self):
        self.assertEqual(self.summary["scenario"], "test_scenario")

    def test_summary_run_id_matches_collector(self):
        self.assertEqual(self.summary["run_id"], self.collector.run_id)

    def test_summary_recovery_rate_in_valid_range(self):
        self.assertGreaterEqual(self.summary["final_recovery_rate"], 0.0)
        self.assertLessEqual(self.summary["final_recovery_rate"], 1.0)

    def test_summary_completion_rate_in_valid_range(self):
        self.assertGreaterEqual(self.summary["final_pickup_completion_rate"], 0.0)
        self.assertLessEqual(self.summary["final_pickup_completion_rate"], 1.0)

    def test_summary_charity_share_in_valid_range(self):
        self.assertGreaterEqual(self.summary["charity_assignment_share"], 0.0)
        self.assertLessEqual(self.summary["charity_assignment_share"], 1.0)

    def test_summary_no_show_rate_in_valid_range(self):
        self.assertGreaterEqual(self.summary["avg_no_show_rate"], 0.0)
        self.assertLessEqual(self.summary["avg_no_show_rate"], 1.0)

    def test_collected_plus_expired_leq_published(self):
        self.assertLessEqual(
            self.summary["total_collected"] + self.summary["total_expired"],
            self.summary["total_surpluses_published"],
        )


if __name__ == "__main__":
    unittest.main()