# 4_Comparison_Summary.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(layout="centered")
st.title("📊 Player Comparison - Counterpressing Summary")

# === Paths ===
DATA_FOLDER = r"C:\Users\guz_m\OneDrive\Escritorio\Guz\Twelve\Project 3\RealMadrid\RealMadrid"
CSV_PATH = os.path.join(DATA_FOLDER, "csv", "counterpress_analysis_all.csv")

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

df = load_data()

# === Métricas agregadas por jugador ===
agg_data = df.groupby("player_tracked").agg(
    Total_Losses=("player_near_loss", "sum"),
    Participated=("player_involved_in_counterpress", "sum"),
    Recovery_With_Participation=("recovered_in_5s", lambda x: x[df["player_involved_in_counterpress"]].mean()),
    Recovery_Without_Participation=("recovered_in_5s", lambda x: x[~df["player_involved_in_counterpress"]].mean()),
    Avg_Recovery_Time_With_Participation=("recovery_time", lambda x: x[df["player_involved_in_counterpress"] & df["recovered_in_5s"]].mean()),
    Avg_Recovery_Time_Without_Participation=("recovery_time", lambda x: x[~df["player_involved_in_counterpress"] & df["recovered_in_5s"]].mean()),
).round(2)

st.subheader("📋 Summary Table")
st.dataframe(agg_data)

# === Gráfico: tasa de participación y efectividad de recuperación ===
st.subheader("📊 Participation & Recovery Effectiveness")

plot_df = agg_data[["Recovery_With_Participation", "Recovery_Without_Participation"]].reset_index()
plot_df = plot_df.rename(columns={
    "player_tracked": "Player",
    "Recovery_With_Participation": "Recovery Rate (With)",
    "Recovery_Without_Participation": "Recovery Rate (Without)"
})

fig, ax = plt.subplots(figsize=(7, 4))
plot_df.plot(x="Player", kind="bar", ax=ax,
             color=["#27ae60", "#c0392b"],
             rot=0)
ax.set_ylabel("Rate")
ax.set_ylim(0, 1)
ax.set_title("Participation & Recovery Effectiveness", fontsize=12)
ax.legend(fontsize=8, title="", loc="upper right")

for container in ax.containers:
    for bar in container:
        height = bar.get_height()
        ax.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7)

st.pyplot(fig)

# === Tactical Insights ===

insights = '''
🧠 **Tactical Insights: Counterpressing Behavior**

Based on 2023–24 event and freeze-frame data for Real Madrid forwards, we observe the following:

1. **Recovery Effectiveness When Involved**  
   When involved, **Mbappé** shows a higher success rate (**36%**) than Rodrygo and Vinicius Jr (both **24%**),  
   though all remain below the ~52% recovery rate when not involved.

2. **Recovery Time Differences**  
   Fastest when involved: Mbappé (**2.10s**), Rodrygo (**2.32s**), Vinicius Jr (**2.71s**).  
   Team-wide average when not involved is consistently **2.82s**.

3. **Implication**  
   The team’s counterpressing structure appears more effective without direct striker involvement,  
   suggesting a tactical focus on rest-defense roles or deeper recovery units.
'''

st.markdown(insights)
