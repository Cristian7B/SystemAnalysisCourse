import random
import math

import mesa

from src.agents.donor_agent import DonorAgent
from src.agents.beneficiary_agent import BeneficiaryAgent
from src.agents.charity_agent import CharityAgent
from src.agents.volunteer_agent import VolunteerAgent
from src.agents.surplus_agent import SurplusAgent
from src.model.constants import (
    GRID_SIZE_KM,
    TICKS_PER_HOUR,
    PUBLICATION_WINDOW_TICKS,
    COLLECTION_WINDOW_TICKS,
)

class FoodWasteModel(mesa.Model):
    # Main Agent-Based Model for the Food Waste Reduction Platform.
    # Orchestrates the full simulation lifecycle: agent initialization,simulation clock, publication window management, surplus creation, expiration handling, and metric collection.
    def __init__(
        self,
        n_donors=10,
        n_beneficiaries=40,
        n_charities=5,
        n_volunteers=8,
        seed=None,
    ):
        super().__init__()
        
        if seed is not None:
            random.seed(seed)

        self.n_donors = n_donors
        self.n_beneficiaries = n_beneficiaries
        self.n_charities = n_charities
        self.n_volunteers = n_volunteers
        self.schedule = mesa.time.RandomActivation(self)
        self.current_tick = 0
        self.publication_open = False
        self.publication_opened_at = None
        self.active_surpluses = []
        self.all_surpluses = []
        self._next_agent_id = 1
        self.donors = []
        self.beneficiaries = []
        self.charities = []
        self.volunteers = []
        self._initialize_agents()
        from src.model.matching_engine import MatchingEngine
        self.matching_engine = MatchingEngine(self)
        
    # Returns the next available unique agent ID and increments the internal counter
    def _get_next_id(self):
        agent_id = self._next_agent_id
        self._next_agent_id += 1
        return agent_id
    
    # Generates a random Cartesian location within the operational grid of GRID_SIZE_KM × GRID_SIZE_KM km centered at the origin.
    # The origin (0, 0) represents the Faculty of Engineering (UD). The grid is a square approximation of the 3 km radius boundary specified in the simulation document.
    # Retunrs tuple: Random (x,y) coordinates in km.
    def _random_location(self):
        x = random.uniform(-GRID_SIZE_KM, GRID_SIZE_KM)
        y = random.uniform(-GRID_SIZE_KM, GRID_SIZE_KM)
        return (x, y)
    
    # Creates and registres all initial agents with the Mesa scheduler
    def _initialize_agents(self):
        for i in range(self.n_donors):
            agent = DonorAgent(
                unique_id=self._get_next_id(),
                model=self,
                name=f"Donor_{i + 1}",
                location=self._random_location(),
            )
            self.donors.append(agent)
            self.schedule.add(agent)
            
        for i in range(self.n_beneficiaries):
            agent = BeneficiaryAgent(
                unique_id=self._get_next_id(),
                model=self,
                name=f"Beneficiary_{i + 1}",
                location=self._random_location(),
            )
            self.beneficiaries.append(agent)
            self.schedule.add(agent)

        for i in range(self.n_charities):
            agent = CharityAgent(
                unique_id=self._get_next_id(),
                model=self,
                name=f"Charity_{i + 1}",
                location=self._random_location(),
            )
            self.charities.append(agent)
            self.schedule.add(agent)
            
        for i in range(self.n_volunteers):
            agent = VolunteerAgent(
                unique_id=self._get_next_id(),
                model=self,
                name=f"Volunteer_{i + 1}",
                location=self._random_location(),
            )
            self.volunteers.append(agent)
            self.schedule.add(agent)
            
    # Opens the daily surplus publication window for all donor agents
    def _open_publication_window(self):
        for donor in self.donors:
            donor.publication_window_open = True
            
        self.publication_open = True
        self.publication_opened_at = self.current_tick
        
    # Closes the surplus publication window for all donor agents.
    def _close_publication_window(self):
        for donor in self.donors:
            donor.publication_window_open = False

        self.publication_open = False
    
    # Instantiates a SurplusAgent from a donor's publication event.
    # Returns SurplusAgent: The newly created and registered surplus agent
    def _create_surplus_from_donor(self, donor, kg):
        surplus = SurplusAgent(
            unique_id=self._get_next_id(),
            model=self,
            donor_id=donor.unique_id,
            location=donor.location,
            kg_available=kg,
            published_at_tick=self.current_tick,
            collection_deadline_tick=self.current_tick + COLLECTION_WINDOW_TICKS,
        )
        self.schedule.add(surplus)
        self.active_surpluses.append(surplus)
        self.all_surpluses.append(surplus)
        return surplus
    
    # Scans all donors and creates SurplusAgents for any new publications that occurred during the current tick
    def _collect_published_surpluses(self):
        published_donor_ids_this_tick = {
            s.donor_id
            for s in self.active_surpluses
            if s.published_at_tick == self.current_tick
        }

        for donor in self.donors:
            if (
                donor.published_today
                and donor.unique_id not in published_donor_ids_this_tick
            ):
                kg = random.uniform(donor.surplus_kg_min, donor.surplus_kg_max)
                self._create_surplus_from_donor(donor, kg)
    
    # Resets per-day state for all donor agents and clears the active surplus list.
    def _reset_daily_state(self):
        for donor in self.donors:
            donor.reset_daily_state()

        self.active_surpluses = []
        self.publication_open = False
    
    # Removes collected and expired surpluses from the active list
    def _cleanup_active_surpluses(self):
        self.active_surpluses = [
            s for s in self.active_surpluses
            if s.status in {"published", "assigned"}
        ]
    
    # Returns a snapshot of the current simulation state as a dictionary of key performance indicators.
    def get_metrics(self):
        total_published = len(self.all_surpluses)
        total_collected = sum(
            1 for s in self.all_surpluses if s.status == "collected"
        )
        total_expired = sum(
            1 for s in self.all_surpluses if s.status == "expired"
        )
        total_reassignments = sum(
            s.reassignment_count for s in self.all_surpluses
        )
        avg_reassignment = (
            total_reassignments / total_published
            if total_published > 0
            else 0.0
        )
        recovery_rate = (
            total_collected / total_published
            if total_published > 0
            else 0.0
        )
        
        return {
            "tick": self.current_tick,
            "total_surpluses_published": total_published,
            "total_collected": total_collected,
            "total_expired": total_expired,
            "total_reassigned": total_reassignments,
            "active_surpluses": len(self.active_surpluses),
            "recovery_rate": round(recovery_rate, 4),
            "avg_reassignment_count": round(avg_reassignment, 4),
            "total_assignments": len(self.matching_engine.assignment_log),
            "pickup_completion_rate": round(
                total_collected / len(self.matching_engine.assignment_log)
                if len(self.matching_engine.assignment_log) > 0
                else 0.0,
                4,
            ),
        }
        
    # Advances the simulation by one tick.

    #   Execution order per tick:
    #  1. Increment current_tick.
    #   2. Open publication window if scheduled.
    #   3. Execute all agent step() methods via the scheduler.
    #   4. Collect any surpluses published during this tick.
    #   5. Close publication window if its duration has elapsed.
    #   6. Reset daily state if a full day cycle has completed.
    #   7. Clean up the active surplus list.
    def step(self):
        self.current_tick += 1

        day_length_ticks = TICKS_PER_HOUR * 24
        ticks_into_day = self.current_tick % day_length_ticks

        if ticks_into_day == 1:
            self._reset_daily_state()

        if ticks_into_day == TICKS_PER_HOUR * 20:
            self._open_publication_window()

        self._collect_published_surpluses()

        self.matching_engine.run(self.current_tick)

        self.schedule.step()

        if (
            self.publication_open
            and self.publication_opened_at is not None
            and self.current_tick - self.publication_opened_at >= PUBLICATION_WINDOW_TICKS
        ):
            self._close_publication_window()

        self._cleanup_active_surpluses()