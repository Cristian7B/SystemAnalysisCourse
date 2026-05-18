import mesa
import math

VALID_STATUSES = {"published", "assigned", "collected", "expired", "reasigned"}

class SurplusAgent(mesa.Agent):
    # Represent a publised food surplus lot within the redistribution system
    def __init__(
        self, 
        unique_id, 
        model,
        donor_id,
        location,
        kg_available,
        published_at_tick,
        collection_deadline_tick,
    ):
        super().__init__(unique_id, model)
        self.donor_id = donor_id
        self.location = location
        self.kg_available = kg_available
        self.published_at_tick = published_at_tick
        self.collection_deadline_tick = collection_deadline_tick
        self.status = "published"
        self.assigned_to_id = None
        self.assigned_at_tick = None
        self.collected_at_tick = None
        self.reassignment_count = 0
        self.kg_collected = 0.0
    
    # Transitions the surplus from 'published' to 'assigned'
    # Returns bool: True if the assignment succeeded, False if surplus was not in 'pubished' state.
    def assign(self, recipient_id, tick):
        if self.status != "published":
            return False
        
        self.status = "assigned"
        self.assigned_to_id = recipient_id
        self.assigned_at_tick = tick
        return True
    
    # Transitions the surplus from 'assigned' to 'collected'
    # Returns bool: True if the collection succeeded, False if surplus was not in 'assigned' state
    def collect(self, kg, tick):
        if self.status != "assigned":
            return False
        
        self.status = "collected"
        self.kg_collected = kg
        self.collected_at_tick = tick
        return True
    
    # Transitions the surplus to 'expired' state
    # Returns bool: True if expiraction succeeded, False if surplus was alredy collected or in an invalid state for expiration
    def expire(self, trick):
        if self.status not in {"published", "assigned"}:
            return False
        
        self.status = "expired"
        return True

    # Resets an expired surplus back to 'published' for a new assignment attempt by the matching engine.
    # Returns bool: True if reassignment succeeded, False if surplus was not in 'expired' state.    
    def reassign(self, tick):
        if self.status != "expired":
            return False
        
        self.status = "published"
        self.assigned_to_id = None
        self.assigned_at_tick = None
        self.reassignment_count += 1
        return True
    
    # Checks whether this surplus has exceeded its collection deadline without being collected.
    # Returns bool:  True if the deadline has passed and the surplus is not yet collected.
    def is_expired(self, current_tick):
        return(
            current_tick > self.collection_deadline_tick
            and self.status != "collected"
        )
        
    # Computes the Euclidean distance between this surplus location and another point in the simulation grid.
    # Retuns float: Eucliden distance in km between self.location and location
    def distance_to(self, location):
        return math.sqrt(
            (self.location[0] - location[0]) ** 2 
            + (self.location[1] - location[1]) ** 2
        )
        
    # Executed once per simulation tick by the Mesa scheduler.
    def step(self):
        if self.status in {"collected", "expired"}:
            return
        
        current_tick = self.model.schedule.time
        
        if self.is_expired(current_tick):
            self.expire(current_tick)