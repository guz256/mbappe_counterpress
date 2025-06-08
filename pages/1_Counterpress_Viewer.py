# 1_Counterpress_Viewer_Final.py

import streamlit as st
import pandas as pd
import json
import os
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import io
from PIL import Image

st.set_page_config(layout="wide")
st.title("🔎 Counterpress Analysis Viewer")

# === Configuration ===
DATA_FOLDER = r"C:\Users\guz_m\OneDrive\Escritorio\Guz\Twelve\Project 3\RealMadrid\RealMadrid"
CSV_PATH = os.path.join(DATA_FOLDER, "csv", "counterpress_analysis_all.csv")
FREEZE_FOLDER = os.path.join(DATA_FOLDER, "freeze")
META_FOLDER = os.path.join(DATA_FOLDER, "meta")

@st.cache_data
def load_data():
    return pd.read_csv(CSV_PATH)

df_all = load_data()

# === Sidebar filters ===
# Diccionario fijo de jugadores
player_ids = {
    6028: "Mbappé",
    12253: "Vinicius Jr",
    23903: "Rodrygo"
}
name_to_id = {v: k for k, v in player_ids.items()}

# Select jugador
players = sorted(player_ids.values())
selected_player = st.sidebar.selectbox("Select player:", players)
selected_id = name_to_id[selected_player]

# Filtrar eventos del jugador
df_player = df_all[df_all["player_tracked"] == selected_player]

# === Acción filtrada primero ===
filter_mode = st.sidebar.radio("Filter actions", ["All", "Player near", "Player involved"])

if filter_mode == "Player near":
    df_filtered_events = df_player[df_player["player_near_loss"] == True]
elif filter_mode == "Player involved":
    df_filtered_events = df_player[df_player["player_involved_in_counterpress"] == True]
else:
    df_filtered_events = df_player.copy()

# === Obtener partidos con eventos disponibles según filtro ===
available_matches = sorted(df_filtered_events["match_id"].dropna().unique().tolist())

if not available_matches:
    st.warning("No matches available for this player and action filter.")
    st.stop()

selected_match_id = st.sidebar.selectbox("Select match:", available_matches)
df_match = df_filtered_events[df_filtered_events["match_id"] == selected_match_id]

# === Selección de jugada
if df_match.empty:
    st.warning("No actions found for this match.")
    st.stop()

frame_selected = st.sidebar.selectbox("Select frame_loss to view freeze frame:",
                                      sorted(df_match["frame_loss"].unique().tolist()))
row_selected = df_match[df_match["frame_loss"] == frame_selected].iloc[0]

# Get correct player ID to highlight
# Player ID lookup
player_ids = {
    6028: "Mbappé",
    12253: "Vinicius Jr",
    23903: "Rodrygo"
}
name_to_id = {v: k for k, v in player_ids.items()}
selected_id = name_to_id.get(selected_player)

# === Load meta and freeze frame ===
meta_path = os.path.join(META_FOLDER, f"{selected_match_id}.json")
freeze_path = os.path.join(FREEZE_FOLDER, f"{selected_match_id}.parquet")
df_frames = pd.read_parquet(freeze_path)

with open(meta_path, "r", encoding="utf-8") as f:
    meta = json.load(f)

pitch_length = meta["pitch_length"]
pitch_width = meta["pitch_width"]

teams_meta = pd.DataFrame([
    {**meta["home_team"], "team_id": meta["home_team"]["id"]},
    {**meta["away_team"], "team_id": meta["away_team"]["id"]},
])
kits_meta = pd.DataFrame([
    {**meta["home_team_kit"], "team_id": meta["home_team"]["id"]},
    {**meta["away_team_kit"], "team_id": meta["away_team"]["id"]},
])
teams_meta = teams_meta.merge(kits_meta, on="team_id")

players_meta = pd.DataFrame(meta["players"])
players_meta = players_meta.rename(columns={"id": "player_id", "number": "jersey_number"})
players_meta = players_meta.merge(
    teams_meta[["team_id", "short_name", "jersey_color", "number_color"]],
    on="team_id", how="left"
)

