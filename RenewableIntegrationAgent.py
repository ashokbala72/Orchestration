import pandas as pd
import numpy as np
import requests
import random
from datetime import datetime
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
# Renewable Integration Agent
# -------------------------
class RenewableIntegrationAgent:
    def __init__(self):
        pass

    # Weather forecast (10 hrs, via Open-Meteo)
    def fetch_weather_forecast(self, lat=51.5, lon=-0.1):
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,windspeed_10m,shortwave_radiation&forecast_days=1&timezone=auto"
        try:
            response = requests.get(url)
            hourly = response.json()['hourly']
            return pd.DataFrame({
                'time': pd.to_datetime(hourly['time']),
                'temperature_2m': hourly['temperature_2m'],
                'windspeed_10m': hourly['windspeed_10m'],
                'shortwave_radiation': hourly['shortwave_radiation']
            }).head(10)
        except:
            return pd.DataFrame()

    # Simulate live sensor feed
    def simulate_live_sensors(self):
        base_time = pd.Timestamp.now() - pd.Timedelta(minutes=9)
        timestamps = [base_time + pd.Timedelta(minutes=i) for i in range(10)]
        return pd.DataFrame({
            'timestamp': timestamps,
            'voltage': np.random.uniform(410, 430, size=10),
            'current': np.random.uniform(15, 25, size=10),
            'inverter_status': np.random.choice(['ON', 'STANDBY', 'FAULT'], size=10)
        })

    # Predict renewable output
    def predict_output(self, weather_df, sensor_df):
        if weather_df.empty or sensor_df.empty:
            return pd.DataFrame()
        forecast_df = weather_df.copy()
        forecast_df['voltage'] = sensor_df['voltage'].iloc[-1]
        forecast_df['current'] = sensor_df['current'].iloc[-1]
        forecast_df['inverter_status'] = sensor_df['inverter_status'].iloc[-1]
        forecast_df['predicted_output_mw'] = (
            0.4 * forecast_df['temperature_2m'] +
            0.5 * forecast_df['windspeed_10m'] +
            0.1 * forecast_df['shortwave_radiation'] / 10 +
            np.random.uniform(-1, 1, len(forecast_df))
        )
        return forecast_df

    # Integration planning: match renewables to demand forecast
    def integrate_with_demand(self, demand_forecast, prediction_df, grid_exceptions):
        plan = []
        if not demand_forecast or prediction_df.empty:
            return []

        # take first 10 steps for alignment
        for i, d in enumerate(demand_forecast[:10]):
            demand = d.get("base_case", 1000)
            renewables = prediction_df.iloc[min(i, len(prediction_df)-1)]['predicted_output_mw']
            backup = max(0, demand - renewables)

            impacted_zone = None
            if grid_exceptions:
                impacted_zone = random.choice(grid_exceptions).get("substation", None)

            plan.append({
                "day": d.get("date", str(datetime.today().date())),
                "demand_mw": demand,
                "renewables_mw": round(renewables, 2),
                "backup_mw": round(backup, 2),
                "grid_constraint_zone": impacted_zone
            })
        return plan

    # GenAI advisory
    def advisory(self, plan):
        if not plan:
            return "No integration plan generated."
        sample = pd.DataFrame(plan).head(5).to_string(index=False)
        prompt = f"""
You are a renewable integration advisor. Analyze the following demand vs renewable integration plan:

{sample}

1. Highlight renewable contribution percentage
2. Identify risks due to grid constraints
3. Suggest balancing actions (storage, curtailment, imports/exports)
4. Provide concise advisory for utility planners
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
            return f"⚠️ Advisory error: {e}"

    # Main run
    def run(self, demand_forecast, grid_exceptions, assets=None):
        weather_df = self.fetch_weather_forecast()
        sensor_df = self.simulate_live_sensors()
        prediction_df = self.predict_output(weather_df, sensor_df)

        integration_plan = self.integrate_with_demand(demand_forecast, prediction_df, grid_exceptions)
        advisory = self.advisory(integration_plan)

        return {
            "agent": "renewable_integration",
            "weather_forecast": weather_df.to_dict(orient="records"),
            "live_sensors": sensor_df.to_dict(orient="records"),
            "predicted_output": prediction_df.to_dict(orient="records"),
            "integration_plan": integration_plan,
            "genai_advisory": advisory
        }
