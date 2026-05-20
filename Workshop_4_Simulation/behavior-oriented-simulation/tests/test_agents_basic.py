import unittest
import mesa
from src.agents.donor_agent import DonorAgent
from src.agents.beneficiary_agent import BeneficiaryAgent
from src.agents.charity_agent import CharityAgent
from src.agents.volunteer_agent import VolunteerAgent


class MinimalModel(mesa.Model):
    """
    Minimal Mesa model used exclusively as a test fixture.
    Provides the model infrastructure Mesa 2.x requires at agent
    initialization without running any simulation logic.
    """

    def __init__(self):
        super().__init__()


class TestDonorAgent(unittest.TestCase):

    def setUp(self):
        self.model = MinimalModel()
        self.donor = DonorAgent(
            unique_id=1,
            model=self.model,
            name="Cafeteria Central",
            location=(10.0, 20.0),
        )

    def test_initial_state(self):
        self.assertTrue(self.donor.is_active)
        self.assertFalse(self.donor.published_today)
        self.assertFalse(self.donor.publication_window_open)
        self.assertEqual(self.donor.total_kg_published, 0.0)
        self.assertEqual(self.donor.surplus_kg_min, 5.0)
        self.assertEqual(self.donor.surplus_kg_max, 15.0)

    def test_publish_surplus_returns_value_in_range(self):
        self.donor.publication_window_open = True
        kg = self.donor.publish_surplus()
        self.assertIsNotNone(kg)
        self.assertGreaterEqual(kg, 5.0)
        self.assertLessEqual(kg, 15.0)

    def test_publish_surplus_sets_published_today(self):
        self.donor.publication_window_open = True
        self.donor.publish_surplus()
        self.assertTrue(self.donor.published_today)

    def test_publish_surplus_accumulates_total(self):
        self.donor.publication_window_open = True
        kg = self.donor.publish_surplus()
        self.assertEqual(self.donor.total_kg_published, kg)

    def test_publish_surplus_blocked_if_already_published(self):
        self.donor.publication_window_open = True
        self.donor.publish_surplus()
        second_attempt = self.donor.publish_surplus()
        self.assertIsNone(second_attempt)

    def test_publish_surplus_blocked_if_inactive(self):
        self.donor.is_active = False
        self.donor.publication_window_open = True
        result = self.donor.publish_surplus()
        self.assertIsNone(result)

    def test_reset_daily_state(self):
        self.donor.published_today = True
        self.donor.publication_window_open = True
        self.donor.reset_daily_state()
        self.assertFalse(self.donor.published_today)
        self.assertFalse(self.donor.publication_window_open)


class TestBeneficiaryAgent(unittest.TestCase):

    def setUp(self):
        self.model = MinimalModel()
        self.beneficiary = BeneficiaryAgent(
            unique_id=2,
            model=self.model,
            name="Estudiante A",
            location=(5.0, 8.0),
        )

    def test_initial_state(self):
        self.assertEqual(self.beneficiary.reliability_score, 50.0)
        self.assertTrue(self.beneficiary.is_active)
        self.assertIsNone(self.beneficiary.current_assignment)
        self.assertEqual(self.beneficiary.total_pickups, 0)
        self.assertEqual(self.beneficiary.total_no_shows, 0)
        self.assertEqual(self.beneficiary.assignment_history, [])

    def test_no_show_probability_in_range(self):
        self.assertGreaterEqual(self.beneficiary.no_show_probability, 0.10)
        self.assertLessEqual(self.beneficiary.no_show_probability, 0.25)

    def test_update_reliability_successful(self):
        self.beneficiary.update_reliability(successful=True)
        self.assertEqual(self.beneficiary.reliability_score, 51.0)
        self.assertEqual(self.beneficiary.total_pickups, 1)
        self.assertEqual(self.beneficiary.total_no_shows, 0)

    def test_update_reliability_no_show(self):
        self.beneficiary.update_reliability(successful=False)
        self.assertEqual(self.beneficiary.reliability_score, 48.0)
        self.assertEqual(self.beneficiary.total_no_shows, 1)
        self.assertEqual(self.beneficiary.total_pickups, 0)

    def test_reliability_score_floor(self):
        self.beneficiary.reliability_score = 1.0
        self.beneficiary.update_reliability(successful=False)
        self.assertEqual(self.beneficiary.reliability_score, 0.0)

    def test_reliability_score_ceiling(self):
        self.beneficiary.reliability_score = 99.5
        self.beneficiary.update_reliability(successful=True)
        self.assertEqual(self.beneficiary.reliability_score, 100.0)

    def test_decide_pickup_returns_bool(self):
        result = self.beneficiary.decide_pickup()
        self.assertIsInstance(result, bool)

    def test_decide_pickup_always_true_when_probability_zero(self):
        self.beneficiary.no_show_probability = 0.0
        for _ in range(20):
            self.assertTrue(self.beneficiary.decide_pickup())

    def test_decide_pickup_always_false_when_probability_one(self):
        self.beneficiary.no_show_probability = 1.0
        for _ in range(20):
            self.assertFalse(self.beneficiary.decide_pickup())

    def test_log_assignment_appends_correctly(self):
        self.beneficiary._log_assignment(
            surplus_id=99,
            tick=5,
            outcome="pickup",
        )
        self.assertEqual(len(self.beneficiary.assignment_history), 1)
        entry = self.beneficiary.assignment_history[0]
        self.assertEqual(entry["surplus_id"], 99)
        self.assertEqual(entry["tick"], 5)
        self.assertEqual(entry["outcome"], "pickup")


