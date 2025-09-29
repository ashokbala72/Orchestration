import pandas as pd
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
# Energy Trading Agent
# -------------------------
class EnergyTradingAgent:
    def __init__(self):
        pass

    # Market position based on dispatch vs demand
    def calculate_position(self, demand_forecast, dispatch_plan):
        if not demand_forecast or not dispatch_plan:
            return {"surplus_deficit_mwh": 0, "recommendation": "HOLD"}

        # Aggregate demand & supply
        demand = sum([d.get("base_case", 1000) for d in demand_forecast[:5]])
        supply = sum([p.get("renewables_mw", 0) + p.get("backup_mw", 0) for p in dispatch_plan[:5]])

        # Apply forecast error and reserve margin
        forecast_error = random.uniform(-0.05, 0.05)  # ±5% demand forecast error
        reserve_margin = random.uniform(-0.08, 0.08)  # ±8% supply inefficiency

        adjusted_demand = int(demand * (1 + forecast_error))
        adjusted_supply = int(supply * (1 + reserve_margin))

        balance = adjusted_supply - adjusted_demand

        # Add buffer so tiny noise doesn't cause false buy/sell
        if balance > 50:
            rec = f"Sell {abs(balance)} MWh"
        elif balance < -50:
            rec = f"Buy {abs(balance)} MWh"
        else:
            rec = "HOLD"

        return {
            "surplus_deficit_mwh": balance,
            "recommendation": rec
        }

    # Generate trade orders
    def generate_orders(self, market_position):
        orders = []
        if "Buy" in market_position["recommendation"]:
            orders.append({
                "type": "BUY",
                "volume_mwh": abs(market_position["surplus_deficit_mwh"]),
                "price": round(random.uniform(40, 60), 2),
                "delivery_date": str(datetime.today().date())
            })
        elif "Sell" in market_position["recommendation"]:
            orders.append({
                "type": "SELL",
                "volume_mwh": abs(market_position["surplus_deficit_mwh"]),
                "price": round(random.uniform(50, 70), 2),
                "delivery_date": str(datetime.today().date())
            })
        return orders

    # Risk adjustments based on faults & supply chain
    def risk_adjustments(self, grid_exceptions, supply_chain, field_ops):
        risks = []
        if grid_exceptions:
            risks.append("⚠️ Grid reliability risk detected (possible outage zone).")
        if supply_chain:
            shortages = [p for p in supply_chain if p.get("Expected Shortage", 0) > 0]
            if shortages:
                risks.append(f"⚠️ {len(shortages)} spare part shortages may limit generation capacity.")
        if field_ops:
            delayed = [w for w in field_ops if w.get("status") != "Assigned"]
            if delayed:
                risks.append("⚠️ Field operations delays detected in technician assignments.")
        return risks if risks else ["No major risks identified."]

    # GenAI trading advisory
    def advisory(self, market_position, orders, risks):
        prompt = f"""
You are an energy trading strategist. Based on the following:

Market Position: {market_position}
Orders: {orders}
Risks: {risks}

Provide:
1. Summary of market stance
2. Suggested actions for traders
3. How risks affect trading strategy
4. Clear executive-level recommendation
"""
        try:
            resp = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.4
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ Advisory error: {e}"

    # Main run
    def run(self, assets, grid_exceptions, demand_forecast, renewable_plan, dispatch_plan, supply_chain, field_ops):
        # Step 1: Market position
        market_position = self.calculate_position(demand_forecast, dispatch_plan)

        # Step 2: Trade orders
        orders = self.generate_orders(market_position)

        # Step 3: Risks
        risks = self.risk_adjustments(grid_exceptions, supply_chain, field_ops)

        # Step 4: GenAI summary
        summary = self.advisory(market_position, orders, risks)

        return {
            "agent": "energy_trading",
            "market_position": market_position,
            "buy_sell_orders": orders,
            "risk_adjustments": risks,
            "genai_advisory": summary
        }
