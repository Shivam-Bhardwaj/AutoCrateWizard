# app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid Layout System.

Provides a user interface for inputting product details, displays calculated
skid layout metrics, and visualizes the layout using Plotly.
(Improved Visibility & Autoscaling Version 5 - Simplified UI & Viz)
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging
import math

# Import the core logic function
from skid_logic import calculate_skid_layout
# Import placeholder for future expansion
from floorboard_logic import calculate_floorboard_layout

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Streamlit Page Setup ---
st.set_page_config(layout="wide", page_title="AutoCrate Wizard")
st.title("⚙️ AutoCrate Wizard - Skid Layout System")
st.caption("Calculates skid layout based on AMAT Standard 5.3 (up to 20,000 lbs)")

# --- Sidebar Inputs ---
st.sidebar.header("Product & Crate Parameters")

product_weight = st.sidebar.slider(
    "Product Weight (lbs)",
    min_value=10.0,
    max_value=20000.0,
    value=4500.0,
    step=10.0,
    help="Total weight of the product being shipped."
)

product_width = st.sidebar.slider(
    "Product Width (inches)",
    min_value=10.0,
    max_value=125.0,
    value=90.0,
    step=0.5,
    format="%.1f",
    help="Width of the product at its widest point."
)

st.sidebar.subheader("Crate Construction Constants")
clearance_side = st.sidebar.number_input(
    "Clearance per Side (inches)", min_value=0.0, value=2.0, step=0.1, format="%.2f",
    help="Minimum space between product and inner crate wall."
)
panel_thickness = st.sidebar.number_input(
    "Panel Thickness (inches)", min_value=0.0, value=0.25, step=0.01, format="%.2f",
    help="Thickness of the side panels (e.g., plywood)."
)
cleat_thickness = st.sidebar.number_input(
    "Cleat Thickness (inches)", min_value=0.0, value=0.75, step=0.01, format="%.2f",
    help="Thickness of the structural cleats inside the panels."
)


# --- Core Logic Execution ---
layout_results = calculate_skid_layout(
    product_weight, product_width, clearance_side, panel_thickness, cleat_thickness
)

# --- Main Area Display ---
st.header("Skid Layout Results")

# Handle potential errors or 'OVER' status from the logic function
if layout_results["status"] in ["ERROR", "OVER"]:
    st.error(f"**Status:** {layout_results['status']} - {layout_results['message']}")
    st.stop()
elif layout_results["status"] == "TOO WIDE":
     st.warning(f"**Status:** {layout_results['status']} - {layout_results['message']}")
else: # Status is OK
     st.success(f"**Status:** ✅ OK - {layout_results['message']}")

# --- Display Key Metrics ---
st.subheader("Key Design Metrics")
col1, col2, col3 = st.columns(3)

# Use try-except for robustness in case keys are missing on error states
try:
    # Calculate Overall Skid Span for metric display
    skid_w_metric = layout_results['skid_width']
    skid_count_metric = layout_results['skid_count']
    positions_metric = layout_results['skid_positions']
    overall_skid_span_metric = 0.0
    if skid_count_metric == 1 and positions_metric: # Check positions_metric is not empty
        overall_skid_span_metric = skid_w_metric
    elif skid_count_metric > 1 and positions_metric: # Check positions_metric is not empty
        first_skid_outer_edge = positions_metric[0] - skid_w_metric / 2
        last_skid_outer_edge = positions_metric[-1] + skid_w_metric / 2
        overall_skid_span_metric = last_skid_outer_edge - first_skid_outer_edge

    with col1:
        st.metric("Crate Width", f"{layout_results['crate_width']:.2f}\"")
        st.metric("Skid Type", f"{layout_results['skid_type']}", help="Nominal size (e.g., 3x4, 4x4, 4x6)")

    with col2:
        # *** Updated Metric: Overall Skid Span ***
        st.metric("Overall Skid Span", f"{overall_skid_span_metric:.2f}\"", help="Distance between outer edges of the outermost skids.")
        st.metric("Skid Width", f"{layout_results['skid_width']:.2f}\"", help="Actual width dimension used for layout")

    with col3:
        st.metric("Skid Count", f"{layout_results['skid_count']}")
        st.metric("Actual Spacing", f"{layout_results['spacing_actual']:.2f}\"",
                  help="Center-to-center distance between skids.")
        st.metric("Max Allowed Spacing", f"{layout_results['max_spacing']:.2f}\"")
except KeyError as e:
    st.error(f"Missing expected result key: {e}. Cannot display all metrics.")
    st.stop() # Stop if core data is missing
except Exception as e: # Catch potential errors during span calculation
    st.error(f"Error calculating metrics: {e}")
    st.stop()


# --- Visualization ---
st.subheader("Top-Down Skid Layout Visualization")

fig = go.Figure()

