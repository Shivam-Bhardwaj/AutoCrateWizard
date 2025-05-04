import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import streamlit as st
import core
import visualizer




st.set_page_config(layout="wide")
st.title("🚧 AutoCrate Wizard")

# UI sliders
st.sidebar.header("📦 Crate Parameters")
weight = st.sidebar.slider("Weight (kg)", 0, 5000, 1000)
width = st.sidebar.slider("Width (mm)", 500, 3000, 1200)
length = st.sidebar.slider("Length (mm)", 500, 3000, 2200)
height = st.sidebar.slider("Height (mm)", 500, 3000, 1000)

# Core logic
skid_count = core.determine_skids(weight, width, length)
st.markdown(f"**Recommended Skids:** {skid_count}")

# Visuals
fig_top, fig_side, fig_front = visualizer.create_crate_figures(width, length, height, skid_count)

# Debug output
st.write("Inputs →", {"Weight": weight, "Width": width, "Length": length, "Height": height})
st.write("Skid count:", skid_count)

# Display charts
col1, col2 = st.columns(2)
with col1:
    st.subheader("📐 Top View")
    st.plotly_chart(fig_top, use_container_width=True)
with col2:
    st.subheader("📐 Side View")
    st.plotly_chart(fig_side, use_container_width=True)

st.subheader("📐 Front View")
st.plotly_chart(fig_front, use_container_width=True)
