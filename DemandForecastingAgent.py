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
# Demand Forecasting Agent
# -------------------------
class DemandForecastingAgent:
    def __init__(self):
        pass

    # Step 1: Generate historical demand data
    def historical_data(self, start="2020-01-01", end="2024-12-31"):
        date_rng = pd.date_range(start=start, end=end, freq="D")
        seasonal_trend = 200 * np.sin(2 * np.pi * date_rng.dayofyear / 365.25)
        random_noise = np.random.normal(0, 50, len(date_rng))
        load_values = 1200 + seasonal_trend + random_noise
        df = pd.DataFrame({"date": date_rng, "load": load_values.astype(int)})
        return df

    # Step 2: Aggregated trends + GenAI insight
    def aggregated_trends(self, hist_df):
        agg_df = hist_df.groupby("date").agg({"load": "sum"}).reset_index()
        sample_preview = agg_df.head(10).to_string(index=False)
        prompt = f"""
        Analyze the following historical electricity demand trends:

        {sample_preview}

        Summarize key patterns, risks, and implications for future planning.
        """
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are an energy demand analyst."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=250,
                temperature=0.4,
            )
            insight = resp.choices[0].message.content
        except Exception as e:
            insight = f"⚠️ GenAI error: {e}"
        return {"aggregated": agg_df.to_dict(orient="records"), "genai_insight": insight}

    # Step 3: Generate scenario prompt (adjusted with assets + grid faults)
    def scenario_prompt(self, assets, grid_exceptions):
        risky_assets = [a for a in assets if a.get("RUL (months)", 12) <= 3]
        risky_zones = [e.get("substation") for e in grid_exceptions] if grid_exceptions else []

        base_prompt = "Electricity demand may fluctuate due to seasonal and economic conditions."
        if risky_assets:
            base_prompt += f" Several critical assets are nearing end of life ({len(risky_assets)} assets flagged), which may increase reliance on backup generation."
        if risky_zones:
            base_prompt += f" Grid reliability issues detected in substations {set(risky_zones)}, potentially raising peak demand in other zones."

        return base_prompt

    # Step 4: Scenario narrative (GenAI)
    def scenario_narrative(self, scenario_prompt, hist_df):
        preview = hist_df.tail(10).to_string(index=False)
        prompt = f"""
        Given the historical demand data sample:
        {preview}

        Scenario Context:
        {scenario_prompt}

        Describe how demand may evolve under this scenario and suggest operational strategies.
        """
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are a scenario modeling expert for energy utilities."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.5,
            )
            narrative = resp.choices[0].message.content
        except Exception as e:
            narrative = f"⚠️ GenAI error: {e}"
        return narrative

    # Step 5: Forecast generation with scenarios
    def forecast(self, horizon_days=30):
        future_dates = pd.date_range(datetime.today(), periods=horizon_days, freq="D")
        base_forecast = 1300 + 100 * np.sin(2 * np.pi * future_dates.dayofyear / 365.25)
        noise = np.random.normal(0, 30, len(future_dates))
        forecast_base = base_forecast + noise

        # Scenario adjustments
        forecast_cold_wave = forecast_base * 1.2
        forecast_recession = forecast_base * 0.9
        forecast_supply_shock = forecast_base * 1.15

        df = pd.DataFrame({
            "date": future_dates,
            "base_case": forecast_base.astype(int),
            "cold_wave": forecast_cold_wave.astype(int),
            "recession": forecast_recession.astype(int),
            "supply_shock": forecast_supply_shock.astype(int)
        })
        return df

    # Step 6: Advisory on forecast
    def forecast_advisory(self, forecast_df):
        preview = forecast_df.tail(10).to_string(index=False)
        prompt = f"""
        Analyze the following 10-day electricity demand forecast:

        {preview}

        1. Highlight anomalies or risks
        2. Suggest operational strategies (demand response, reserves, storage)
        3. Provide recommendations for utility planners
        """
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[
                    {"role": "system", "content": "You are a UK energy grid analyst."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=300,
                temperature=0.5,
            )
            advisory = resp.choices[0].message.content
        except Exception as e:
            advisory = f"⚠️ GenAI error: {e}"
        return advisory

    # Main run method (integrated with Agent 1 + Agent 2 outputs)
    def run(self, assets, grid_exceptions, horizon_days=30):
        # Step 1: Historical data
        hist_df = self.historical_data()

        # Step 2: Aggregated trends
        agg = self.aggregated_trends(hist_df)

        # Step 3: Scenario prompt
        scenario = self.scenario_prompt(assets, grid_exceptions)

        # Step 4: Scenario narrative
        narrative = self.scenario_narrative(scenario, hist_df)

        # Step 5: Forecast
        forecast_df = self.forecast(horizon_days)

        # Step 6: Advisory
        advisory = self.forecast_advisory(forecast_df)

        return {
            "agent": "demand_forecasting",
            "historical_summary": f"{len(hist_df)} days of demand history generated.",
            "aggregated_trends": agg,
            "scenario_prompt": scenario,
            "scenario_narrative": narrative,
            "forecast": forecast_df.to_dict(orient="records"),
            "genai_advisory": advisory
        }
