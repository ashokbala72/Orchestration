import streamlit as st
import pandas as pd
import json
import os
from orchestrator import OrchestratorAgent
from openai import AzureOpenAI

# ----------------------
# Setup
# ----------------------
st.set_page_config(page_title="Utility Orchestrator", layout="wide")
st.title("⚡ Utility Orchestrator – Multi-Agent Results")

st.sidebar.header("Controls")

# Azure OpenAI Client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# ---------- Helper: GenAI Recommendation ----------
def get_genai_recommendation(tab_name, output):
    """Generate a GenAI recommendation for a given tab and output."""
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

# ---------- Helper: Output Renderer ----------
def render_output(tab_name, output):
    # Asset Integrity with RAG backgrounds
    if tab_name == "Asset Integrity" and isinstance(output, list):
        df = pd.DataFrame(output)

        def color_row(row):
            if "Immediate" in str(row.get("status", "")):
                return ['background-color: red'] * len(row)
            elif "Medium" in str(row.get("status", "")):
                return ['background-color: orange'] * len(row)
            elif "Long" in str(row.get("status", "")):
                return ['background-color: lightgreen'] * len(row)
            else:
                return [''] * len(row)

        styled_df = df.style.apply(color_row, axis=1)
        st.dataframe(styled_df, use_container_width=True)

    # Dict outputs → table + chart
    elif isinstance(output, dict):
        df = pd.DataFrame(list(output.items()), columns=["Metric", "Value"])
        st.table(df)

        numeric_df = df[pd.to_numeric(df["Value"], errors="coerce").notnull()]
        if not numeric_df.empty:
            st.bar_chart(numeric_df.set_index("Metric"))

    # List of dicts → dataframe + optional line chart
    elif isinstance(output, list) and all(isinstance(i, dict) for i in output):
        df = pd.DataFrame(output)
        st.dataframe(df, use_container_width=True)

        time_cols = [c for c in df.columns if "time" in c.lower() or "date" in c.lower()]
        if time_cols:
            try:
                st.line_chart(df.set_index(time_cols[0]))
            except Exception:
                pass

    else:
        st.write(output)

    # Add GenAI Recommendation below the table/chart
    st.markdown("### 🤖 GenAI Recommendation")
    recommendation = get_genai_recommendation(tab_name, output)
    st.write(recommendation)


# ----------------------
# Orchestrator Execution
# ----------------------
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
            st.subheader(f"{tab_labels[idx]} Output")
            render_output(tab_labels[idx], output)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
