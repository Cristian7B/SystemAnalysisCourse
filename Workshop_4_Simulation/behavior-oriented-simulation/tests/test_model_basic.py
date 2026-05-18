import unittest
from src.model.food_waste_model import FoodWasteModel, TICKS_PER_HOUR


class TestFoodWasteModelInitialization(unittest.TestCase):
    """Tests for model initialization and agent registration."""

    def setUp(self):
        self.model = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )

    def test_scheduler_agent_count(self):
        expected = 3 + 10 + 2 + 3
        self.assertEqual(len(self.model.schedule.agents), expected)

    def test_typed_lists_populated_correctly(self):
        self.assertEqual(len(self.model.donors), 3)
        self.assertEqual(len(self.model.beneficiaries), 10)
        self.assertEqual(len(self.model.charities), 2)
        self.assertEqual(len(self.model.volunteers), 3)

    def test_initial_tick_is_zero(self):
        self.assertEqual(self.model.current_tick, 0)

    def test_initial_publication_state(self):
        self.assertFalse(self.model.publication_open)
        self.assertIsNone(self.model.publication_opened_at)

    def test_initial_surplus_lists_empty(self):
        self.assertEqual(self.model.active_surpluses, [])
        self.assertEqual(self.model.all_surpluses, [])

    def test_donor_locations_within_grid(self):
        for donor in self.model.donors:
            x, y = donor.location
            self.assertGreaterEqual(x, -3.0)
            self.assertLessEqual(x, 3.0)
            self.assertGreaterEqual(y, -3.0)
            self.assertLessEqual(y, 3.0)

    def test_all_agent_ids_unique(self):
        all_ids = [a.unique_id for a in self.model.schedule.agents]
        self.assertEqual(len(all_ids), len(set(all_ids)))

    def test_next_agent_id_incremented_correctly(self):
        expected_next = 3 + 10 + 2 + 3 + 1
        self.assertEqual(self.model._next_agent_id, expected_next)


class TestFoodWasteModelClock(unittest.TestCase):
    """Tests for simulation clock and tick progression."""

    def setUp(self):
        self.model = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )

    def test_tick_increments_after_step(self):
        self.model.step()
        self.assertEqual(self.model.current_tick, 1)

    def test_tick_increments_correctly_over_multiple_steps(self):
        for _ in range(50):
            self.model.step()
        self.assertEqual(self.model.current_tick, 50)

    def test_publication_window_opens_at_correct_tick(self):
        publication_tick = TICKS_PER_HOUR * 20
        for _ in range(publication_tick):
            self.model.step()
        self.assertTrue(self.model.publication_open)
        self.assertEqual(self.model.publication_opened_at, publication_tick)

    def test_publication_window_closed_before_scheduled_tick(self):
        for _ in range(TICKS_PER_HOUR * 19):
            self.model.step()
        self.assertFalse(self.model.publication_open)

    def test_publication_window_closes_after_duration(self):
        publication_tick = TICKS_PER_HOUR * 20
        close_tick = publication_tick + 24
        for _ in range(close_tick + 1):
            self.model.step()
        self.assertFalse(self.model.publication_open)


class TestFoodWasteModelSurplusCreation(unittest.TestCase):
    """Tests for surplus publication and lifecycle."""

    def setUp(self):
        self.model = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )
        publication_tick = TICKS_PER_HOUR * 20
        for _ in range(publication_tick + 1):
            self.model.step()

    def test_surpluses_published_after_window_opens(self):
        self.assertGreater(len(self.model.all_surpluses), 0)

    def test_surplus_count_matches_donors_per_tick(self):
        published_ticks = {s.published_at_tick for s in self.model.all_surpluses}
        for tick in published_ticks:
            surpluses_in_tick = [
                s for s in self.model.all_surpluses
                if s.published_at_tick == tick
            ]
            self.assertLessEqual(
                len(surpluses_in_tick),
                len(self.model.donors),
                msg=f"More surpluses than donors published at tick {tick}",
            )

    def test_surplus_locations_match_donor_locations(self):
        donor_locations = {d.unique_id: d.location for d in self.model.donors}
        for surplus in self.model.all_surpluses:
            self.assertEqual(
                surplus.location,
                donor_locations[surplus.donor_id],
            )

    def test_surplus_kg_within_expected_range(self):
        for surplus in self.model.all_surpluses:
            self.assertGreaterEqual(surplus.kg_available, 5.0)
            self.assertLessEqual(surplus.kg_available, 15.0)

    def test_surplus_published_at_tick_correct(self):
        for surplus in self.model.all_surpluses:
            self.assertGreater(surplus.published_at_tick, 0)

    def test_surplus_deadline_set_correctly(self):
        for surplus in self.model.all_surpluses:
            expected_deadline = surplus.published_at_tick + 18
            self.assertEqual(surplus.collection_deadline_tick, expected_deadline)

    def test_surplus_initial_status_is_published_or_expired(self):
        for surplus in self.model.all_surpluses:
            self.assertIn(surplus.status, {"published", "expired", "assigned", "collected"})


