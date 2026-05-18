import mesa
import random

class BeneficiaryAgent(mesa.Agent):
    # Represents an individual beneficiary
    def __init__(
        self, 
        unique_id, 
        model,
        name,
        location,
    ):
        super().__init__(unique_id, model)
        self.name = name
        self.location = location
        self.reliability_score = 50.0
        self.is_active = True
        self.current_assignment = None
        self.no_show_probability = random.uniform(0.10, 0.25)
        self.total_pickups = 0
        self.total_no_shows = 0
        self.assignment_history = []
        
    # Updates the reliability score based on the outcome of a pickup attempt
    def update_reliability(self, successful):
        if successful:
            self.reliability_score += 1.0
            self.total_pickups += 1
        else: 
            self.reliability_score -= 2.0
            self.total_no_shows += 1
        
        self.reliability_score = max(0.0, min(100.0, self.reliability_score))
        
    # Simulates the probabilistic decision of whether the beneficiary will show up to collect the assigned surplus.
    # Returns bool: True if the beneficiary decides to pick up, False if no-show.
    def decide_pickup(self):
        return random.random() >= self.no_show_probability
    
    # Record and assignment event to the history log.
    def _log_assignment(self, surplus_id, tick, outcome):
        self.assignment_history.append(
            {
                # unique_id of the assigned SurplusAgent (int)
                "surplus_id": surplus_id,
                # current simulation tick at time of outcome (int)
                "tick": tick,
                # enter 'pickup' or 'no_show' (string)
                "outcome": outcome,
            }
        )
    
    # Executed once per simulation tick by Mesa scheduler.
    def step(self):
        pass