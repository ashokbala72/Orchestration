import streamlit as st
import pandas as pd
import json
import os
import pprint
from orchestrator import OrchestratorAgent
from dotenv import load_dotenv
from openai import AzureOpenAI

# ----------------------
# Azure OpenAI Setup
# ----------------------
load_dotenv()
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def genai_advisory(prompt: str):
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a utility operations advisor."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ GenAI Error: {e}"

# ----------------------
# Table Coloring Logic (RUL-driven)
# ----------------------
def color_rag(row):
    if "RUL (months)" in row:
        if row["RUL (months)"] <= 3:
            return ['background-color: red'] * len(row)
        elif row["RUL (months)"] <= 6:
            return ['background-color: yellow'] * len(row)
    return ['background-color: lightgreen'] * len(row)

# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(page_title="Utility Orchestrator", layout="wide")
st.title("⚡ Utility Orchestrator – Multi-Agent Dashboard")

st.sidebar.header("Controls")
if st.sidebar.button("▶ Run Orchestrator"):
    orch = OrchestratorAgent()
    results = orch.run()

    # Explicit mapping to orchestrator keys
    tab_mapping = {
        "Asset Integrity": "AssetIntegrity",
        "Grid Faults": "GridFaults",
        "Demand Forecast": "DemandForecast",
        "Renewable Integration": "RenewableIntegration",
        "Utility Energy Management": "UtilityEnergyManagement",
        "Supply Chain Optimization": "SupplyChainOptimization",
        "Field Operations": "FieldOperations",
        "Energy Trading": "EnergyTrading"
    }

    tabs = st.tabs(list(tab_mapping.keys()))

    for idx, (label, agent_key) in enumerate(tab_mapping.items()):
        with tabs[idx]:
            st.subheader(f"{label} Results")

            output = results.get(agent_key, {})
            if not output:
                st.warning("⚠️ No data returned from this agent.")
                continue

            df = None

            # --- Custom handling per agent ---
            if label == "Asset Integrity":
                df = pd.DataFrame(output) if isinstance(output, list) else pd.json_normalize(output)
                styled_df = df.style.apply(color_rag, axis=1)
                st.dataframe(styled_df, use_container_width=True, height=300)

            elif label == "Grid Faults":
                df = pd.DataFrame(output) if isinstance(output, list) else pd.json_normalize(output)
                st.dataframe(df, use_container_width=True, height=300)

            elif label == "Demand Forecast":
                if isinstance(output, dict) and "forecast" in output:
                    df = pd.DataFrame(output["forecast"])
                    st.dataframe(df, use_container_width=True, height=300)
                    if "summary" in output:
                        st.markdown(f"**Agent Summary:** {output['summary']}")
                else:
                    st.json(output)

            elif label == "Renewable Integration":
                if isinstance(output, dict) and "integration_plan" in output:
                    df = pd.DataFrame(output["integration_plan"])
                    st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.json(output)

            elif label == "Utility Energy Management":
                if isinstance(output, dict) and "dispatch_plan" in output:
                    df = pd.DataFrame(output["dispatch_plan"])
                    st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.json(output)

            elif label == "Supply Chain Optimization":
                if isinstance(output, dict) and "parts_forecast" in output:
                    df = pd.DataFrame(output["parts_forecast"])
                    st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.json(output)

            elif label == "Field Operations":
                if isinstance(output, dict) and "work_orders" in output:
                    df = pd.DataFrame(output["work_orders"])
                    st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.json(output)

            elif label == "Energy Trading":
                if isinstance(output, dict):
                    if "market_position" in output:
                        st.json(output["market_position"])
                    if "buy_sell_orders" in output:
                        df = pd.DataFrame(output["buy_sell_orders"])
                        st.dataframe(df, use_container_width=True, height=300)
                else:
                    st.json(output)

            # --- GenAI Recommendation ---
            try:
                safe_output = json.dumps(output, indent=2, default=str)
            except Exception:
                safe_output = pprint.pformat(output, indent=2)

            prompt = f"Summarize insights and give a recommendation for the following {label} results:\n{safe_output}"
            with st.spinner("Generating GenAI recommendation..."):
                advisory = genai_advisory(prompt)
                st.markdown("### 🤖 GenAI Recommendation")
                st.info(advisory)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
