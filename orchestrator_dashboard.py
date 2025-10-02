import streamlit as st
import pandas as pd
import json
import os
from orchestrator import OrchestratorAgent
from openai import AzureOpenAI

st.set_page_config(page_title="Utility Orchestrator", layout="wide")
st.title("⚡ Utility Orchestrator – Multi-Agent Results")
st.sidebar.header("Controls")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

def get_genai_recommendation(tab_name, output):
    try:
        prompt = f"""
        You are a utility sector advisor. Analyze the following output from {tab_name}
        and give clear recommendations, focusing on risks, actions, and priorities.

        Data:
        {json.dumps(output, indent=2)}
        """
        resp = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant for energy and utilities."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ GenAI recommendation unavailable: {e}"

def render_output(tab_name, output):
    if tab_name == "Asset Integrity" and isinstance(output, list):
        df = pd.DataFrame(output)
        def color_row(row):
            if "RUL (months)" in row:
                if row["RUL (months)"] <= 3:
                    return ['background-color: red'] * len(row)
                elif row["RUL (months)"] <= 6:
                    return ['background-color: yellow'] * len(row)
                else:
                    return ['background-color: lightgreen'] * len(row)
            return [''] * len(row)
        st.markdown("**🟩 Green = Safe | 🟨 Yellow = Nearing Replacement | 🟥 Red = Immediate Replacement Required**")
        styled_df = df.style.apply(color_row, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=500)
    else:
        if isinstance(output, dict):
            df = pd.DataFrame(list(output.items()), columns=["Metric", "Value"])
            st.dataframe(df, use_container_width=True, height=500)
        elif isinstance(output, list) and all(isinstance(i, dict) for i in output):
            df = pd.DataFrame(output)
            st.dataframe(df, use_container_width=True, height=500)
        else:
            st.write(output)

    st.markdown("### 🤖 GenAI Recommendation")
    recommendation = get_genai_recommendation(tab_name, output)
    st.write(recommendation)


# ----------------------
# Orchestrator Execution
# ----------------------
if st.sidebar.button("▶ Run Orchestrator"):
    orch = OrchestratorAgent()
    results = orch.run()  # <-- dict of agent outputs

    # Map expected tab names to orchestrator keys
    mapping = {
        "Asset Integrity": "asset_integrity",
        "Grid Faults": "grid_faults",
        "Demand Forecast": "demand_forecast",
        "Renewable Integration": "renewable_integration",
        "Utility Energy Management": "utility_energy_mgmt",
        "Supply Chain Optimization": "supply_chain_optimization",
        "Field Operations": "field_operations",
        "Energy Trading": "energy_trading"
    }

    tabs = st.tabs(list(mapping.keys()))

    # Render each tab using the correct agent output
    for idx, (tab_name, agent_key) in enumerate(mapping.items()):
        with tabs[idx]:
            st.subheader(f"{tab_name} Output")
            output = results.get(agent_key, {})
            render_output(tab_name, output)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
