import pandas as pd
import random
import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

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
# Field Operations Agent
# -------------------------
class FieldOperationsAgent:
    def __init__(self):
        # Dummy technician pool (would come from HR/roster in production)
        self.technicians = [
            {"name": "Technician Smith", "skills": ["Transformer", "Relay"], "zone": "Zone A"},
            {"name": "Technician Patel", "skills": ["Generator", "Breaker"], "zone": "Zone B"},
            {"name": "Technician Wang", "skills": ["Inverter", "Smart Meter"], "zone": "Zone C"},
            {"name": "Technician Singh", "skills": ["Pipeline", "Compressor"], "zone": "Zone D"}
        ]

    # Step 1: Simulate new faults based on assets and grid exceptions
    def simulate_faults(self, assets, grid_exceptions, n=5):
        fault_codes = ["TRF101", "GEN203", "CB404", "INVT555"]
        equipments = ["Transformer", "Generator", "Circuit Breaker", "Inverter"]
        zones = ["Zone A", "Zone B", "Zone C", "Zone D"]

        faults = []
        for _ in range(n):
            faults.append({
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fault_code": random.choice(fault_codes),
                "equipment": random.choice(equipments),
                "location": random.choice(zones),
                "status": "New",
                "technician": None
            })
        return pd.DataFrame(faults)

    # Step 2: Assign technician to a fault
    def assign_technician(self, fault):
        available = [t for t in self.technicians if fault["equipment"] in t["skills"]]
        if available:
            tech = random.choice(available)
        else:
            tech = random.choice(self.technicians)
        fault["technician"] = tech["name"]
        fault["status"] = "Assigned"
        return fault

    # Step 3: Work order generation
    def generate_work_orders(self, faults_df, supply_chain):
        work_orders = []
        for _, row in faults_df.iterrows():
            fault = row.to_dict()
            fault = self.assign_technician(fault)

            # Check if spare part exists in supply chain forecast
            needed_part = next((p for p in supply_chain if row["equipment"] in p["Part Name"]), None)

            work_orders.append({
                "asset_id": fault.get("asset_id", "N/A"),
                "fault_code": fault["fault_code"],
                "equipment": fault["equipment"],
                "location": fault["location"],
                "assigned_to": fault["technician"],
                "status": fault["status"],
                "spare_part_needed": needed_part["Part Name"] if needed_part else "Unknown"
            })
        return work_orders

    # Step 4: GenAI risk & field advisory
    def advisory(self, work_orders, dispatch_plan):
        sample = pd.DataFrame(work_orders).head(5).to_string(index=False)
        dispatch_preview = pd.DataFrame(dispatch_plan).head(3).to_string(index=False)

        prompt = f"""
You are a field operations strategist. Review the following work orders:

{sample}

Operational Dispatch Context:
{dispatch_preview}

Provide:
1. Risk assessment (safety, outage impact, weather issues)
2. Priority ranking of tasks
3. Technician advisory (who should be supported, where delays expected)
4. Clear field guidance for the next 24h
"""
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.5
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Advisory error: {e}"

    # Step 5: Main run
    def run(self, assets, grid_exceptions, demand_forecast, renewable_plan, dispatch_plan, supply_chain):
        # Simulate faults
        faults_df = self.simulate_faults(assets, grid_exceptions, n=5)

        # Generate work orders
        work_orders = self.generate_work_orders(faults_df, supply_chain)

        # GenAI advisory
        advisory = self.advisory(work_orders, dispatch_plan)

        return {
            "agent": "field_operations",
            "faults": faults_df.to_dict(orient="records"),
            "work_orders": work_orders,
            "genai_field_advisory": advisory
        }
