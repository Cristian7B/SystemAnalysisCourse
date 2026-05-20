import mesa 
import random

class DonorAgent(mesa.Agent):
    # Represents a cafeteria or restaurant that publishes food surplus
    def __init__(
        self,
        unique_id,
        model,
        name,
        location,
        surplus_kg_min=5.0,
        surplus_kg_max=15.0,
    ):
        super().__init__(unique_id, model)
        self.name = name
        self.location = location
        self.is_active = True
        self.surplus_kg_min = surplus_kg_min
        self.surplus_kg_max = surplus_kg_max
        self.publication_window_open = False
        self.published_today = False
        self.total_kg_published = 0.0
    
    # Generates and records a surplus publication if conditions are met
    # Returns the kg of surplus published (or none)
    def publish_surplus(self):
        if not self.is_active or self.published_today:
            return None
        
        kg = random.uniform(self.surplus_kg_min, self.surplus_kg_max)
        self.total_kg_published += kg
        self.published_today = True
        return kg
    
    # Resets per-day state flags. Called by the model at the start of each new simulation day.
    def reset_daily_state(self):
        self.published_today = False
        self.publication_window_open = False
    
    # Executed once per simulation tick by Mesa scheduler.
    def step(self):
        if self.publication_window_open and not self.published_today:
            self.publish_surplus()