# Extract data for plotting (check if keys exist after potential error above)
if layout_results["status"] == "OK":
    skid_w = layout_results['skid_width']
    skid_h_actual = layout_results['skid_height']
    skid_count = layout_results['skid_count']
    positions = layout_results['skid_positions']
    spacing = layout_results['spacing_actual']
    max_spacing_val = layout_results['max_spacing']

    # Determine a reasonable visual height for the plot elements
    viz_base_height = max(3.0, min(8.0, 0.08 * skid_count * skid_w if skid_count * skid_w > 0 else 3.0))
    y_padding_factor = 1.5
    y_padding = viz_base_height * y_padding_factor


    # --- Plot Elements ---
    ANNOTATION_FONT_SIZE_SMALL = 11
    ANNOTATION_FONT_SIZE_MEDIUM = 12
    ANNOTATION_FONT_SIZE_LARGE = 14

    # 1. Skids
    skid_color = "#8B4513"
    skid_outline_color = "#654321"
    for i, pos in enumerate(positions):
        x0 = pos - skid_w / 2
        x1 = pos + skid_w / 2
        y_center = 0
        y0 = y_center - viz_base_height / 2
        y1 = y_center + viz_base_height / 2

        fig.add_shape(type="rect",
            x0=x0, y0=y0, x1=x1, y1=y1,
            fillcolor=skid_color,
            line=dict(color=skid_outline_color, width=1.5),
        )

        # Add Skid Label Annotation (Above)
        fig.add_annotation(
            x=pos, y=y1 + y_padding * 0.3,
            text=f"<b>Skid {i}</b>",
            showarrow=False,
            font=dict(color="black", size=ANNOTATION_FONT_SIZE_MEDIUM)
        )

        # Add Skid Position Annotation (Below)
        fig.add_annotation(
            x=pos, y=y0 - y_padding * 0.2,
            text=f'{pos:.2f}"',
            showarrow=False,
            font=dict(color="black", size=ANNOTATION_FONT_SIZE_SMALL)
        )

    # Add single dummy trace for Skid legend entry
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers',
                             marker=dict(color=skid_color, size=10, symbol='square',
                                         line=dict(color=skid_outline_color, width=1)),
                             name='Skids'))

    # 2. Spacing Annotations (Between Skids)
    if skid_count > 1:
        y0_ref = -viz_base_height / 2
        y_spacing_annotation = y0_ref - y_padding * 0.5
        for i in range(skid_count - 1):
            pos1 = positions[i]
            pos2 = positions[i+1]
            mid_x = (pos1 + pos2) / 2
            fig.add_annotation(
                x=mid_x, y=y_spacing_annotation,
                text=f'↔ {spacing:.2f}"<br>(Max: {max_spacing_val:.2f}")',
                showarrow=False,
                align="center",
                font=dict(color="purple", size=ANNOTATION_FONT_SIZE_SMALL)
            )

    # 3. Calculate and Add "Overall Skid Span" Annotation (Top Center)
    # Re-calculate here for the visualization context
    overall_skid_span_viz = 0.0
    if skid_count == 1:
        overall_skid_span_viz = skid_w
    elif skid_count > 1:
        first_skid_outer_edge = positions[0] - skid_w / 2
        last_skid_outer_edge = positions[-1] + skid_w / 2
        overall_skid_span_viz = last_skid_outer_edge - first_skid_outer_edge

    y1_ref = viz_base_height / 2
    y_top_annotation = y1_ref + y_padding * 0.6

    fig.add_annotation(
        x=(positions[0] + positions[-1])/2 if skid_count > 0 else 0,
        y=y_top_annotation,
        text=f'<b>Overall Skid Span: {overall_skid_span_viz:.2f}"</b>',
        showarrow=False,
        font=dict(color="black", size=ANNOTATION_FONT_SIZE_LARGE)
    )

    # Configure Layout
    fig.update_layout(
        title="Skid Layout (Top View)",
        xaxis_title=None, # <<< Removed X axis title
        yaxis_title=None,
        yaxis=dict(
            showticklabels=False, showgrid=False, zeroline=False,
            scaleanchor="x", scaleratio=1
        ),
        xaxis=dict(
            zeroline=False,
            showgrid=False,
            showline=False, # <<< Removed X axis line
            showticklabels=False # <<< Hide X axis tick labels as well
        ),
        plot_bgcolor='white', paper_bgcolor='white',
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1,
            font=dict(color="black", size=12)
        ),
        margin=dict(l=20, r=20, t=80, b=20),
        autosize=True
    )
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True, showticklabels=False) # Ensure ticks are off

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Visualization cannot be generated due to calculation errors.")


# --- REMOVED Debugging Truth Table Section ---


# --- Placeholder for Future Modules ---
# (Keep placeholder section as it was)
st.divider()
st.subheader("Future Modules (Placeholder)")
st.caption("Output from the skid logic can be used by other modules.")

if st.button("Calculate Floorboard Layout (Placeholder)"):
     dummy_length = st.number_input("Enter Crate Length (for Floorboard)", value=120.0, step=1.0)
     floor_results = calculate_floorboard_layout(layout_results, crate_length=dummy_length)
     st.write(floor_results)

