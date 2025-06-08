# Home.py

import streamlit as st

st.set_page_config(layout="centered")
st.title("⚽ Project Mbappé Twelve - Counterpressing App")

st.markdown("""
Welcome to the counterpressing analysis application for Real Madrid forwards.

This tool allows you to explore and compare immediate defensive actions after ball losses,
with a focus on three attackers:

- **Kylian Mbappé**
- **Vinicius Jr**
- **Rodrygo**

---

### 📄 Navigation

Use the sidebar menu to access each section:

1. 🔎 Mbappé - Counterpress Viewer: visualization of specific sequences and freeze frames.
2. 📊 Mbappé - Summary: full statistical analysis for Mbappé.
3. 📊 Player Comparison: individual analysis for Mbappé, Vinicius, and Rodrygo.
4. 📊 Global Comparison: comparative table and bar charts across all three players.

---

### 🧠 About this project

This app is part of the **Mbappé Twelve Project**, developed using enriched event data + freeze frames from Skill Corner.

Developed by **Guzmán Montgomery**.

---
""")
