import unittest
from src.model.food_waste_model import FoodWasteModel
from src.model.matching_engine import (
    MatchingEngine,
    WEIGHT_PROXIMITY,
    WEIGHT_RELIABILITY,
    WEIGHT_CHARITY,
    RADIUS_RING_1,
    RADIUS_RING_2,
    RADIUS_RING_3,
    DELAY_RING_1,
    DELAY_RING_2,
    MAX_REASSIGNMENT_ATTEMPTS,
)
from src.agents.charity_agent import CharityAgent
from src.agents.beneficiary_agent import BeneficiaryAgent
from src.agents.volunteer_agent import VolunteerAgent
from src.agents.surplus_agent import SurplusAgent


class MinimalModel(FoodWasteModel):
    """
    Small deterministic model used as test fixture.
    Uses seed=42 for full reproducibility across all test runs.
    """

    def __init__(self):
        super().__init__(
            n_donors=3,
            n_beneficiaries=10,
            n_charities=2,
            n_volunteers=3,
            seed=42,
        )


class TestMatchingEngineScoring(unittest.TestCase):
    """Tests for the composite scoring algorithm."""

    def setUp(self):
        self.model = MinimalModel()
        self.engine = self.model.matching_engine

        self.surplus = SurplusAgent(
            unique_id=999,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=19,
        )

    def test_score_returns_float(self):
        agent = self.model.beneficiaries[0]
        score = self.engine._compute_score(self.surplus, agent)
        self.assertIsInstance(score, float)

    def test_score_in_valid_range(self):
        for agent in self.model.beneficiaries + self.model.charities:
            score = self.engine._compute_score(self.surplus, agent)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_charity_scores_higher_than_beneficiary_same_conditions(self):
        charity = CharityAgent(
            unique_id=901,
            model=self.model,
            name="TestCharity",
            location=(0.5, 0.0),
        )
        beneficiary = BeneficiaryAgent(
            unique_id=902,
            model=self.model,
            name="TestBeneficiary",
            location=(0.5, 0.0),
        )
        charity.reliability_score = 70.0
        beneficiary.reliability_score = 70.0

        charity_score = self.engine._compute_score(self.surplus, charity)
        beneficiary_score = self.engine._compute_score(self.surplus, beneficiary)

        self.assertGreater(charity_score, beneficiary_score)

    def test_closer_agent_scores_higher(self):
        close_agent = BeneficiaryAgent(
            unique_id=903,
            model=self.model,
            name="Close",
            location=(0.1, 0.0),
        )
        far_agent = BeneficiaryAgent(
            unique_id=904,
            model=self.model,
            name="Far",
            location=(2.5, 0.0),
        )
        close_agent.reliability_score = 50.0
        far_agent.reliability_score = 50.0

        self.assertGreater(
            self.engine._compute_score(self.surplus, close_agent),
            self.engine._compute_score(self.surplus, far_agent),
        )

    def test_higher_reliability_scores_higher(self):
        agent_high = BeneficiaryAgent(
            unique_id=905,
            model=self.model,
            name="HighRel",
            location=(1.0, 0.0),
        )
        agent_low = BeneficiaryAgent(
            unique_id=906,
            model=self.model,
            name="LowRel",
            location=(1.0, 0.0),
        )
        agent_high.reliability_score = 90.0
        agent_low.reliability_score = 10.0

        self.assertGreater(
            self.engine._compute_score(self.surplus, agent_high),
            self.engine._compute_score(self.surplus, agent_low),
        )

    def test_agent_beyond_grid_scores_zero(self):
        far_agent = BeneficiaryAgent(
            unique_id=907,
            model=self.model,
            name="TooFar",
            location=(5.0, 5.0),
        )
        score = self.engine._compute_score(self.surplus, far_agent)
        self.assertEqual(score, 0.0)

    def test_weights_sum_to_one(self):
        self.assertAlmostEqual(
            WEIGHT_PROXIMITY + WEIGHT_RELIABILITY + WEIGHT_CHARITY,
            1.0,
            places=10,
        )


class TestMatchingEngineEligibility(unittest.TestCase):
    """Tests for recipient eligibility filtering."""

    def setUp(self):
        self.model = MinimalModel()
        self.engine = self.model.matching_engine
        self.surplus = SurplusAgent(
            unique_id=999,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=19,
        )

    def test_inactive_agent_not_eligible(self):
        agent = self.model.beneficiaries[0]
        agent.is_active = False
        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_3)
        self.assertNotIn(agent, eligible)

    def test_agent_with_active_assignment_not_eligible(self):
        agent = self.model.beneficiaries[0]
        agent.current_assignment = self.surplus
        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_3)
        self.assertNotIn(agent, eligible)

    def test_unavailable_volunteer_not_eligible(self):
        volunteer = self.model.volunteers[0]
        volunteer.is_available = False
        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_3)
        self.assertNotIn(volunteer, eligible)

    def test_agent_outside_radius_not_eligible(self):
        agent = BeneficiaryAgent(
            unique_id=910,
            model=self.model,
            name="OutsideRadius",
            location=(2.0, 0.0),
        )
        self.model.beneficiaries.append(agent)
        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_1)
        self.assertNotIn(agent, eligible)

    def test_empty_list_when_no_candidates(self):
        for agent in self.model.beneficiaries:
            agent.is_active = False
        for agent in self.model.charities:
            agent.is_active = False
        for agent in self.model.volunteers:
            agent.is_active = False

        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_3)
        self.assertEqual(eligible, [])

    def test_active_available_agent_within_radius_is_eligible(self):
        agent = BeneficiaryAgent(
            unique_id=911,
            model=self.model,
            name="NearAgent",
            location=(0.1, 0.0),
        )
        agent.is_active = True
        agent.current_assignment = None
        self.model.beneficiaries.append(agent)

        eligible = self.engine._get_eligible_recipients(self.surplus, RADIUS_RING_3)
        self.assertIn(agent, eligible)


