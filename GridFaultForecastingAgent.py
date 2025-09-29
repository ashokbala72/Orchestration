import pandas as pd
import random
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

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
# Grid Fault Forecasting Agent
# -------------------------
class GridFaultForecastingAgent:
    def __init__(self):
        pass

    # Always simulate events from assets
    def simulate_events_from_assets(self, assets):
        events = []
        fault_types = ["Outage", "Overload", "RelayTrip", "VoltageDip"]
        for asset in assets:
            # Simulate a few events per asset randomly
            if random.random() < 0.3:  # 30% chance an asset produces an event
                events.append({
                    "timestamp": datetime.now().isoformat(),
                    "substation": asset.get("Location", "Zone X"),
                    "event_type": random.choice(fault_types),
                    "fault_code": random.choice(["F001", "F002", "F003", "None"]),
                    "load_MW": round(random.uniform(50, 120), 2),
                    "asset_id": asset.get("Asset ID", "Unknown")
                })
        return pd.DataFrame(events)

    # Root cause + advisory
    def analyze_event(self, row_dict):
        prompt = (
            f"You are a grid reliability assistant. Analyze this simulated grid event:\n\n"
            f"Asset: {row_dict.get('asset_id')}\n"
            f"Substation: {row_dict.get('substation')}\n"
            f"Event Type: {row_dict.get('event_type')}\n"
            f"Fault Code: {row_dict.get('fault_code')}\n"
            f"Load (MW): {row_dict.get('load_MW')}\n\n"
            f"Provide a short root cause analysis and preventive action."
        )
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.4,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"⚠️ Error: {e}"

    # Executive summary
    def summarize_exceptions(self, exceptions_df):
        if exceptions_df.empty:
            return "No simulated exceptions detected."
        prompt = (
            f"As an AI grid analyst, review {len(exceptions_df)} simulated exceptions.\n"
            f"Highlight:\n- Common event types\n- Risky substations\n- Fault patterns\n- Recommendations\n\n"
            f"Sample Data:\n{exceptions_df[['event_type','substation','fault_code','load_MW']].head(10).to_string(index=False)}"
        )
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
                temperature=0.4,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Summary Error: {e}"

    # Manager insights
    def manager_insights(self, exceptions_df):
        if exceptions_df.empty:
            return "No management actions required."
        prompt = (
            f"As a grid operations strategist, analyze these {len(exceptions_df)} simulated exceptions.\n"
            f"Give recommendations for grid reliability and operational efficiency.\n\n"
            f"Data:\n{exceptions_df[['event_type','substation','fault_code','load_MW']].head(10).to_string(index=False)}"
        )
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.4,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Insight Error: {e}"

    # Forecast future issues
    def forecast_future(self, df):
        if df.empty:
            return "No simulated data to forecast."
        prompt = f"""You are a predictive reliability analyst. Forecast operational risks for the next 30 days.

Tasks:
1. Identify substations likely to face repeat faults or overloads
2. Detect event patterns that signal emerging risks
3. Suggest preventive actions
4. Recommend inventory to stock (relays, breakers, fuses) with quantities by substation

Recent Simulated Events:
{df[['timestamp','substation','event_type','fault_code','load_MW']].tail(20).to_string(index=False)}
"""
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You forecast grid issues and recommend parts inventory."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.4,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Forecast Error: {e}"

    # Main Run
    def run(self, assets):
        if not assets:
            return {"error": "No assets provided from AssetIntegrityAgent."}

        # Always simulate events from assets
        events_df = self.simulate_events_from_assets(assets)

        exceptions = []
        for _, row in events_df.iterrows():
            if row.get("event_type") in ["Outage", "Overload", "RelayTrip"] or row.get("load_MW", 0) > 80:
                advisory = self.analyze_event(row.to_dict())
                record = row.to_dict()
                record["GenAI Advisory"] = advisory
                exceptions.append(record)

        exceptions_df = pd.DataFrame(exceptions)

        # Trends
        trends = {}
        if not events_df.empty:
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
            trend_df = events_df.groupby([pd.Grouper(key='timestamp', freq='D'), 'event_type']).size().unstack(fill_value=0)
            trends = trend_df.to_dict()

        # Repetitive faults
        repetitive = []
        if not events_df.empty and "fault_code" in events_df.columns:
            repeat_faults = events_df[events_df['fault_code'].notnull()].groupby(['substation', 'fault_code']).size().reset_index(name='count')
            repetitive = repeat_faults[repeat_faults['count'] > 1].to_dict(orient="records")

        # Clustering
        clusters = []
        if not events_df.empty and "load_MW" in events_df.columns:
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(events_df[['load_MW']].fillna(0))
            kmeans = KMeans(n_clusters=3, random_state=42)
            events_df['cluster'] = kmeans.fit_predict(scaled_features)
            clusters = events_df[['substation', 'event_type', 'load_MW', 'cluster']].to_dict(orient="records")

        return {
            "simulated_events": events_df.to_dict(orient="records"),
            "detected_exceptions": exceptions,
            "trends": trends,
            "repetitive_faults": repetitive,
            "clusters": clusters,
            "executive_summary": self.summarize_exceptions(exceptions_df),
            "manager_insights": self.manager_insights(exceptions_df),
            "forecast": self.forecast_future(events_df)
        }
