# 2_Comparison_Analysis_Summary_v2.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mplsoccer import Pitch
import os
import json

st.set_page_config(layout="centered")
st.title("📊 Counterpress Summary - Player Comparison")

# === Paths ===
DATA_FOLDER = r"C:\Users\guz_m\OneDrive\Escritorio\Guz\Twelve\Project 3\RealMadrid\RealMadrid"
CSV_PATH = os.path.join(DATA_FOLDER, "csv", "counterpress_analysis_all.csv")
META_PATH = os.path.join(DATA_FOLDER, "meta", "1712797.json")

# === Load pitch dimensions from meta ===
with open(META_PATH, "r", encoding="utf-8") as f:
    meta = json.load(f)
pitch_length = meta["pitch_length"]
pitch_width = meta["pitch_width"]

# === Load data ===
@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

df = load_data()

# === Sidebar filter ===
player_names = df["player_tracked"].unique().tolist()
selected_player = st.sidebar.selectbox("Select player to analyze:", player_names)
df = df[df["player_tracked"] == selected_player]

# === Mappings for labels ===
df["third_start_clean"] = df["third_start"].map({
    "defensive_third": "Defensive Third",
    "middle_third": "Middle Third",
    "attacking_third": "Attacking Third"
})
df["channel_start_clean"] = df["channel_start"].map({
    "wide_left": "Wide Left",
    "half_space_left": "Half-Space Left",
    "center": "Center",
    "half_space_right": "Half-Space Right",
    "wide_right": "Wide Right"
})
df["Involvement"] = df["player_involved_in_counterpress"].map({True: "Involved", False: "Not Involved"})

# === KPI cards ===
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("🔄 Total losses", len(df))
with col2: st.metric(f"🎯 {selected_player} near", df["player_near_loss"].sum())
with col3: st.metric(f"🚀 {selected_player} involved", df["player_involved_in_counterpress"].sum())
with col4: st.metric("✅ Recovered <5s", df["recovered_in_5s"].sum())

