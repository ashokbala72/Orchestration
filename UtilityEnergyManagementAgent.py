import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import random

# -------------------------
# Setup Azure OpenAI client
# -------------------------
load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# -------------------------
# Utility Energy Management Agent
# -------------------------
class UtilityEnergyManagementAgent:
    def __init__(self):
        # Sample tariff and carbon factors (can be replaced with live data)
        self.tariff = {
            "00:00-06:00": 2.5,
            "06:00-12:00": 5.0,
            "12:00-18:00": 7.0,
            "18:00-22:00": 10.0,
            "22:00-00:00": 3.5
        }
        self.carbon_factor = 0.233  # kg CO₂/kWh (UK grid factor)

    # Generate dispatch plan from demand + renewables
    def optimize_dispatch(self, demand_forecast, renewable_plan, assets, grid_exceptions):
        plan = []
        if not demand_forecast or not renewable_plan:
            return []

        for i, d in enumerate(demand_forecast[:10]):  # look at 10-day horizon
            demand = d.get("base_case", 1000)
            renewables = renewable_plan[i].get("renewables_mw", 0) if i < len(renewable_plan) else 0
            backup = max(0, demand - renewables)

            impacted_zone = None
            if grid_exceptions:
                impacted_zone = random.choice(grid_exceptions).get("substation", None)

            plan.append({
                "day": d.get("date", str(datetime.today().date())),
                "demand_mw": demand,
                "renewables_mw": renewables,
                "backup_mw": backup,
                "grid_constraint_zone": impacted_zone,
                "action": "normal" if backup < demand * 0.3 else "shift load / demand response"
            })
        return plan

    # Load shifting recommendations
    def recommend_load_shifting(self, plan):
        if not plan:
            return "No plan available."
        peak_days = [p for p in plan if p["backup_mw"] > p["demand_mw"] * 0.3]
        if not peak_days:
            return "No significant load shifting required."
        return f"Shift ~{len(peak_days)*100} MW of industrial/commercial load to off-peak hours."

    # Efficiency advisory based on asset performance
    def efficiency_advisory(self, assets):
        if not assets:
            return "No asset data available."
        inefficient = [a for a in assets if a.get("Degradation %", 0) > 70]
        if not inefficient:
            return "All major assets are within efficiency norms."
        return f"{len(inefficient)} assets show high degradation — recommend maintenance scheduling."

    # Carbon footprint estimation
    def estimate_carbon(self, plan):
        if not plan:
            return {"total_emissions_kg": 0}
        total_energy = sum([p["demand_mw"] for p in plan])
        return {"total_emissions_kg": round(total_energy * self.carbon_factor, 2)}

    # GenAI summary
    def genai_summary(self, plan, load_shift, efficiency, carbon):
        sample = pd.DataFrame(plan).head(5).to_string(index=False) if plan else "No plan"
        prompt = f"""
You are an energy management advisor. Analyze the following operational plan:

{sample}

Load Shifting Advice: {load_shift}
Efficiency Advice: {efficiency}
Carbon Outlook: {carbon}

Provide a concise management summary with recommended actions.
"""
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.4
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Summary error: {e}"

    # Main run
    def run(self, assets, grid_exceptions, demand_forecast, renewable_plan):
        plan = self.optimize_dispatch(demand_forecast, renewable_plan, assets, grid_exceptions)
        load_shift = self.recommend_load_shifting(plan)
        efficiency = self.efficiency_advisory(assets)
        carbon = self.estimate_carbon(plan)
        summary = self.genai_summary(plan, load_shift, efficiency, carbon)

        return {
            "agent": "utility_energy_management",
            "dispatch_plan": plan,
            "load_shifting": load_shift,
            "efficiency_advisory": efficiency,
            "carbon_footprint": carbon,
            "genai_summary": summary
        }
