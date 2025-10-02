import streamlit as st
import pandas as pd
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

    # Loop over results and display output
    for idx, (agent_name, output) in enumerate(results.items()):
        with tabs[idx]:
            st.subheader(f"{tab_labels[idx]} Output")

            # -------------------------
            # Asset Integrity → RAG table
            # -------------------------
            if agent_name == "Asset Integrity":
                if "assets" in output:
                    df = pd.DataFrame(output["assets"])

                    # Color styling
                    def color_rag(val):
                        if str(val).lower() == "red":
                            return "background-color: #ff4d4d; color: white"
                        elif str(val).lower() == "amber":
                            return "background-color: #ffbf00; color: black"
                        elif str(val).lower() == "green":
                            return "background-color: #70db70; color: black"
                        return ""

                    st.dataframe(df.style.applymap(color_rag, subset=["status"]))
                else:
                    st.json(output)

            # -------------------------
            # Other tabs → JSON output
            # -------------------------
            else:
                st.json(output)

            # -------------------------
            # GenAI Recommendation
            # -------------------------
            if "recommendation" in output:
                st.markdown("### 🤖 GenAI Recommendation")
                st.write(output["recommendation"])

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
