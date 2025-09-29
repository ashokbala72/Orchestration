import streamlit as st
import json
from orchestrator import OrchestratorAgent  # your orchestrator file

# ----------------------
# UI Setup
# ----------------------
st.set_page_config(page_title="Utility Orchestrator", layout="wide")
st.title("⚡ Utility Orchestrator – Multi-Agent Results")

st.sidebar.header("Controls")
if st.sidebar.button("▶ Run Orchestrator"):
    orch = OrchestratorAgent()
    results = orch.run()

    # Define tab labels
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

    # Create tabs
    tabs = st.tabs(tab_labels)

    # Loop over results and display JSON in corresponding tab
    for idx, (agent_name, output) in enumerate(results.items()):
        with tabs[idx]:
            st.subheader(f"{tab_labels[idx]} Output")
            st.json(output)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
