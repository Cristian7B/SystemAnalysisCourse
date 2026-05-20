from src.agents.charity_agent import CharityAgent
from src.agents.volunteer_agent import VolunteerAgent
from src.model.constants import GRID_SIZE_KM

WEIGHT_PROXIMITY = 0.5
WEIGHT_RELIABILITY = 0.3
WEIGHT_CHARITY = 0.2

RADIUS_RING_1 = 0.5
RADIUS_RING_2 = 1.0
RADIUS_RING_3 = 3.0

DELAY_RING_1 = 2
DELAY_RING_2 = 4

MAX_REASSIGNMENT_ATTEMPTS = 3

class MatchingEngine:
    # serialized priority matching engine for the Food Waste Reduction Platform.
    # Implements the composite scoring algorithm specified in the simulation docuemtn (REQ-05), combining proximity, reliability, and charity priority into a single score used to select the best recipient for each published surplus
    def __init__(self, model):
        self.model = model
        self.assignment_log = []
        
    # Determines the current search radius for a surplus based on how many ticks have elapsed since its publication.
    # Implements the staged notifications sistem (REQ-06): Rign1 - 500m, Ring2 - 1km, Ring3 - 3km
    # Returns float: Active research radous in km
    def _determine_active_radius(self, surplus, tick):
        ticks_elapsed = tick - surplus.published_at_tick
        
        if ticks_elapsed < DELAY_RING_1:
            return RADIUS_RING_1
        if ticks_elapsed < DELAY_RING_2:
            return RADIUS_RING_2
        return RADIUS_RING_3
    
    # Checks wheter an agent is currently avalaible to receive a new surplus assignment.
    # Returns bool: True if the adent can accept a new assignment.
    def _is_available(self, agent):
        if hasattr(agent, "is_available"):
            return agent.is_available
        return agent.current_assignment is None
    
    # Returns a list with all available agents within the specificed radous of the surplus location.
    def _get_eligible_recipients(self, surplus, max_radius):
        all_candidates = (
            self.model.beneficiaries + self.model.charities + self.model.volunteers
        )
        
        eligible = []
        for agent in all_candidates:
            if not agent.is_active:
                continue
            if not self._is_available(agent):
                continue
            distance = surplus.distance_to(agent.location)
            if distance <= max_radius:
                eligible.append(agent)
        
        return eligible
    
    # Computes the composite matching score for a surplus_agent pair.
    # Returns float: Compositive score in [0.0, 1.0]. Retunrs 0.0 id the agent is beyond GRID_SIZE_KM
    def _compute_score(self, surplus, agent):
        distance = surplus.distance_to(agent.location)
        
        if distance > GRID_SIZE_KM:
            return 0.0
        
        proximity_score = 1.0 - (distance / GRID_SIZE_KM)
        reliability_score = agent.reliability_score / 100.0
        charity_bonus = 1.0 if isinstance(agent, CharityAgent) else 0.0
        
        return (
            (WEIGHT_PROXIMITY * proximity_score) + (WEIGHT_RELIABILITY * reliability_score) + (WEIGHT_CHARITY * charity_bonus)
        )
        
    # Selects the candidate with the highest composite scroe
    # Returns: (Agent) the best-scoring candidate, (None) if the candidates is empty
    def _select_best(self, surplus, candidates):
        if not candidates:
            return None
        
        return max(
            candidates,
            key=lambda agent: self._compute_score(surplus, agent),
        )
    
    # Executes the physical assignment between a surplu and a recipient
    # Returns bool: True if the assignment was recorded successfully
    def _assign(self, surplus, recipient, tick, ring):
        score = self._compute_score(surplus, recipient)
        
        surplus.assign(recipient.unique_id, tick)
        
        if isinstance(recipient, VolunteerAgent):
            recipient.accept_mission(surplus)
        else:
            recipient.current_assignment = surplus
        
        self.assignment_log.append(
            {
                "surplus_id": surplus.unique_id,
                "recipient_id": recipient.unique_id,
                "recipient_type": type(recipient).__name__,
                "tick": tick,
                "score": round(score, 4),
                "ring": ring,
            }
        )
        
        return True
    
    # Processes pickup outcomes for all currently assigned surpluses
    def _process_collections(self, tick):
        for surplus in list(self.model.active_surpluses):
            if surplus.status != "assigned":
                continue
            if surplus.assigned_at_tick is None or surplus.assigned_at_tick >= tick:
                continue

            all_recipients = (
                self.model.beneficiaries
                + self.model.charities
                + self.model.volunteers
            )
            recipient = next(
                (a for a in all_recipients if a.unique_id == surplus.assigned_to_id),
                None,
            )

            if recipient is None:
                continue

            if isinstance(recipient, VolunteerAgent):
                will_collect = recipient.decide_mission()
            else:
                will_collect = recipient.decide_pickup()

            if will_collect:
                surplus.collect(surplus.kg_available, tick)
                recipient.update_reliability(successful=True)
                if isinstance(recipient, VolunteerAgent):
                    recipient.total_assists += 1
                    recipient._log_mission(surplus.unique_id, tick, outcome="completed")
                    recipient.current_mission = None
                    recipient.is_available = True
                else:
                    recipient._log_assignment(surplus.unique_id, tick, outcome="pickup")
                    recipient.current_assignment = None
            else:
                recipient.update_reliability(successful=False)
                if isinstance(recipient, VolunteerAgent):
                    recipient._log_mission(surplus.unique_id, tick, outcome="no_show")
                    recipient.current_mission = None
                    recipient.is_available = True
                else:
                    recipient._log_assignment(surplus.unique_id, tick, outcome="no_show")
                    recipient.current_assignment = None

                self._release_recipient(surplus)
                if surplus.reassignment_count >= MAX_REASSIGNMENT_ATTEMPTS:
                    surplus.expire(tick)
                else:
                    surplus.reassign(tick)
        
        # Clears the assignment state on the recipient currently holding this surplus, freeing them to receive a new assignment
    def _release_recipient(self, surplus):
        if surplus.assigned_to_id is None:
            return

        all_recipients = (
            self.model.beneficiaries
            + self.model.charities
            + self.model.volunteers
        )

        for agent in all_recipients:
            if agent.unique_id == surplus.assigned_to_id:
                if isinstance(agent, VolunteerAgent):
                    agent.current_mission = None
                    agent.is_available = True
                else:
                    agent.current_assignment = None
                break
        
     # Scans active surpluses for axpired entries and eiter reassigns or permanently expires the based on reassignment_count.
    def _handle_expired_surpluses(self, tick):
        for surplus in list(self.model.active_surpluses):
            if surplus.status == "collected":
                continue
            if surplus.status == "assigned":
                if surplus.assigned_at_tick is not None and surplus.assigned_at_tick >= tick - 1:
                    continue
            if not surplus.is_expired(tick):
                continue
            if surplus.status not in {"published", "assigned"}:
                continue

            self._release_recipient(surplus)
            surplus.expire(tick)

            if surplus.reassignment_count >= MAX_REASSIGNMENT_ATTEMPTS:
                pass
            else:
                surplus.reassign(tick)

    # Maps a radius value its corresponding ring number for logging
    # Returns int: Ring number
    def _get_ring_number(self, radius):
        if radius <= RADIUS_RING_1:
            return 1
        if radius <= RADIUS_RING_2:
            return 2
        return 3
    
    # Main Matching loop executed once per simulation tick by FoodWasteModel.step()
    def run(self, tick):
        self._process_collections(tick)

        current_assigned = sum(
            1 for s in self.model.active_surpluses
            if s.status == "assigned"
        )

        for surplus in list(self.model.active_surpluses):
            if surplus.status != "published":
                continue

            max_cap = self.model.max_concurrent_assignments
            if max_cap is not None and current_assigned >= max_cap:
                break

            active_radius = self._determine_active_radius(surplus, tick)
            candidates = self._get_eligible_recipients(surplus, active_radius)
            best = self._select_best(surplus, candidates)

            if best is not None:
                ring = self._get_ring_number(active_radius)
                self._assign(surplus, best, tick, ring)
                current_assigned += 1

        self._handle_expired_surpluses(tick)