# === Recovery outcome table ===
combo_data = {
    f"{selected_player} involved + Recovered": len(df[(df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]),
    f"{selected_player} involved + Not recovered": len(df[(df["player_involved_in_counterpress"]) & (~df["recovered_in_5s"])]),
    f"{selected_player} near + Recovered": len(df[(df["player_near_loss"]) & (df["recovered_in_5s"])]),
    f"{selected_player} near + Not recovered": len(df[(df["player_near_loss"]) & (~df["recovered_in_5s"])]),
}
st.subheader(f"🧮 Recovery Outcomes by {selected_player}'s Role")
st.dataframe(pd.DataFrame.from_dict(combo_data, orient="index", columns=["Count"]))

# === Recovery time averages ===
with_player = df[(df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]
without_player = df[(~df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]
st.subheader("⏱️ Average Recovery Time (<5s)")
st.write(f"**{selected_player} involved:** {with_player['recovery_time'].mean():.2f} sec")
st.write(f"**{selected_player} NOT involved:** {without_player['recovery_time'].mean():.2f} sec")

# === Recovery rate barplot ===
st.subheader("📊 Recovery Rate")
rate_df = pd.DataFrame({
    "Category": [f"{selected_player} Involved", f"{selected_player} Not Involved"],
    "Rate": [
        df[df["player_involved_in_counterpress"]]["recovered_in_5s"].mean(),
        df[~df["player_involved_in_counterpress"]]["recovered_in_5s"].mean()
    ]
})
fig, ax = plt.subplots(figsize=(4.5, 2.5))
sns.barplot(data=rate_df, x="Category", y="Rate", palette=["#4B7BEC", "#ec4b7b"], ax=ax)
ax.set_ylim(0, 1)
for i, row in rate_df.iterrows():
    ax.text(i, row["Rate"] + 0.03, f"{row['Rate']:.0%}", ha="center", fontsize=8)
st.pyplot(fig)

# === Heatmap: losses where involved ===
st.subheader(f"📍 Heatmap of Ball Losses ({selected_player} Involved)")
pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width, pitch_color='white', line_color='black')
df_involved = df[df["player_involved_in_counterpress"]]
fig1, ax1 = pitch.draw(figsize=(5, 3))
pitch.heatmap(pitch.bin_statistic(df_involved["x_loss"], df_involved["y_loss"], bins=(30, 20)), ax=ax1, cmap="Reds", zorder=0)
st.pyplot(fig1)

# === Scatter maps of recoveries ===
st.subheader("🟢 Recovery Locations (<5s)")
df_rec = df[df["recovered_in_5s"]]
rec_with = df_rec[df_rec["player_involved_in_counterpress"]]
rec_without = df_rec[~df_rec["player_involved_in_counterpress"]]

fig2, ax2 = pitch.draw(figsize=(5, 3))
pitch.scatter(rec_with["x_loss"], rec_with["y_loss"], ax=ax2, color="#27ae60", s=30, alpha=0.7)
ax2.set_title(f"Recovered - With {selected_player}", fontsize=9)
st.pyplot(fig2)

st.subheader(f"📊 Recovery Effectiveness when {selected_player} was Nearby")

# Filtrar dataset
df_near = df[df["player_near_loss"] == True].copy()

# Mapear columnas legibles
df_near["third_start_clean"] = df_near["third_start"].map({
    "defensive_third": "Defensive Third",
    "middle_third": "Middle Third",
    "attacking_third": "Attacking Third"
})
df_near["channel_start_clean"] = df_near["channel_start"].map({
    "wide_left": "Wide Left",
    "half_space_left": "Half-Space Left",
    "center": "Center",
    "half_space_right": "Half-Space Right",
    "wide_right": "Wide Right"
})
df_near["Player Involved"] = df_near["player_involved_in_counterpress"].map({
    True: f"{selected_player} Involved",
    False: "Not Involved"
})

st.subheader(f"📊 Recovery Rate by Field Third ({selected_player} Nearby)")

tabla_tercios = (
    df_near.groupby(["third_start_clean", "Player Involved", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
)

efectividad_tercio = (
    tabla_tercios["Recovered"] / (tabla_tercios["Recovered"] + tabla_tercios["Not Recovered"])
).unstack()

# Reordenar columnas
involved_label = f"{selected_player} Involved"
column_order = ["Not Involved", involved_label] if involved_label in efectividad_tercio.columns else efectividad_tercio.columns
tercio_order = ["Defensive Third", "Middle Third", "Attacking Third"]
efectividad_tercio = efectividad_tercio.reindex(tercio_order)

fig, ax = plt.subplots(figsize=(5.5, 3))
efectividad_tercio.plot(kind="bar", ax=ax, color=["#4B7BEC", "#ec4b7b"])
ax.set_ylabel("Recovery Rate")
ax.set_xlabel("Third")
ax.set_title(f"Recovery Rate by Field Third ({selected_player} Nearby)", fontsize=10)
ax.set_ylim(0, 1)
ax.tick_params(axis='x', rotation=15, labelsize=8)
ax.legend(title=selected_player, title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))
for container in ax.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=7)
st.pyplot(fig)

st.subheader(f"📊 Recovery Rate by Channel ({selected_player} Nearby)")

channel_order = ["Wide Left", "Half-Space Left", "Center", "Half-Space Right", "Wide Right"]

tabla_channel = (
    df_near.groupby(["channel_start_clean", "Player Involved", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
).reindex(channel_order, level=0)

efectividad_channel = (
    tabla_channel["Recovered"] / (tabla_channel["Recovered"] + tabla_channel["Not Recovered"])
).unstack()

# Reordenar columnas
efectividad_channel = efectividad_channel[column_order]

fig_ch, ax_ch = plt.subplots(figsize=(6, 3))
efectividad_channel.loc[channel_order].plot(kind="bar", ax=ax_ch, color=["#4B7BEC", "#ec4b7b"])
ax_ch.set_ylabel("Recovery Rate")
ax_ch.set_title(f"Recovery Rate by Channel ({selected_player} Nearby)", fontsize=10)
ax_ch.set_ylim(0, 1)
ax_ch.tick_params(axis='x', rotation=15, labelsize=8)
ax_ch.legend(title=selected_player, title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))
for container in ax_ch.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax_ch.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=7)
st.pyplot(fig_ch)

st.subheader(f"📊 Recovery Rate by Game State ({selected_player} Nearby)")

tabla_game_state = (
    df_near.groupby(["game_state", "Player Involved", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
)

efectividad_game_state = (
    tabla_game_state["Recovered"] / (tabla_game_state["Recovered"] + tabla_game_state["Not Recovered"])
).unstack()

# Ordenar columnas (color) y eje X
involved_label = f"{selected_player} Involved"
column_order = ["Not Involved", involved_label] if involved_label in efectividad_game_state.columns else efectividad_game_state.columns
game_state_order = ["losing", "drawing", "winning"]
efectividad_game_state = efectividad_game_state[column_order].reindex(game_state_order)

# Gráfico
fig_gs, ax_gs = plt.subplots(figsize=(5.5, 3))
efectividad_game_state.plot(kind="bar", ax=ax_gs, color=["#4B7BEC", "#ec4b7b"])
ax_gs.set_ylabel("Recovery Rate")
ax_gs.set_title(f"Recovery Rate by Game State ({selected_player} Nearby)", fontsize=10)
ax_gs.set_ylim(0, 1)
ax_gs.tick_params(axis='x', rotation=15, labelsize=8)
ax_gs.tick_params(axis='y', labelsize=8)
ax_gs.legend(title=selected_player, title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))

for container in ax_gs.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax_gs.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=7)

st.pyplot(fig_gs)
