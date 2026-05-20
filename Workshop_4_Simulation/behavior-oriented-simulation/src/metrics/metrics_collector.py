import pandas as pd
from datetime import datetime

from src.agents.beneficiary_agent import BeneficiaryAgent
from src.agents.charity_agent import CharityAgent
from src.agents.volunteer_agent import VolunteerAgent

class MetricsCollector:
    # Observes and records simulation state across all ticks of a single run.
    def __init__(self, model, scenario_name):
        self.model = model
        self.scenario_name = scenario_name
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.tick_records = []
        self.agent_records = []
        
    # Captures a snapshot of the current simulation state and appends ot to tick_records
    def record_tick(self):
        metrics = self.model.get_metrics()
        
        record = {
            "scenario": self.scenario_name,
            "run_id": self.run_id,
            "n_donors": self.model.n_donors,
            "n_beneficiaries": self.model.n_beneficiaries,
            "n_charities": self.model.n_charities,
            "n_volunteers": self.model.n_volunteers,
            **metrics,
        }
        
        self.tick_records.append(record)
        
    # Captures the final state of all recipient agents at the end of a simulation run.
    def record_agents(self):
        for agent in self.model.beneficiaries + self.model.charities:
            total_interactions = agent.total_pickups + agent.total_no_shows
            no_show_rate = (
                agent.total_no_shows / total_interactions
                if total_interactions > 0
                else 0.0
            )

            self.agent_records.append(
                {
                    "scenario": self.scenario_name,
                    "run_id": self.run_id,
                    "agent_id": agent.unique_id,
                    "agent_type": type(agent).__name__,
                    "final_reliability_score": agent.reliability_score,
                    "total_pickups": agent.total_pickups,
                    "total_no_shows": agent.total_no_shows,
                    "no_show_rate": round(no_show_rate, 4),
                    "is_charity": isinstance(agent, CharityAgent),
                }
            )

        for agent in self.model.volunteers:
            total_interactions = agent.total_assists + agent.total_no_shows
            no_show_rate = (
                agent.total_no_shows / total_interactions
                if total_interactions > 0
                else 0.0
            )

            self.agent_records.append(
                {
                    "scenario": self.scenario_name,
                    "run_id": self.run_id,
                    "agent_id": agent.unique_id,
                    "agent_type": type(agent).__name__,
                    "final_reliability_score": agent.reliability_score,
                    "total_assists": agent.total_assists,
                    "total_no_shows": agent.total_no_shows,
                    "no_show_rate": round(no_show_rate, 4),
                    "is_charity": False,
                }
            )
    
    # Returns the tick-level time series as a pandas DataFrame
    def to_dataframe(self):
        if not self.tick_records:
            return pd.DataFrame(columns=[
                "scenario", "run_id", "tick",
                "n_donors", "n_beneficiaries", "n_charities", "n_volunteers",
                "total_surpluses_published", "total_collected", "total_expired",
                "total_reassigned", "active_surpluses", "recovery_rate",
                "avg_reassignment_count", "total_assignments",
                "pickup_completion_rate",
            ])

        return pd.DataFrame(self.tick_records)
    
    # Returns the agent-level end-of-run metrics as a pandas DataFrame.
    def agents_to_dataframe(self):
        if not self.agent_records:
            return pd.DataFrame(columns=[
                "scenario", "run_id", "agent_id", "agent_type",
                "final_reliability_score", "total_pickups",
                "total_no_shows", "no_show_rate", "is_charity",
            ])
            
        return pd.DataFrame(self.agent_records)
    
    # Returns a single-run summary with aggegated metrics
    def get_summary(self):
        final_metrics = self.model.get_metrics()
        
        no_show_rates = [
            r["no_show_rate"]
            for r in self.agent_records
            if "no_show_rate" in r
        ]
        avg_no_show_rate = (
            sum(no_show_rates) / len(no_show_rates)
            if no_show_rates
            else 0.0
        )
        
        assignment_log = self.model.matching_engine.assignment_log
        total_assignments = len(assignment_log)
        charity_assignments = sum(
            1 for e in assignment_log
            if e["recipient_type"] == "CharityAgent"
        )
        charity_assignment_share = (
            charity_assignments / total_assignments
            if total_assignments > 0
            else 0.0
        )

        return {
            "scenario": self.scenario_name,
            "run_id": self.run_id,
            "final_recovery_rate": final_metrics["recovery_rate"],
            "final_pickup_completion_rate": final_metrics["pickup_completion_rate"],
            "total_surpluses_published": final_metrics["total_surpluses_published"],
            "total_collected": final_metrics["total_collected"],
            "total_expired": final_metrics["total_expired"],
            "total_assignments": final_metrics["total_assignments"],
            "total_reassignments": final_metrics["total_reassigned"],
            "avg_no_show_rate": round(avg_no_show_rate, 4),
            "charity_assignment_share": round(charity_assignment_share, 4),
        }