# === Summary metrics ===
col1, col2, col3 = st.columns(3)
col1.metric("Total actions", len(df_match))
col2.metric("Player near", df_match["player_near_loss"].sum())
col3.metric("Player involved", df_match["player_involved_in_counterpress"].sum())

# === Dynamic frame viewer ===
frame_loss = int(row_selected["frame_loss"])
frame_range = list(range(frame_loss - 10, frame_loss + 11))
frame_range = [f for f in frame_range if f in df_frames["frame"].unique()]

frame_to_display = st.slider("Select frame", min_value=min(frame_range),
                             max_value=max(frame_range),
                             value=frame_loss, step=1)

st.markdown("## 🎮 Frame viewer")
df_frame = df_frames[df_frames["frame"] == frame_to_display]
df_frame = df_frame.merge(players_meta, on="player_id", how="left")

pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
              pitch_color='white', line_color='black')
fig, ax = pitch.draw(figsize=(10, 7))

df_ball = df_frame[df_frame["is_ball"] == True]
ax.scatter(df_ball["x"], df_ball["y"], color="black", s=60, zorder=6)

df_players = df_frame[df_frame["is_ball"] == False]
ax.scatter(df_players["x"], df_players["y"], s=150,
           color=df_players["jersey_color"], edgecolors="black", zorder=5)

for _, row in df_players.iterrows():
    ax.text(row["x"], row["y"], str(int(row["jersey_number"])),
            color=row["number_color"], fontsize=8, weight="bold",
            ha="center", va="center", zorder=6)

highlight = df_players[df_players["player_id"] == selected_id]
if not highlight.empty:
    ax.scatter(highlight["x"], highlight["y"], s=200,
               facecolors='none', edgecolors='blue', linewidths=2,
               label=selected_player, zorder=7)

ax.set_title(f"Freeze Frame {frame_to_display} (Match ID: {selected_match_id})", fontsize=14)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=3)
st.pyplot(fig)

# === Export GIF animation ===
st.markdown("## 🎮 Generate animation")
frame_padding = st.slider("How many frames before/after to include?", 10, 150, value=100, step=10)
frame_range = list(range(frame_loss - frame_padding, frame_loss + frame_padding + 1))

if st.button("🎮 Export GIF animation"):
    st.info("⏳ Generating animation...")
    images = []
    for f in frame_range:
        df_f = df_frames[(df_frames["frame"] == f)]
        if df_f.empty:
            continue
        df_f = df_f.merge(players_meta, on="player_id", how="left")
        pitch = Pitch(pitch_type='skillcorner', pitch_length=pitch_length, pitch_width=pitch_width,
                      pitch_color='white', line_color='black')
        fig, ax = pitch.draw(figsize=(8, 6))
        df_ball = df_f[df_f["is_ball"] == True]
        df_players = df_f[df_f["is_ball"] == False]
        ax.scatter(df_ball["x"], df_ball["y"], color="black", s=60, zorder=6)
        ax.scatter(df_players["x"], df_players["y"], s=150,
                   color=df_players["jersey_color"], edgecolors="black", zorder=5)
        for _, row in df_players.iterrows():
            ax.text(row["x"], row["y"], str(int(row["jersey_number"])),
                    color=row["number_color"], fontsize=8, weight="bold",
                    ha="center", va="center", zorder=6)
        highlight = df_players[df_players["player_id"] == selected_id]
        if not highlight.empty:
            ax.scatter(highlight["x"], highlight["y"], s=200, facecolors='none',
                       edgecolors='blue', linewidths=2, label=selected_player, zorder=7)
        ax.set_title(f"Frame {f}", fontsize=12)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        images.append(Image.open(buf))
        plt.close(fig)
    gif_path = os.path.join(DATA_FOLDER, f"{selected_player.lower().replace(' ', '_')}_sequence_{selected_match_id}_f{frame_loss}.gif")
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=150, loop=0)
    st.success(f"✅ Animation exported: {gif_path}")
    st.image(images, caption=[f"Frame {f}" for f in frame_range[:len(images)]], width=800)
