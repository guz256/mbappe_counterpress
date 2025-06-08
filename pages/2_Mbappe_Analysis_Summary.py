# 2_Mbappe_Analysis_Summary.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from mplsoccer import Pitch
import os
import json

st.set_page_config(layout="centered")
st.title("📊 Mbappé - Counterpress Summary")

# === Paths ===
DATA_FOLDER = r"C:\Users\guz_m\OneDrive\Escritorio\Guz\Twelve\Project 3\RealMadrid\RealMadrid"
CSV_PATH = os.path.join(DATA_FOLDER, "csv", "counterpress_analysis_all.csv")
META_PATH = os.path.join(DATA_FOLDER, "meta", "1712797.json")  # usás 1 como referencia

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
df = df[df["player_tracked"] == "Mbappé"]

# === KPI cards ===
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("🔄 Total losses", len(df))
with col2: st.metric("🎯 Mbappé near", df["player_near_loss"].sum())
with col3: st.metric("🔁 Mbappé involved", df["player_involved_in_counterpress"].sum())
with col4: st.metric("✅ Recovered <5s", df["recovered_in_5s"].sum())

# === Combinations summary ===
combo_data = {
    "Mbappé involved + Recovered": len(df[(df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]),
    "Mbappé involved + Not recovered": len(df[(df["player_involved_in_counterpress"]) & (~df["recovered_in_5s"])]),
    "Mbappé near + Recovered": len(df[(df["player_near_loss"]) & (df["recovered_in_5s"])]),
    "Mbappé near + Not recovered": len(df[(df["player_near_loss"]) & (~df["recovered_in_5s"])]),
}
combo_df = pd.DataFrame.from_dict(combo_data, orient="index", columns=["Count"])

st.subheader("🧮 Recovery Outcomes by Mbappé's Role")
st.dataframe(combo_df)

# === Recovery time averages ===
with_mbappe = df[(df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]
without_mbappe = df[(~df["player_involved_in_counterpress"]) & (df["recovered_in_5s"])]

avg_with = with_mbappe["recovery_time"].mean()
avg_without = without_mbappe["recovery_time"].mean()

st.subheader("⏱️ Average Recovery Time (<5s)")
st.write(f"**Mbappé involved:** {avg_with:.2f} sec")
st.write(f"**Mbappé NOT involved:** {avg_without:.2f} sec")

# === Barchart ===
st.subheader("📊 Recovery Rate")

rate_df = pd.DataFrame({
    "Category": ["Mbappé Involved", "Mbappé Not Involved"],
    "Rate": [
        df[df["player_involved_in_counterpress"]]["recovered_in_5s"].mean(),
        df[~df["player_involved_in_counterpress"]]["recovered_in_5s"].mean()
    ]
})


fig, ax = plt.subplots(figsize=(4.5, 2.5))
sns.barplot(data=rate_df, x="Category", y="Rate",
            palette=["#4B7BEC", "#ec4b7b"], ax=ax)

# Reduce label font sizes
ax.tick_params(axis='x', labelsize=6)
ax.set_yticks([])  # Elimina las marcas del eje Y
ax.set_xlabel("")
ax.set_ylabel("")
ax.set_ylim(0, 1)

# Annotate bars
for i, row in rate_df.iterrows():
    offset = 0.02 if row["Rate"] < 0.95 else -0.05
    color = "black" if row["Rate"] < 0.95 else "white"
    ax.text(i, row["Rate"] + offset, f"{row['Rate']:.0%}", ha="center", fontsize=6, weight="bold", color=color)


# Explanatory note
ax.text(0.5, -0.25,
        "Note: Mbappé participated in only 3.6% of total losses. Total recovery rate is driven by non-involved actions.",
        ha="center", fontsize=6, transform=ax.transAxes)

st.pyplot(fig)

# === Heatmaps ===
st.subheader("📍 Heatmaps of Ball Losses")

df_involved = df[df["player_involved_in_counterpress"]]
df_not_involved = df[~df["player_involved_in_counterpress"]]

pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
              pitch_color='white', line_color='black')

fig1, ax1 = pitch.draw(figsize=(5, 3))
pitch.heatmap(
    pitch.bin_statistic(df_involved["x_loss"], df_involved["y_loss"], bins=(30, 20)), 
    ax=ax1, cmap="Reds", zorder=0)
ax1.set_title("Mbappé Involved", fontsize=9)
st.pyplot(fig1)


# === Recovery plots ===
st.subheader("🟢 Recovery Locations")

df_recovered = df[df["recovered_in_5s"]]
rec_with = df_recovered[df_recovered["player_involved_in_counterpress"]]
rec_without = df_recovered[~df_recovered["player_involved_in_counterpress"]]

fig3, ax3 = pitch.draw(figsize=(5, 3))
pitch.scatter(rec_with["x_loss"], rec_with["y_loss"], ax=ax3, color="#27ae60", s=30, alpha=0.7)
ax3.set_title("Recovered - With Mbappé", fontsize=9)
st.pyplot(fig3)

df["third_start_clean"] = df["third_start"].map({
    "defensive_third": "Defensive Third",
    "middle_third": "Middle Third",
    "attacking_third": "Attacking Third"
})

st.subheader("📊 Recovery by Field Third (when Mbappé was Nearby)")

# Filtrar acciones donde Mbappé estaba cerca de la pérdida
df_near = df[df["player_near_loss"] == True].copy()


# Mapear nombres legibles
df_near["third_start_clean"] = df_near["third_start"].map({
    "defensive_third": "Defensive Third",
    "middle_third": "Middle Third",
    "attacking_third": "Attacking Third"
})
df_near["Mbappé Involved in Counterpress"] = df_near["player_involved_in_counterpress"].map({
    True: "Mbappé Involved", False: "Not Involved"
})

# Tabla de conteo absoluto por tercio
tabla_tercios = (
    df_near.groupby(["third_start_clean", "Mbappé Involved in Counterpress", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
)

st.dataframe(tabla_tercios)

# Gráfico de efectividad
efectividad_tercio = (
    tabla_tercios["Recovered"] / (tabla_tercios["Recovered"] + tabla_tercios["Not Recovered"])
).unstack()

fig, ax = plt.subplots(figsize=(5.5, 3))
efectividad_tercio.plot(kind="bar", ax=ax, color=["#4B7BEC", "#ec4b7b"])

ax.set_ylabel("Recovery Rate")
ax.set_xlabel("Third")
ax.set_title("Recovery Rate by Field Third (Mbappé Nearby)", fontsize=10)
ax.set_ylim(0, 1)
ax.tick_params(axis='x', rotation=15, labelsize=8)
ax.tick_params(axis='y', labelsize=8)

# Etiquetas de porcentaje
for container in ax.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f"{height:.0%}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha='center', va='bottom', fontsize=7)

# Leyenda más chica y colocada afuera
ax.legend(title="Mbappé", title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))

st.pyplot(fig)

st.subheader("📊 Recovery by Channel (when Mbappé was Nearby)")

# Mapear nombres legibles de carriles
df_near["channel_start_clean"] = df_near["channel_start"].map({
    "wide_left": "Wide Left",
    "half_space_left": "Half-Space Left",
    "center": "Center",
    "half_space_right": "Half-Space Right",
    "wide_right": "Wide Right"
})
df_near["Mbappé Involved in Counterpress"] = df_near["player_involved_in_counterpress"].map({
    True: "Mbappé Involved", False: "Not Involved"
})

# Definir orden lógico izquierda → derecha
channel_order = ["Wide Left", "Half-Space Left", "Center", "Half-Space Right", "Wide Right"]

# Agrupación y tabla
tabla_channel = (
    df_near.groupby(["channel_start_clean", "Mbappé Involved in Counterpress", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
).reindex(channel_order, level=0)

st.dataframe(tabla_channel)

# Calcular efectividad por canal
efectividad_channel = (
    tabla_channel["Recovered"] / (tabla_channel["Recovered"] + tabla_channel["Not Recovered"])
).unstack()

# Gráfico
fig_ch, ax_ch = plt.subplots(figsize=(6, 3))
efectividad_channel.loc[channel_order].plot(kind="bar", ax=ax_ch, color=["#4B7BEC", "#ec4b7b"])
ax_ch.set_ylabel("Recovery Rate")
ax_ch.set_title("Recovery Rate by Channel (Mbappé Nearby)", fontsize=10)
ax_ch.set_ylim(0, 1)
ax_ch.tick_params(axis='x', rotation=15, labelsize=8)
ax_ch.tick_params(axis='y', labelsize=8)
ax_ch.legend(title="Mbappé", title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))

# Etiquetas
for container in ax_ch.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax_ch.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=7)

st.pyplot(fig_ch)


st.subheader("📊 Recovery by Game State (when Mbappé was Nearby)")

tabla_game_state = (
    df_near.groupby(["game_state", "Mbappé Involved in Counterpress", "recovered_in_5s"])
    .size()
    .unstack(fill_value=0)
    .rename(columns={True: "Recovered", False: "Not Recovered"})
)
st.dataframe(tabla_game_state)

efectividad_game_state = (
    tabla_game_state["Recovered"] / (tabla_game_state["Recovered"] + tabla_game_state["Not Recovered"])
).unstack()

fig_gs, ax_gs = plt.subplots(figsize=(5.5, 3))
efectividad_game_state.plot(kind="bar", ax=ax_gs, color=["#4B7BEC", "#ec4b7b"])
ax_gs.set_ylabel("Recovery Rate")
ax_gs.set_title("Recovery Rate by Game State (Mbappé Nearby)", fontsize=10)
ax_gs.set_ylim(0, 1)
ax_gs.tick_params(axis='x', rotation=15, labelsize=8)
ax_gs.tick_params(axis='y', labelsize=8)
ax_gs.legend(title="Mbappé", title_fontsize=8, fontsize=7, loc='upper left', bbox_to_anchor=(1, 1))
for container in ax_gs.containers:
    for bar in container:
        height = bar.get_height()
        if height > 0:
            ax_gs.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3), textcoords="offset points",
                           ha='center', va='bottom', fontsize=7)

st.pyplot(fig_gs)
