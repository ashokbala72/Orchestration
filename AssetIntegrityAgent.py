import pandas as pd
import random
from datetime import datetime, timedelta
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
# Utility: Generate Assets
# -------------------------
def generate_assets():
    equipment_types = {
        "Pump": 30, "Compressor": 10, "Turbine": 5,
        "Heat Exchanger": 10, "Tank": 10, "Vessel": 5,
        "Pipeline": 15, "Motor": 10, "Control Panel": 5,
        "Sensor": 40
    }
    assets = []
    id_counter = 1
    for eq_type, count in equipment_types.items():
        for _ in range(count):
            assets.append({
                "Asset ID": f"A{id_counter:04d}",
                "Type": eq_type,
                "Location": f"Zone {random.choice(['A','B','C','D'])}",
                "Age (years)": random.randint(1, 20),
                "Last Maintenance": (datetime.today() - timedelta(days=random.randint(30, 900))).date().isoformat(),
                "Degradation %": round(random.uniform(10, 90), 2),
                "Status": random.choice(["Operational", "Under Maintenance", "Standby"]),
                "Vibration": round(random.uniform(0.1, 5.0), 2),
                "Temperature": round(random.uniform(30, 120), 1),
                "Corrosion Level": round(random.uniform(0, 1.0), 2),
                "RUL (months)": random.randint(1, 36)
            })
            id_counter += 1
    return pd.DataFrame(assets)

# -------------------------
# Utility: GenAI Advisory
# -------------------------
def genai_advisory(prompt: str):
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are an asset integrity advisor."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GenAI Error: {e}"

# -------------------------
# Asset Integrity Agent
# -------------------------
class AssetIntegrityAgent:
    def __init__(self):
        self.assets_df = generate_assets()

    def overview(self):
        return {
            "description": "AI-powered Asset Integrity Agent with modules for asset health, RUL, corrosion, failures, compliance, costs, and work orders.",
            "modules": [
                "Asset Register", "Lifespan Estimator", "Corrosion Simulator",
                "Failure Mode Predictor", "Field Report Summarizer",
                "Regulatory Watch", "Replacement Cost Forecast", "Work Order Optimizer"
            ]
        }

    def asset_register(self):
        return {"assets": self.assets_df.to_dict(orient="records")}

    def lifespan_estimator(self):
        low_rul_df = self.assets_df[self.assets_df["RUL (months)"] <= 6]
        advisories = []
        for _, sample in low_rul_df.iterrows():
            prompt = f"""Asset ID: {sample['Asset ID']}
Type: {sample['Type']}
Age: {sample['Age (years)']} years
Degradation: {sample['Degradation %']}%
Vibration: {sample['Vibration']}
Temperature: {sample['Temperature']} deg C
Corrosion Level: {sample['Corrosion Level']}
RUL: {sample['RUL (months)']} months
Explain why this asset's RUL is low and suggest next steps."""
            advisories.append({
                "asset": sample["Asset ID"],
                "advisory": genai_advisory(prompt)
            })
        return {"low_rul_assets": low_rul_df.to_dict(orient="records"), "advisories": advisories}

    def corrosion_simulator(self):
        corroding = self.assets_df.sort_values("Corrosion Level", ascending=False).head(5)
        advisories = []
        for _, row in corroding.iterrows():
            prompt = f"Asset {row['Asset ID']} has corrosion level {row['Corrosion Level']}. Suggest mitigation strategy."
            advisories.append({"asset": row["Asset ID"], "advisory": genai_advisory(prompt)})
        return {"top_corroding": corroding.to_dict(orient="records"), "advisories": advisories}

    def failure_mode_predictor(self):
        risky = self.assets_df.sort_values("Degradation %", ascending=False).head(5)
        advisories = []
        for _, row in risky.iterrows():
            prompt = f"Predict failure modes for {row['Asset ID']} ({row['Type']}) with degradation {row['Degradation %']}%."
            advisories.append({"asset": row["Asset ID"], "advisory": genai_advisory(prompt)})
        return {"risky_assets": risky.to_dict(orient="records"), "advisories": advisories}

    def field_report_summary(self, note: str):
        if not note:
            return {"error": "No field report provided"}
        prompt = f"Summarize this field report into risk advisory:\n{note}"
        return {"field_report": note, "summary": genai_advisory(prompt)}

    def regulatory_watch(self):
        sample = self.assets_df.sample(1).iloc[0]
        prompt = f"The asset {sample['Asset ID']} is {sample['Age (years)']} years old with degradation {sample['Degradation %']}%, in {sample['Location']}. Predict compliance risks."
        return {"asset": sample["Asset ID"], "advisory": genai_advisory(prompt)}

    def replacement_cost_forecast(self):
        def get_equipment_cost(eq_type):
            catalog = {
                "Pump": random.randint(5000, 15000),
                "Compressor": random.randint(20000, 60000),
                "Turbine": random.randint(40000, 120000),
                "Tank": random.randint(15000, 40000),
                "Sensor": random.randint(500, 3000),
                "Pipeline": random.randint(10000, 30000),
                "Motor": random.randint(8000, 20000),
                "Control Panel": random.randint(5000, 15000),
                "Heat Exchanger": random.randint(10000, 25000),
                "Vessel": random.randint(12000, 35000)
            }
            return catalog.get(eq_type, 10000)

        low_rul = self.assets_df[self.assets_df["RUL (months)"] <= 6]
        if low_rul.empty:
            return {"message": "No assets nearing end of life"}
        low_rul["Replacement Cost ($)"] = low_rul["Type"].apply(get_equipment_cost)
        low_rul["Replace By"] = pd.to_datetime('today') + pd.to_timedelta(low_rul["RUL (months)"] * 30, unit='D')
        total = low_rul["Replacement Cost ($)"].sum()
        prompt = f"In the next 6 months, assets totaling ${total} are due for replacement. Provide a capital planning summary."
        return {
            "assets_due": low_rul.to_dict(orient="records"),
            "capital_summary": genai_advisory(prompt)
        }

    def work_order_optimizer(self):
        critical_assets = self.assets_df[self.assets_df["RUL (months)"] <= 3]
        if critical_assets.empty:
            return {"message": "No urgent work orders required"}
        sample = critical_assets.sample(1).iloc[0]
        prompt = f"""Create a prioritized maintenance work order for:
Asset: {sample['Asset ID']}
Type: {sample['Type']}
Location: {sample['Location']}
Status: {sample['Status']}
RUL: {sample['RUL (months)']} months
Vibration: {sample['Vibration']}
Temperature: {sample['Temperature']} deg C
Corrosion: {sample['Corrosion Level']}
Suggest optimal technician type and urgency."""
        return {
            "critical_assets": critical_assets.to_dict(orient="records"),
            "work_order": genai_advisory(prompt)
        }

    def run(self, action: str, **kwargs):
        mapping = {
            "overview": self.overview,
            "asset_register": self.asset_register,
            "lifespan": self.lifespan_estimator,
            "corrosion": self.corrosion_simulator,
            "failure_mode": self.failure_mode_predictor,
            "field_report": lambda: self.field_report_summary(kwargs.get("note", "")),
            "regulatory": self.regulatory_watch,
            "replacement_cost": self.replacement_cost_forecast,
            "work_order": self.work_order_optimizer
        }
        if action in mapping:
            return mapping[action]()
        return {"error": f"Unknown action {action}"}
