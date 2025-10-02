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

    # -------- Helper Functions --------
    def rag_highlight(val):
        """Highlight RAG for numeric age/condition values."""
        try:
            if isinstance(val, (int, float)):
                if val > 70:
                    return "background-color: red; color: white"
                elif val > 40:
                    return "background-color: orange; color: black"
                else:
                    return "background-color: green; color: white"
        except:
            return ""
        return ""

    def show_output(output, tab_name):
        # ----- Asset Integrity -----
        if tab_name == "Asset Integrity" and isinstance(output, list):
            df = pd.DataFrame(output)
            if "age" in df.columns:
                st.subheader("📋 Asset Register with Ageing Status")
                st.dataframe(df.style.applymap(rag_highlight, subset=["age"]))
            else:
                st.dataframe(df)

        # ----- Grid Faults -----
        elif tab_name == "Grid Faults":
            if isinstance(output, list):
                st.dataframe(pd.DataFrame(output))
            else:
                st.json(output)

        # ----- Demand Forecast -----
        elif tab_name == "Demand Forecast" and isinstance(output, dict) and "forecast" in output:
            df = pd.DataFrame(output["forecast"])
            if not df.empty:
                st.subheader("📈 Forecast Chart")
                chart = alt.Chart(df).mark_line(point=True).encode(
                    x=alt.X(df.columns[0], title="Date"),
                    y=alt.Y(df.columns[1], title="Forecast"),
                    tooltip=list(df.columns)
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.dataframe(df)
            else:
                st.info("No forecast data available.")

        # ----- Renewable Integration -----
        elif tab_name == "Renewable Integration" and isinstance(output, dict) and "integration_plan" in output:
            df = pd.DataFrame(output["integration_plan"])
            st.subheader("🔋 Renewable Integration Plan")
            st.dataframe(df)

        # ----- Utility Energy Management -----
        elif tab_name == "Utility Energy Management" and isinstance(output, dict):
            if "dispatch_plan" in output:
                df = pd.DataFrame(output["dispatch_plan"])
                if not df.empty:
                    st.subheader("⚡ Dispatch Plan")
                    chart = alt.Chart(df).mark_bar().encode(
                        x=df.columns[0],
                        y=df.columns[1],
                        tooltip=list(df.columns)
                    )
                    st.altair_chart(chart, use_container_width=True)
                    st.dataframe(df)
            else:
                st.json(output)

        # ----- Supply Chain Optimization -----
        elif tab_name == "Supply Chain Optimization" and isinstance(output, dict):
            if "parts_forecast" in output:
                df = pd.DataFrame(output["parts_forecast"])
                st.subheader("📦 Parts Forecast")
                st.dataframe(df)
            else:
                st.json(output)

        # ----- Field Operations -----
        elif tab_name == "Field Operations" and isinstance(output, dict):
            if "work_orders" in output:
                df = pd.DataFrame(output["work_orders"])
                st.subheader("🛠 Work Orders")
                st.dataframe(df)
            else:
                st.json(output)

        # ----- Energy Trading -----
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

        # ----- Fallback -----
        else:
            st.json(output)

    # -------- Loop over agents --------
    for idx, (agent_name, output) in enumerate(results.items()):
        with tabs[idx]:
            st.subheader(f"{tab_labels[idx]} Results")
            show_output(output, tab_labels[idx])

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
