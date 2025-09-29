import os
from dotenv import load_dotenv

# Import all agents
from AssetIntegrityAgent import AssetIntegrityAgent
from GridFaultForecastingAgent import GridFaultForecastingAgent
from DemandForecastingAgent import DemandForecastingAgent
from RenewableIntegrationAgent import RenewableIntegrationAgent
from UtilityEnergyManagementAgent import UtilityEnergyManagementAgent
from SupplyChainOptimizationAgent import SupplyChainOptimizationAgent
from FieldOperationsAgent import FieldOperationsAgent
from EnergyTradingAgent import EnergyTradingAgent

# Load Azure OpenAI credentials
load_dotenv()

class OrchestratorAgent:
    def __init__(self):
        # Instantiate all agents
        self.asset_agent = AssetIntegrityAgent()
        self.grid_agent = GridFaultForecastingAgent()
        self.demand_agent = DemandForecastingAgent()
        self.renewable_agent = RenewableIntegrationAgent()
        self.energy_mgmt_agent = UtilityEnergyManagementAgent()
        self.supply_chain_agent = SupplyChainOptimizationAgent()
        self.field_ops_agent = FieldOperationsAgent()
        self.trading_agent = EnergyTradingAgent()

    def run(self):
        # Step 1: Asset Integrity
        asset_data = self.asset_agent.asset_register()["assets"]

        # Step 2: Grid Fault Forecasting
        grid_exceptions = self.grid_agent.run(asset_data)["detected_exceptions"]

        # Step 3: Demand Forecasting
        demand_results = self.demand_agent.run(
            assets=asset_data, grid_exceptions=grid_exceptions, horizon_days=30
        )
        demand_forecast = demand_results["forecast"]

        # Step 4: Renewable Integration
        renewable_results = self.renewable_agent.run(
            demand_forecast=demand_forecast,
            grid_exceptions=grid_exceptions,
            assets=asset_data
        )
        renewable_plan = renewable_results["integration_plan"]

        # Step 5: Utility Energy Management
        energy_mgmt_results = self.energy_mgmt_agent.run(
            assets=asset_data,
            grid_exceptions=grid_exceptions,
            demand_forecast=demand_forecast,
            renewable_plan=renewable_plan
        )
        dispatch_plan = energy_mgmt_results["dispatch_plan"]

        # Step 6: Supply Chain Optimization
        supply_chain_results = self.supply_chain_agent.run(
            assets=asset_data,
            grid_exceptions=grid_exceptions,
            demand_forecast=demand_forecast,
            renewable_plan=renewable_plan,
            dispatch_plan=dispatch_plan,
            company_type="Integrated Utility"
        )
        supply_chain_plan = supply_chain_results["parts_forecast"]

        # Step 7: Field Operations
        field_ops_results = self.field_ops_agent.run(
            assets=asset_data,
            grid_exceptions=grid_exceptions,
            demand_forecast=demand_forecast,
            renewable_plan=renewable_plan,
            dispatch_plan=dispatch_plan,
            supply_chain=supply_chain_plan
        )

        # Step 8: Energy Trading
        trading_results = self.trading_agent.run(
            assets=asset_data,
            grid_exceptions=grid_exceptions,
            demand_forecast=demand_forecast,
            renewable_plan=renewable_plan,
            dispatch_plan=dispatch_plan,
            supply_chain=supply_chain_plan,
            field_ops=field_ops_results["work_orders"]
        )

        # Final orchestration output
        return {
            "AssetIntegrity": asset_data,
            "GridFaults": grid_exceptions,
            "DemandForecast": demand_results,
            "RenewableIntegration": renewable_results,
            "UtilityEnergyManagement": energy_mgmt_results,
            "SupplyChainOptimization": supply_chain_results,
            "FieldOperations": field_ops_results,
            "EnergyTrading": trading_results
        }

# Example usage
if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    results = orchestrator.run()
    import json
    print(json.dumps(results, indent=2))
