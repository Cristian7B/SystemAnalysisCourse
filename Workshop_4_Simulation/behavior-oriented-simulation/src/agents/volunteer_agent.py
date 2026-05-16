import mesa
import random


class VolunteerAgent(mesa.Agent):
    # Represents a volunter who assist in surplus collection when no nearby beneficiary or charity is available to claim a published surplus.
    def __init__(
        self,
        unique_id,
        model,
        name,
        location,
        max_distance_km=3.0,
    ):
        super().__init__(unique_id, model)
        self.name = name
        self.location = location
        self.reliability_score = 60.0
        self.is_active = True
        self.is_available = True
        self.max_distance_km = max_distance_km
        self.current_mission = None
        self.no_show_probability = random.uniform(0.05, 0.15)
        self.total_assists = 0
        self.total_no_shows = 0
        self.mission_history = []
    
    # Updates the reability score based on the outcome of a mission
    def update_reliability(self, successful):
        if successful:
            self.reliability_score += 1.0
        else:
            self.reliability_score -= 2.0
            self.total_no_shows += 1

        self.reliability_score = max(0.0, min(100.0, self.reliability_score))

    # Attempts to accept a surplus collection mission.
    # Returns bool: True if the mission was accepted
    def accept_mission(self, surplus_agent):
        if not self.is_available:
            return False

        self.current_mission = surplus_agent
        self.is_available = False
        return True
    
    # Marks the current mission as successfully completed.
    def complete_mission(self):
        surplus_id = self.current_mission.unique_id
        tick = self.model.schedule.time

        self.total_assists += 1
        self.update_reliability(successful=True)
        self._log_mission(surplus_id, tick, outcome="completed")

        self.current_mission = None
        self.is_available = True
        
    # Record a mission event to the history log
    def _log_mission(self, surplus_id, tick, outcome):
        self.mission_history.append(
            {
                "surplus_id": surplus_id,
                "tick": tick,
                "outcome": outcome,
            }
        )
        
    # Simulates the probabilistic decision of wheter the volunter will actually show up to complete an accepted mission
    # Returns bool: True if the volunteer completes the mission, False if no-show
    def decide_mission(self):
        return random.random() >= self.no_show_probability
    
    # Executed once per simulation tick by the Mesa scheduler.
    def step(self):
        if self.current_mission is None:
            return

        if self.decide_mission():
            self.complete_mission()
        else:
            surplus_id = self.current_mission.unique_id
            tick = self.model.schedule.time

            self.update_reliability(successful=False)
            self._log_mission(surplus_id, tick, outcome="no_show")

            self.current_mission = None
            self.is_available = True