class TestMatchingEngineRadius(unittest.TestCase):
    """Tests for staged notification radius logic."""

    def setUp(self):
        self.model = MinimalModel()
        self.engine = self.model.matching_engine
        self.surplus = SurplusAgent(
            unique_id=999,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=100,
            collection_deadline_tick=118,
        )

    def test_ring_1_radius_within_delay_1(self):
        radius = self.engine._determine_active_radius(self.surplus, 101)
        self.assertEqual(radius, RADIUS_RING_1)

    def test_ring_2_radius_between_delays(self):
        radius = self.engine._determine_active_radius(self.surplus, 103)
        self.assertEqual(radius, RADIUS_RING_2)

    def test_ring_3_radius_after_delay_2(self):
        radius = self.engine._determine_active_radius(self.surplus, 105)
        self.assertEqual(radius, RADIUS_RING_3)

    def test_ring_number_mapping(self):
        self.assertEqual(self.engine._get_ring_number(RADIUS_RING_1), 1)
        self.assertEqual(self.engine._get_ring_number(RADIUS_RING_2), 2)
        self.assertEqual(self.engine._get_ring_number(RADIUS_RING_3), 3)


class TestMatchingEngineAssignment(unittest.TestCase):
    """Tests for end-to-end assignment outcomes."""

    def setUp(self):
        self.model = MinimalModel()
        self.engine = self.model.matching_engine
        for _ in range(200):
            self.model.step()

    def test_total_assignments_greater_than_zero(self):
        self.assertGreater(len(self.engine.assignment_log), 0)

    def test_recovery_rate_above_threshold(self):
        metrics = self.model.get_metrics()
        self.assertGreaterEqual(metrics["recovery_rate"], 0.80)

    def test_pickup_completion_rate_above_threshold(self):
        metrics = self.model.get_metrics()
        self.assertGreaterEqual(metrics["pickup_completion_rate"], 0.85)

    def test_assignment_log_entry_has_correct_keys(self):
        expected_keys = {
            "surplus_id",
            "recipient_id",
            "recipient_type",
            "tick",
            "score",
            "ring",
        }
        for entry in self.engine.assignment_log:
            self.assertEqual(set(entry.keys()), expected_keys)

    def test_assignment_scores_in_valid_range(self):
        for entry in self.engine.assignment_log:
            self.assertGreaterEqual(entry["score"], 0.0)
            self.assertLessEqual(entry["score"], 1.0)

    def test_assignment_rings_are_valid(self):
        for entry in self.engine.assignment_log:
            self.assertIn(entry["ring"], {1, 2, 3})

    def test_charities_receive_proportionally_more_assignments(self):
        total = len(self.engine.assignment_log)
        charity_count = sum(
            1 for e in self.engine.assignment_log
            if e["recipient_type"] == "CharityAgent"
        )
        charity_ratio = charity_count / total if total > 0 else 0
        n_charities = len(self.model.charities)
        n_total_recipients = (
            len(self.model.beneficiaries)
            + len(self.model.charities)
            + len(self.model.volunteers)
        )
        pure_ratio = n_charities / n_total_recipients
        self.assertGreater(charity_ratio, pure_ratio * 0.5)

    def test_collected_surpluses_have_collected_at_tick(self):
        collected = [
            s for s in self.model.all_surpluses
            if s.status == "collected"
        ]
        for surplus in collected:
            self.assertIsNotNone(surplus.collected_at_tick)
            self.assertGreater(surplus.collected_at_tick, 0)


class TestMatchingEngineReassignment(unittest.TestCase):
    """Tests for expiration and reassignment logic."""

    def setUp(self):
        self.model = MinimalModel()
        self.engine = self.model.matching_engine

    def test_expired_surplus_reassignment_count_increments(self):
        surplus = SurplusAgent(
            unique_id=998,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=1,
        )
        self.model.active_surpluses.append(surplus)
        self.model.all_surpluses.append(surplus)

        self.engine._handle_expired_surpluses(tick=5)
        self.assertEqual(surplus.reassignment_count, 1)
        self.assertEqual(surplus.status, "published")

    def test_surplus_permanently_expired_after_max_attempts(self):
        surplus = SurplusAgent(
            unique_id=997,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=1,
        )
        surplus.reassignment_count = MAX_REASSIGNMENT_ATTEMPTS
        self.model.active_surpluses.append(surplus)
        self.model.all_surpluses.append(surplus)

        self.engine._handle_expired_surpluses(tick=5)
        self.assertEqual(surplus.status, "expired")

    def test_release_recipient_clears_beneficiary_assignment(self):
        surplus = SurplusAgent(
            unique_id=996,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=19,
        )
        recipient = self.model.beneficiaries[0]
        surplus.assign(recipient.unique_id, tick=1)
        recipient.current_assignment = surplus

        self.engine._release_recipient(surplus)
        self.assertIsNone(recipient.current_assignment)

    def test_release_recipient_clears_volunteer_mission(self):
        surplus = SurplusAgent(
            unique_id=995,
            model=self.model,
            donor_id=1,
            location=(0.0, 0.0),
            kg_available=10.0,
            published_at_tick=1,
            collection_deadline_tick=19,
        )
        volunteer = self.model.volunteers[0]
        surplus.assign(volunteer.unique_id, tick=1)
        volunteer.accept_mission(surplus)

        self.engine._release_recipient(surplus)
        self.assertIsNone(volunteer.current_mission)
        self.assertTrue(volunteer.is_available)


if __name__ == "__main__":
    unittest.main()