class TestCharityAgent(unittest.TestCase):

    def setUp(self):
        self.model = MinimalModel()
        self.charity = CharityAgent(
            unique_id=3,
            model=self.model,
            name="Fundacion Esperanza",
            location=(15.0, 12.0),
        )

    def test_initial_state(self):
        self.assertEqual(self.charity.reliability_score, 70.0)
        self.assertTrue(self.charity.is_active)
        self.assertTrue(self.charity.is_verified)
        self.assertEqual(self.charity.priority_weight, 0.25)
        self.assertEqual(self.charity.capacity_kg, 30.0)
        self.assertIsNone(self.charity.current_assignment)
        self.assertEqual(self.charity.total_pickups, 0)
        self.assertEqual(self.charity.total_no_shows, 0)
        self.assertEqual(self.charity.assignment_history, [])

    def test_no_show_probability_in_range(self):
        self.assertGreaterEqual(self.charity.no_show_probability, 0.05)
        self.assertLessEqual(self.charity.no_show_probability, 0.15)

    def test_is_verified_is_read_only(self):
        with self.assertRaises(AttributeError):
            self.charity.is_verified = False

    def test_charity_baseline_higher_than_beneficiary(self):
        beneficiary = BeneficiaryAgent(
            unique_id=99,
            model=self.model,
            name="Test",
            location=(0.0, 0.0),
        )
        self.assertGreater(
            self.charity.reliability_score,
            beneficiary.reliability_score,
        )

    def test_update_reliability_successful(self):
        self.charity.update_reliability(successful=True)
        self.assertEqual(self.charity.reliability_score, 71.0)
        self.assertEqual(self.charity.total_pickups, 1)

    def test_update_reliability_no_show(self):
        self.charity.update_reliability(successful=False)
        self.assertEqual(self.charity.reliability_score, 68.0)
        self.assertEqual(self.charity.total_no_shows, 1)

    def test_custom_priority_weight(self):
        charity_custom = CharityAgent(
            unique_id=4,
            model=self.model,
            name="ONG Test",
            location=(0.0, 0.0),
            priority_weight=0.30,
        )
        self.assertEqual(charity_custom.priority_weight, 0.30)

    def test_custom_capacity_kg(self):
        charity_custom = CharityAgent(
            unique_id=5,
            model=self.model,
            name="ONG Grande",
            location=(0.0, 0.0),
            capacity_kg=50.0,
        )
        self.assertEqual(charity_custom.capacity_kg, 50.0)


class TestVolunteerAgent(unittest.TestCase):

    def setUp(self):
        self.model = MinimalModel()
        self.volunteer = VolunteerAgent(
            unique_id=6,
            model=self.model,
            name="Voluntario A",
            location=(3.0, 7.0),
        )

    def test_initial_state(self):
        self.assertEqual(self.volunteer.reliability_score, 60.0)
        self.assertTrue(self.volunteer.is_active)
        self.assertTrue(self.volunteer.is_available)
        self.assertEqual(self.volunteer.max_distance_km, 3.0)
        self.assertIsNone(self.volunteer.current_mission)
        self.assertEqual(self.volunteer.total_assists, 0)
        self.assertEqual(self.volunteer.total_no_shows, 0)
        self.assertEqual(self.volunteer.mission_history, [])

    def test_no_show_probability_in_range(self):
        self.assertGreaterEqual(self.volunteer.no_show_probability, 0.05)
        self.assertLessEqual(self.volunteer.no_show_probability, 0.15)

    def test_baseline_between_beneficiary_and_charity(self):
        beneficiary = BeneficiaryAgent(99, self.model, "Test", (0.0, 0.0))
        charity = CharityAgent(100, self.model, "Test", (0.0, 0.0))
        self.assertGreater(
            self.volunteer.reliability_score,
            beneficiary.reliability_score,
        )
        self.assertLess(
            self.volunteer.reliability_score,
            charity.reliability_score,
        )

    def test_accept_mission_when_available(self):
        mock_surplus = type("MockSurplus", (), {"unique_id": 10})()
        result = self.volunteer.accept_mission(mock_surplus)
        self.assertTrue(result)
        self.assertFalse(self.volunteer.is_available)
        self.assertEqual(self.volunteer.current_mission.unique_id, 10)

    def test_accept_mission_blocked_when_unavailable(self):
        mock_surplus_1 = type("MockSurplus", (), {"unique_id": 10})()
        mock_surplus_2 = type("MockSurplus", (), {"unique_id": 11})()
        self.volunteer.accept_mission(mock_surplus_1)
        result = self.volunteer.accept_mission(mock_surplus_2)
        self.assertFalse(result)
        self.assertEqual(self.volunteer.current_mission.unique_id, 10)

    def test_update_reliability_successful(self):
        self.volunteer.update_reliability(successful=True)
        self.assertEqual(self.volunteer.reliability_score, 61.0)

    def test_update_reliability_no_show(self):
        self.volunteer.update_reliability(successful=False)
        self.assertEqual(self.volunteer.reliability_score, 58.0)
        self.assertEqual(self.volunteer.total_no_shows, 1)

    def test_decide_mission_returns_bool(self):
        result = self.volunteer.decide_mission()
        self.assertIsInstance(result, bool)

    def test_decide_mission_always_true_when_probability_zero(self):
        self.volunteer.no_show_probability = 0.0
        for _ in range(20):
            self.assertTrue(self.volunteer.decide_mission())

    def test_log_mission_appends_correctly(self):
        self.volunteer._log_mission(
            surplus_id=42,
            tick=3,
            outcome="completed",
        )
        self.assertEqual(len(self.volunteer.mission_history), 1)
        entry = self.volunteer.mission_history[0]
        self.assertEqual(entry["surplus_id"], 42)
        self.assertEqual(entry["tick"], 3)
        self.assertEqual(entry["outcome"], "completed")


if __name__ == "__main__":
    unittest.main()