import streamlit as st
import pandas as pd
import altair as alt
from orchestrator import OrchestratorAgent

st.set_page_config(page_title="Utility Orchestrator", layout="wide")
st.title("⚡ Utility Orchestrator – Multi-Agent Results")

# ----------------------
# Helper Functions
# ----------------------
def rag_highlight(val):
    """RAG highlight for numeric values (asset ageing)."""
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

def render_styled_table(df, rag_column=None):
    """Render styled DataFrame with optional RAG column."""
    if rag_column and rag_column in df.columns:
        styled = df.style.applymap(rag_highlight, subset=[rag_column])
        st.write(styled.to_html(), unsafe_allow_html=True)
    else:
        st.dataframe(df)

def show_recommendations(output):
    """Show GenAI recommendations if present."""
    if isinstance(output, dict):
        for key in ["recommendations", "advisory", "summary"]:
            if key in output and output[key]:
                st.subheader("🤖 GenAI Recommendations")
                if isinstance(output[key], list):
                    for rec in output[key]:
                        st.markdown(f"- {rec}")
                else:
                    st.markdown(output[key])

# ----------------------
# Main
# ----------------------
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

            # ----- Asset Integrity -----
            if tab_labels[idx] == "Asset Integrity" and isinstance(output, list):
                df = pd.DataFrame(output)
                st.subheader("📋 Asset Register")
                render_styled_table(df, rag_column="age")
                show_recommendations({"recommendations": [a.get("recommendation", "") for a in output if "recommendation" in a]})

            # ----- Grid Faults -----
            elif tab_labels[idx] == "Grid Faults":
                if isinstance(output, list):
                    st.dataframe(pd.DataFrame(output))
                show_recommendations(output)

            # ----- Demand Forecast -----
            elif tab_labels[idx] == "Demand Forecast" and isinstance(output, dict):
                if "forecast" in output:
                    df = pd.DataFrame(output["forecast"])
                    if not df.empty:
                        st.subheader("📈 Forecast Chart")
                        chart = alt.Chart(df).mark_line(point=True).encode(
                            x=df.columns[0], y=df.columns[1], tooltip=list(df.columns)
                        ).interactive()
                        st.altair_chart(chart, use_container_width=True)
                        st.dataframe(df)
                show_recommendations(output)

            # ----- Renewable Integration -----
            elif tab_labels[idx] == "Renewable Integration" and isinstance(output, dict):
                if "integration_plan" in output:
                    st.subheader("🔋 Renewable Integration Plan")
                    st.dataframe(pd.DataFrame(output["integration_plan"]))
                show_recommendations(output)

            # ----- Utility Energy Management -----
            elif tab_labels[idx] == "Utility Energy Management" and isinstance(output, dict):
                if "dispatch_plan" in output:
                    df = pd.DataFrame(output["dispatch_plan"])
                    st.subheader("⚡ Dispatch Plan")
                    chart = alt.Chart(df).mark_bar().encode(
                        x=df.columns[0], y=df.columns[1], tooltip=list(df.columns)
                    )
                    st.altair_chart(chart, use_container_width=True)
                    st.dataframe(df)
                show_recommendations(output)

            # ----- Supply Chain -----
            elif tab_labels[idx] == "Supply Chain Optimization" and isinstance(output, dict):
                if "parts_forecast" in output:
                    st.subheader("📦 Parts Forecast")
                    st.dataframe(pd.DataFrame(output["parts_forecast"]))
                show_recommendations(output)

            # ----- Field Operations -----
            elif tab_labels[idx] == "Field Operations" and isinstance(output, dict):
                if "work_orders" in output:
                    st.subheader("🛠 Work Orders")
                    st.dataframe(pd.DataFrame(output["work_orders"]))
                show_recommendations(output)

            # ----- Energy Trading -----
            elif tab_labels[idx] == "Energy Trading" and isinstance(output, dict):
                if "buy_sell_orders" in output and output["buy_sell_orders"]:
                    st.subheader("📊 Buy/Sell Orders")
                    st.dataframe(pd.DataFrame(output["buy_sell_orders"]))
                if "market_position" in output:
                    st.subheader("⚖ Market Position")
                    st.write(output["market_position"])
                if "risk_adjustments" in output:
                    st.subheader("⚠️ Risks")
                    for r in output["risk_adjustments"]:
                        st.markdown(f"- {r}")
                show_recommendations(output)

            # ----- Fallback -----
            else:
                st.json(output)

else:
    st.info("Click **▶ Run Orchestrator** in the sidebar to execute all 8 agents.")