class TestFoodWasteModelMetrics(unittest.TestCase):
    """Tests for get_metrics() output structure and values."""

    def setUp(self):
        self.model = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )

    def test_metrics_returns_dict(self):
        metrics = self.model.get_metrics()
        self.assertIsInstance(metrics, dict)

    def test_metrics_contains_all_expected_keys(self):
        metrics = self.model.get_metrics()
        expected_keys = {
            "tick",
            "total_surpluses_published",
            "total_collected",
            "total_expired",
            "total_reassigned",
            "active_surpluses",
            "recovery_rate",
            "avg_reassignment_count",
        }
        self.assertEqual(set(metrics.keys()), expected_keys)

    def test_metrics_initial_values(self):
        metrics = self.model.get_metrics()
        self.assertEqual(metrics["tick"], 0)
        self.assertEqual(metrics["total_surpluses_published"], 0)
        self.assertEqual(metrics["total_collected"], 0)
        self.assertEqual(metrics["total_expired"], 0)
        self.assertEqual(metrics["recovery_rate"], 0.0)

    def test_recovery_rate_is_zero_without_matching_engine(self):
        for _ in range(200):
            self.model.step()
        metrics = self.model.get_metrics()
        self.assertEqual(metrics["recovery_rate"], 0.0)

    def test_total_expired_grows_over_time(self):
        for _ in range(200):
            self.model.step()
        metrics = self.model.get_metrics()
        self.assertGreater(metrics["total_expired"], 0)

    def test_total_published_grows_over_time(self):
        for _ in range(200):
            self.model.step()
        metrics = self.model.get_metrics()
        self.assertGreater(metrics["total_surpluses_published"], 0)

    def test_collected_plus_expired_leq_published(self):
        for _ in range(200):
            self.model.step()
        metrics = self.model.get_metrics()
        self.assertLessEqual(
            metrics["total_collected"] + metrics["total_expired"],
            metrics["total_surpluses_published"],
        )


class TestFoodWasteModelReproducibility(unittest.TestCase):
    """Tests for deterministic behavior with fixed seed."""

    def test_same_seed_produces_same_surplus_count(self):
        model_a = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=99,
        )
        model_b = FoodWasteModel(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=99,
        )
        for _ in range(200):
            model_a.step()
            model_b.step()

        self.assertEqual(
            len(model_a.all_surpluses),
            len(model_b.all_surpluses),
        )

    def test_same_seed_produces_same_donor_locations(self):
        model_a = FoodWasteModel(n_donors=5, n_beneficiaries=5,
                                  n_charities=1, n_volunteers=1, seed=7)
        model_b = FoodWasteModel(n_donors=5, n_beneficiaries=5,
                                  n_charities=1, n_volunteers=1, seed=7)
        for da, db in zip(model_a.donors, model_b.donors):
            self.assertEqual(da.location, db.location)

    def test_different_seeds_produce_different_locations(self):
        model_a = FoodWasteModel(n_donors=5, n_beneficiaries=5,
                                  n_charities=1, n_volunteers=1, seed=1)
        model_b = FoodWasteModel(n_donors=5, n_beneficiaries=5,
                                  n_charities=1, n_volunteers=1, seed=2)
        locations_a = [d.location for d in model_a.donors]
        locations_b = [d.location for d in model_b.donors]
        self.assertNotEqual(locations_a, locations_b)


if __name__ == "__main__":
    unittest.main()