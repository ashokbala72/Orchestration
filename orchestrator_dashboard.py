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
# Table Coloring Logic
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

    tab_labels = [
        "Asset Integrity",
        "Grid Faults",
        "Demand Forecast",
        "Renewable Integration",
        "Utility Energy Management",
        "Supply Chain Optimization",
        "Field Operations",
        "Energy Trading"
    ]
    tabs = st.tabs(tab_labels)

    for idx, (agent_name, output) in enumerate(results.items()):
        with tabs[idx]:
            st.subheader(f"{tab_labels[idx]} Results")

            # Convert JSON to DataFrame if possible
            try:
                if isinstance(output, dict):
                    df = pd.json_normalize(output)
                elif isinstance(output, list):
                    df = pd.DataFrame(output)
                else:
                    df = pd.DataFrame([{"Result": str(output)}])

                # Apply RAG coloring only if RUL present
                if "RUL (months)" in df.columns:
                    styled_df = df.style.apply(color_rag, axis=1)
                    st.dataframe(styled_df, use_container_width=True, height=300)
                else:
                    st.dataframe(df, use_container_width=True, height=300)
            except Exception:
                st.json(output)

            # GenAI Recommendation (safe serialization)
            try:
                safe_output = json.dumps(output, indent=2, default=str)
            except Exception:
                safe_output = pprint.pformat(output, indent=2)

            prompt = (
                f"Summarize insights and give a recommendation for the following "
                f"{tab_labels[idx]} results:\n{safe_output}"
            )
            with st.spinner("Generating GenAI recommendation..."):
                advisory = genai_advisory(prompt)
                st.markdown("### 🤖 GenAI Recommendation")
                st.info(advisory)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
