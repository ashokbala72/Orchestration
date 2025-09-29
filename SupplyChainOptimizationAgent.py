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
# Supply Chain Optimization Agent
# -------------------------
class SupplyChainOptimizationAgent:
    def __init__(self):
        self.vendor_pool = ["ABB", "Siemens", "GE", "Schneider", "Hitachi", "Mitsubishi"]

    # Generate spare parts inventory based on company type
    def generate_parts(self, company_type):
        part_names = {
            "Transmission Operator": ["Transformer Coil", "HV Cable Drum", "Insulator Bushing", "Surge Arrester"],
            "Distribution Operator": ["Feeder Line Kit", "Fuse Switch", "Distribution Box", "Smart Meter"],
            "Generation Company": ["Gas Turbine Blade", "Steam Turbine Rotor", "Generator Exciter", "Control Valve"],
            "Retail Energy Supplier": ["Smart Meter", "Home Energy Monitor", "WiFi Gateway"],
            "Integrated Utility": ["Universal Switchgear", "Multi-purpose Relay", "Hybrid Transformer"]
        }
        parts = part_names.get(company_type, [])
        df = pd.DataFrame([{
            "Part Name": p,
            "Installed Base": random.randint(50, 300),
            "Stock": random.randint(1, 20),
            "Lead Time (days)": random.choice([7, 14, 21, 28]),
            "Failure Rate": round(random.uniform(0.01, 0.15), 2)
        } for p in parts])
        return df

    # Forecast spare part demand
    def forecast_parts(self, df, forecast_months=3):
        df["Forecast Qty"] = (df["Installed Base"] * df["Failure Rate"] * forecast_months).round().astype(int)
        df["Expected Shortage"] = df["Forecast Qty"] - df["Stock"]
        return df

    # Recommend reorder quantities (EOQ + shortage logic)
    def reorder_plan(self, df):
        ordering_cost = 50
        holding_cost = 10
        df["EOQ"] = ((2 * df["Forecast Qty"] * ordering_cost) / holding_cost) ** 0.5
        df["EOQ"] = df["EOQ"].round().astype(int)
        df["Recommended Qty"] = df.apply(lambda row: max(row["Expected Shortage"], row["EOQ"]), axis=1).astype(int)
        return df

    # Generate vendor options
    def vendor_selection(self, df):
        vendor_records = []
        for _, row in df.iterrows():
            for _ in range(3):
                vendor_records.append({
                    "Part Name": row["Part Name"],
                    "Vendor": random.choice(self.vendor_pool),
                    "Unit Cost (£)": round(random.uniform(100, 500), 2),
                    "Lead Time (days)": random.choice([7, 14, 21]),
                    "Reliability (%)": round(random.uniform(85, 99), 2)
                })
        return pd.DataFrame(vendor_records)

    # GenAI summary
    def genai_summary(self, df, vendor_df, dispatch_plan):
        prompt = f"""
You are a supply chain advisor. Analyze the following:

Spare Parts: {df.to_dict(orient="records")}
Vendors: {vendor_df.head(10).to_dict(orient="records")}
Dispatch Plan (from Energy Management): {dispatch_plan[:3]}

1. Identify risks in spare part shortages
2. Recommend vendor strategy
3. Suggest urgent procurement actions
4. Provide executive summary
"""
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=350,
                temperature=0.4
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ GenAI error: {e}"

    # Main run
    def run(self, assets, grid_exceptions, demand_forecast, renewable_plan, dispatch_plan, company_type="Transmission Operator"):
        # Step 1: Generate parts
        df_parts = self.generate_parts(company_type)

        # Step 2: Forecast demand for parts
        df_parts = self.forecast_parts(df_parts)

        # Step 3: Reorder recommendations
        df_parts = self.reorder_plan(df_parts)

        # Step 4: Vendor options
        vendor_df = self.vendor_selection(df_parts)

        # Step 5: Advisory
        advisory = self.genai_summary(df_parts, vendor_df, dispatch_plan)

        return {
            "agent": "supply_chain_optimization",
            "parts_forecast": df_parts.to_dict(orient="records"),
            "vendors": vendor_df.to_dict(orient="records"),
            "dispatch_dependency": dispatch_plan[:3],  # sample slice
            "genai_advisory": advisory
        }
