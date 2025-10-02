import streamlit as st
import pandas as pd
import altair as alt
from orchestrator import OrchestratorAgent

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

    # Helper: show output as table or chart
    def show_output(output, tab_name):
        # Case 1: If it's a list of dicts -> Table
        if isinstance(output, list) and all(isinstance(i, dict) for i in output):
            st.dataframe(pd.DataFrame(output))

        # Case 2: Demand Forecast – plot a line chart
        elif isinstance(output, dict) and "forecast" in output:
            df = pd.DataFrame(output["forecast"])
            if not df.empty:
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x=alt.X(df.columns[0], title="Date"),
                    y=alt.Y(df.columns[1], title="Forecast"),
                    tooltip=list(df.columns)
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.dataframe(df)
            else:
                st.info("No forecast data available.")

        # Case 3: Energy Trading – show buy/sell orders in table
        elif tab_name == "Energy Trading" and isinstance(output, dict):
            if "buy_sell_orders" in output and output["buy_sell_orders"]:
                st.subheader("📊 Buy/Sell Orders")
                st.dataframe(pd.DataFrame(output["buy_sell_orders"]))
            if "market_position" in output:
                st.subheader("⚖ Market Position")
                st.write(output["market_position"])
            if "risk_adjustments" in output:
                st.subheader("⚠️ Risks")
                st.write(output["risk_adjustments"])

        # Case 4: Default fallback
        else:
            st.json(output)

    # Loop over results and display in each tab
    for idx, (agent_name, output) in enumerate(results.items()):
        with tabs[idx]:
            st.subheader(f"{tab_labels[idx]} Results")
            show_output(output, tab_labels[idx])

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
