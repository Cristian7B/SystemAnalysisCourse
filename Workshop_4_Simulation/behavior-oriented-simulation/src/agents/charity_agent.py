import mesa
import random

class CharityAgent(mesa.Agent):
    # Represents a verified organization (charity) that collect surplus on behalf of vulnerable populations.
    def __init__(
        self, 
        unique_id, 
        model,
        name,
        location,
        priority_weight=0.25,
        capacity_kg=30.0,
    ):
        super().__init__(unique_id, model)
        self.name = name
        self.location = location
        self.reliability_score = 70.0
        self.is_active = True
        self._is_verified = True
        self.priority_weight = priority_weight
        self.capacity_kg = capacity_kg
        self.current_assignment = None
        self.no_show_probability = random.uniform(0.05, 0.15)
        self.total_pickups = 0
        self.total_no_shows = 0
        self.assignment_history = []
        
    # Read-only flag consumed by the matching engine to identify verified organizations and apply their priority weight.
    # Returns bool: Always True for CarityAgent instances
    @property
    def is_verified(self):
        return self._is_verified
    
    # Updates the reliability scroe based on the outcome of a pickup attempt.
    def update_reliability(self, successful):
        if successful:
            self.reliability_score += 1.0
            self.total_pickups += 1
        else:
            self.reliability_score -= 2.0
            self.total_no_shows += 1
        
        self.reliability_score = max(0.0, min(100.0, self.reliability_score))
    
    # Simulates the provavilistic decision of wheter the charity will show up to collect the assigned surplus
    # Retunrs bool: True if the charity decides to pick up, Flase it no-show
    def decide_pickup(self):
        return random.random() >= self.no_show_probability
    
    # Records and assignment event to the history log.
    def _log_assignment(self, surplus_id, tick, outcome):
        self.assignment_history.append(
            {
                "surplus_id": surplus_id,
                "tick": tick,
                "outcome": outcome,
            }
        )
        
    #  # Executed once per simulation tick by Mesa scheduler.
    def step(self):
        pass