# app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid & Floorboard Layout System.

Provides UI for inputs, displays skid/floorboard metrics, and visualizes layouts.
Recalculates automatically. Floorboards calculated symmetrically
along product length + 2*clearance, using available lumber based on refined rules
(Std >=5.5 & <=11.25). Allows one optional Custom Narrow board (>=2.5 & <5.5)
IF explicitly selected by the user (DEFAULT is ON). Aims for centered gap <= 0.25".
Issues WARNING if gap > 0.25". Uses absolute imports.
Version 0.3.19 - Fixed ImportError by reverting to absolute imports. Improved visualization font colors, added tolerance to skid logic check (originally in 0.3.18).
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import logging
import math
from collections import Counter # For counting boards

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Import Core Logic Modules ---
try:
    # Use absolute import
    from skid_logic import calculate_skid_layout, FLOAT_TOLERANCE as SKID_FLOAT_TOLERANCE
    log.info("Successfully imported calculate_skid_layout from skid_logic.")
except ImportError as e:
    log.error(f"Failed to import from skid_logic: {e}")
    st.error(f"Fatal Error: Could not import `skid_logic.py`. Ensure it's in the same directory and there are no errors. Details: {e}")
    st.stop()

try:
    # Import floorboard logic (expecting v0.3.9 or later)
    # Use absolute import
    from floorboard_logic import (
        calculate_floorboard_layout,
        calculate_overall_skid_span,
        MAX_CENTER_GAP,
        ALL_STANDARD_FLOORBOARDS,
        FLOAT_TOLERANCE as FLOORBOARD_FLOAT_TOLERANCE # Calculation tolerance from logic module
    )
    log.info("Successfully imported calculate_floorboard_layout and constants from floorboard_logic.")
    floorboard_logic_available = True
    # Define options for the multiselect widget
    STANDARD_LUMBER_OPTIONS = list(ALL_STANDARD_FLOORBOARDS.keys())
    CUSTOM_NARROW_OPTION_TEXT = "Use Custom Narrow Board (Fill < 5.5\")"
    ALL_UI_LUMBER_OPTIONS = STANDARD_LUMBER_OPTIONS + [CUSTOM_NARROW_OPTION_TEXT]
    # Default selection includes standard boards (>= 5.5") AND the custom narrow option
    DEFAULT_STANDARD_LUMBER = [
        k for k, v in ALL_STANDARD_FLOORBOARDS.items()
        if (v >= 5.5 - FLOORBOARD_FLOAT_TOLERANCE and v <= 11.25 + FLOORBOARD_FLOAT_TOLERANCE)
    ]
    DEFAULT_UI_LUMBER_SELECTION = DEFAULT_STANDARD_LUMBER + [CUSTOM_NARROW_OPTION_TEXT]

except ImportError as e:
    log.warning(f"`floorboard_logic.py` not found or failed to import: {e}")
    # Fallbacks if floorboard logic is missing
    def calculate_floorboard_layout(*args, **kwargs):
        return {"status": "NOT FOUND", "message": f"floorboard_logic.py not found or import error: {e}"}
    def calculate_overall_skid_span(*args, **kwargs): return None
    floorboard_logic_available = False
    MAX_CENTER_GAP = 0.25
    # Fallback calculation tolerance - matches skid_logic now
    SKID_FLOAT_TOLERANCE = 1e-6
    FLOORBOARD_FLOAT_TOLERANCE = 1e-6
    STANDARD_LUMBER_OPTIONS = ["2x12", "2x10", "2x8", "2x6"]
    CUSTOM_NARROW_OPTION_TEXT = "Use Custom Narrow Board (Fill < 5.5\")"
    ALL_UI_LUMBER_OPTIONS = STANDARD_LUMBER_OPTIONS + [CUSTOM_NARROW_OPTION_TEXT]
    DEFAULT_UI_LUMBER_SELECTION = STANDARD_LUMBER_OPTIONS + [CUSTOM_NARROW_OPTION_TEXT]


# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="AutoCrate Wizard", page_icon="⚙️")

# --- Page Title and Description ---
st.title("⚙️ AutoCrate Wizard - Skid & Floorboard Layout")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts based on product details and selected lumber (up to 20,000 lbs).")
st.divider()

# --- Sidebar Inputs ---
st.sidebar.header("Product & Crate Parameters")

product_weight = st.sidebar.slider( "Product Weight (lbs)", 1.0, 20000.0, 1500.0, 10.0, help="Enter the weight of the product to be crated." )
st.sidebar.caption("Skid type/spacing changes at: 500, 4500, 6000, 12000 lbs")
product_width = st.sidebar.slider( "Product Width (inches)", 10.0, 125.0, 90.0, 0.5, "%.1f", help="Enter the width of the product (across the skids)." )
product_length = st.sidebar.slider( "Product Length (inches)", 10.0, 96.0, 44.8, 1.0, "%.1f", help="Enter the length of the product (along the skids)." ) # Default 44.8 -> Target 48.8 (Custom fills)

st.sidebar.subheader("Crate Construction Constants")
clearance_side = st.sidebar.number_input( "Clearance per Side (inches)", 0.0, value=2.0, step=0.1, format="%.2f", help="Clearance space added to each side of the product width and length." )
panel_thickness = st.sidebar.number_input( "Panel Thickness (inches)", 0.0, value=0.25, step=0.01, format="%.2f", help="Thickness of the crate wall/floor panels." )
cleat_thickness = st.sidebar.number_input( "Cleat Thickness (inches)", 0.0, value=0.75, step=0.01, format="%.2f", help="Thickness of the internal crate cleats." )

st.sidebar.subheader("Floorboard Options")
selected_ui_options = st.sidebar.multiselect( "Available Floorboard Lumber", options=ALL_UI_LUMBER_OPTIONS, default=DEFAULT_UI_LUMBER_SELECTION, help="Select standard lumber sizes (e.g., 2x12). Deselect 'Use Custom Narrow Board' to prevent filling center gaps between 2.5\" and 5.5\" with a custom-width piece." )

# --- Process Lumber Selection ---
selected_nominal_sizes = [opt for opt in selected_ui_options if opt != CUSTOM_NARROW_OPTION_TEXT]
allow_custom_narrow = CUSTOM_NARROW_OPTION_TEXT in selected_ui_options

# --- Core Logic Execution ---
log.info(f"UI Inputs: Wgt={product_weight}, W={product_width}, L={product_length}, Clr={clearance_side}, Pnl={panel_thickness}, Clt={cleat_thickness}, SelectedNominal={selected_nominal_sizes}, AllowCustom={allow_custom_narrow}")
try:
    layout_results = calculate_skid_layout( product_weight, product_width, clearance_side, panel_thickness, cleat_thickness )
    log.info(f"Skid calculation status: {layout_results.get('status')}")
    skid_status = layout_results.get("status", "UNKNOWN")
except Exception as e:
    log.error(f"Error during skid calculation: {e}", exc_info=True); st.error(f"An unexpected error occurred during skid calculation: {e}")
    layout_results = { "status": "CRITICAL ERROR", "message": f"Skid calculation failed: {e}" }; skid_status = "CRITICAL ERROR"

floor_results = None
if floorboard_logic_available and skid_status == "OK":
    if not selected_nominal_sizes and not allow_custom_narrow:
         log.warning("Floorboard calculation skipped: No standard lumber selected AND custom narrow not allowed.")
         floor_results = {"status": "INPUT ERROR", "message": "No standard lumber selected and custom narrow board not allowed."}
    else:
        log.info("Calling floorboard calculation...")
        try:
            floor_results = calculate_floorboard_layout( skid_layout_data=layout_results, product_length=product_length, clearance_side=clearance_side, available_nominal_sizes=selected_nominal_sizes, allow_custom_narrow_board=allow_custom_narrow )
            log.info(f"Floorboard calculation status: {floor_results.get('status')}")
        except Exception as e:
             log.error(f"Error during floorboard calculation: {e}", exc_info=True); st.error(f"An unexpected error occurred during floorboard calculation: {e}")
             floor_results = {"status": "CRITICAL ERROR", "message": f"Floorboard calculation failed: {e}"}

# --- Main Area Display ---

# =====================================
# Skid Results Section
# =====================================
st.header("Skid Layout Results")
skid_message = layout_results.get("message", "No message provided.")
if skid_status == "OK": st.success(f"**Skid Status:** ✅ OK - {skid_message}")
elif skid_status in ["ERROR", "OVER", "CRITICAL ERROR"]: st.error(f"**Skid Status:** ❌ {skid_status} - {skid_message}")
else: st.warning(f"**Skid Status:** ⚠️ {skid_status} - {skid_message}")
st.divider()

# =====================================
# Summary Metrics Section
# =====================================
st.subheader("📊 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
try:
    crate_total_length = product_length + 2 * clearance_side + 2 * (panel_thickness + cleat_thickness)
    def format_metric(value, unit="\"", decimals=2, default="N/A"):
        if value is None or not isinstance(value, (int, float)): return default
        try: return f"{value:.{decimals}f}{unit}"
        except (TypeError, ValueError): return str(value) if value is not None else default

    with col1: # Crate Dims
        st.markdown("**📦 Crate Dimensions**"); st.metric("Crate Width", format_metric(layout_results.get('crate_width'))); st.metric("Crate Length", format_metric(crate_total_length))
    with col2: # Skid Setup
        st.markdown("**🔩 Skid Setup**"); st.metric("Skid Type", layout_results.get('skid_type', 'N/A')); st.metric("Skid Width", format_metric(layout_results.get('skid_width'))); skid_count_metric = layout_results.get('skid_count'); st.metric("Skid Count", str(skid_count_metric) if skid_count_metric is not None else "N/A")
    with col3: # Skid Spacing
        st.markdown("**↔️ Skid Spacing**"); spacing_actual_metric = layout_results.get('spacing_actual'); spacing_display = format_metric(spacing_actual_metric) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"; st.metric("Actual Spacing", spacing_display, help="Center-to-center spacing between skids."); st.metric("Max Allowed Spacing", format_metric(layout_results.get('max_spacing'))); overall_skid_span_metric = calculate_overall_skid_span(layout_results) if floorboard_logic_available else None
        if overall_skid_span_metric is None and skid_status == "OK": # Fallback calc
             skid_w_metric = layout_results.get('skid_width'); positions_metric = layout_results.get('skid_positions', []); skid_count_metric = layout_results.get('skid_count')
             if skid_count_metric == 1 and skid_w_metric is not None: overall_skid_span_metric = skid_w_metric
             elif skid_count_metric > 1 and positions_metric and skid_w_metric is not None and len(positions_metric) == skid_count_metric: first_outer_edge = positions[0] - skid_w_metric / 2.0; last_outer_edge = positions[-1] + skid_w_metric / 2.0; overall_skid_span_metric = abs(last_outer_edge - first_outer_edge)
        span_display = format_metric(overall_skid_span_metric) if overall_skid_span_metric is not None else "N/A"; st.metric("Overall Skid Span", span_display, help="Total width covered by skids, outer edge to outer edge.")
    with col4: # Floorboard Summary
        st.markdown("**🪵 Floorboard Summary**");
        if floor_results:
            fb_status = floor_results.get('status', 'UNKNOWN'); fb_message = floor_results.get('message', 'No message.'); fb_center_gap = floor_results.get("center_gap"); fb_boards = floor_results.get("floorboards", []); fb_board_counts = floor_results.get("board_counts", {}); fb_custom_width = floor_results.get("custom_board_width"); fb_length_across_skids = floor_results.get("floorboard_length_across_skids"); fb_calculated_span = floor_results.get("calculated_span_covered"); fb_target_span = floor_results.get("target_span_along_length"); fb_narrow_used = floor_results.get("narrow_board_used")
            status_color = "green" if fb_status == 'OK' else "orange" if fb_status == 'WARNING' else "red"; status_icon = "✅" if fb_status == 'OK' else "⚠️" if fb_status == 'WARNING' else "❌"; st.markdown(f"Status: <span style='color:{status_color};'>{status_icon} {fb_status}</span>", unsafe_allow_html=True)
            if fb_status not in ["NOT FOUND", "INPUT ERROR", "CRITICAL ERROR"]:
                st.metric("Total Boards", len(fb_boards) if fb_boards else "N/A"); st.metric("Board Length", format_metric(fb_length_across_skids), help="Length of each floorboard plank (equals Overall Skid Span)."); st.metric("Target Span", format_metric(fb_target_span), help="Target width to cover with floorboards (Product Length + 2 * Clearance Side)."); gap_display_val = "N/A"; gap_help_text = None
                if fb_center_gap is not None:
                    gap_display_val = f"{fb_center_gap:.3f}\"";
                    if fb_status == "WARNING": gap_display_val = f"⚠️ {gap_display_val}"; gap_help_text = f"Gap exceeds recommended max ({MAX_CENTER_GAP:.3f}\")"
                gap_color = "orange" if fb_status == "WARNING" else "inherit"; st.markdown(f"**Center Gap:** <span style='color:{gap_color};'>{gap_display_val}</span>", unsafe_allow_html=True);
                if gap_help_text: st.caption(gap_help_text)
                custom_width_display = format_metric(fb_custom_width, decimals=3) if fb_narrow_used else "Not Used"; st.metric("Custom Narrow Used", custom_width_display, help="Width of the 'Custom' board used for center fill, if any.")
                counts_str = ", ".join([f"{nom}: {cnt}" for nom, cnt in sorted(fb_board_counts.items())]); st.markdown(f"**Counts:** {counts_str if counts_str else 'None'}"); st.markdown("---")
                if fb_status in ["OK", "WARNING"] and fb_calculated_span is not None and fb_target_span is not None:
                    if math.isclose(fb_calculated_span, fb_target_span, abs_tol=FLOORBOARD_FLOAT_TOLERANCE * 10): st.success(f"✅ Span Check: PASS")
                    else: st.error(f"❌ Span Check: FAIL (Calc: {fb_calculated_span:.3f}\" vs Target: {fb_target_span:.3f}\")"); log.error(f"Floorboard sanity check failed: Calculated={fb_calculated_span}, Target={fb_target_span}")
                else: st.caption("Sanity check requires valid calculation.")
            if fb_status not in ['OK', 'WARNING']: st.caption(f"{fb_message}")
        else: # Floor_results is None
             st.markdown("**Status:** Not Calculated");
             if not floorboard_logic_available: st.caption("Floorboard logic module not found.")
             elif skid_status == "OK" and not selected_nominal_sizes and not allow_custom_narrow: st.caption("Please select standard lumber or allow custom narrow board in the sidebar.")
             elif skid_status != "OK": st.caption("Requires OK skid status.")
except Exception as e: st.error(f"An error occurred while displaying metrics: {e}"); log.error(f"Metrics display error: {e}", exc_info=True); skid_status = "METRIC DISPLAY ERROR"

# --- Visualizations ---
st.divider(); st.header("Layout Visualizations")

# =====================================
# Skid Visualization Section
# =====================================
st.subheader("Top-Down Skid Layout")
skid_fig = go.Figure(); skid_plot_generated = False; skid_plot_error = None
if skid_status == "OK":
    try:
        skid_w_viz = layout_results.get('skid_width'); skid_count_viz = layout_results.get('skid_count'); positions_viz = layout_results.get('skid_positions'); spacing_viz = layout_results.get('spacing_actual'); max_spacing_viz = layout_results.get('max_spacing'); skid_h_viz = layout_results.get('skid_height', 3.5)
        if (skid_w_viz is not None and skid_w_viz > SKID_FLOAT_TOLERANCE and skid_count_viz is not None and skid_count_viz > 0 and positions_viz and len(positions_viz) == skid_count_viz):
            SKID_COLOR = "#8B4513"; SKID_OUTLINE_COLOR = "#654321"; FONT_S, FONT_M, FONT_L = 10, 11, 13; SPACING_COLOR = "purple"; viz_skid_h_display = max(skid_h_viz * 0.5, skid_w_viz * 0.5, 5.0); y_center, y_bottom, y_top = 0, -viz_skid_h_display / 2, viz_skid_h_display / 2; y_padding = viz_skid_h_display * 1.2
            for i, pos in enumerate(positions_viz): x0, x1 = pos - skid_w_viz / 2, pos + skid_w_viz / 2; skid_fig.add_shape(type="rect", x0=x0, y0=y_bottom, x1=x1, y1=y_top, fillcolor=SKID_COLOR, line=dict(color=SKID_OUTLINE_COLOR, width=1.5)); skid_fig.add_annotation(x=pos, y=y_top, text=f"<b>Skid {i+1}</b>", showarrow=False, font=dict(size=FONT_M, color="white"), yshift=20); skid_fig.add_annotation(x=pos, y=y_bottom, text=f'{pos:.2f}"', showarrow=False, font=dict(size=FONT_S, color="white"), yshift=-20) # Changed font color to white
            skid_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Skids', marker=dict(color=SKID_COLOR, size=10, symbol='square', line=dict(color=SKID_OUTLINE_COLOR, width=1))))
            if skid_count_viz > 1 and spacing_viz is not None and max_spacing_viz is not None:
                 y_spacing_ann = y_bottom - y_padding * 0.6;
                 for i in range(skid_count_viz - 1): mid_x = (positions_viz[i] + positions_viz[i+1]) / 2; skid_fig.add_annotation(x=mid_x, y=y_spacing_ann, text=f'↔ {spacing_viz:.2f}"<br>(Max: {max_spacing_viz:.2f}")', showarrow=False, align="center", font=dict(color=SPACING_COLOR, size=FONT_S), yshift=-10)
            overall_skid_span_viz = overall_skid_span_metric
            if overall_skid_span_viz is not None and overall_skid_span_viz > SKID_FLOAT_TOLERANCE: y_top_ann = y_top + y_padding * 0.8; plot_center_x = (positions_viz[0] + positions_viz[-1]) / 2 if positions_viz else 0; skid_fig.add_annotation(x=plot_center_x, y=y_top_ann, text=f'<b>Overall Skid Span: {overall_skid_span_viz:.2f}"</b>', showarrow=False, font=dict(color="black", size=FONT_L), yshift=10)
            min_x_pos = positions_viz[0] - skid_w_viz / 2; max_x_pos = positions_viz[-1] + skid_w_viz / 2; x_padding = max(skid_w_viz * 1.5, (max_x_pos - min_x_pos) * 0.15); x_range = [min_x_pos - x_padding, max_x_pos + x_padding]; y_extent = y_padding * 1.5; y_range = [y_center - y_extent, y_center + y_extent]
            skid_fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis=dict(range=x_range, showline=False, showgrid=False, showticklabels=False, zeroline=False, fixedrange=True), yaxis=dict(range=y_range, showline=False, showgrid=False, showticklabels=False, zeroline=False, fixedrange=True), plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=10, r=10, t=30, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), autosize=True); skid_plot_generated = True
        else: skid_plot_error = "Missing or invalid skid data for plotting (Width, Count, or Positions)." ; log.warning(skid_plot_error)
    except Exception as e: skid_plot_error = f"Error generating skid visualization: {e}"; log.error(f"Skid visualization error: {e}", exc_info=True)
if skid_plot_generated: st.plotly_chart(skid_fig, use_container_width=True)
elif skid_plot_error: st.warning(f"⚠️ Could not generate skid visualization: {skid_plot_error}")
elif skid_status != "OK": st.info("Skid visualization requires a successful 'OK' calculation status.")
else: st.info("Enter parameters to generate the skid visualization.")

# =====================================
# Floorboard Visualization Section (Strict Zero Gap Check)
# =====================================
st.divider()
st.subheader("Top-Down Floorboard Layout")
if floorboard_logic_available:
    if floor_results:
        fb_status = floor_results.get("status", "UNKNOWN"); fb_message = floor_results.get("message", "No message.")
        floorboard_plot_generated = False; floorboard_plot_error = None
        if fb_status in ["OK", "WARNING"] and floor_results.get("floorboards"):
            fb_boards = floor_results.get("floorboards", []); fb_target_span = floor_results.get("target_span_along_length", 0.0); fb_center_gap = floor_results.get("center_gap", 0.0); fb_length_across_skids = floor_results.get("floorboard_length_across_skids", 0.0)
            if fb_boards and fb_length_across_skids > FLOORBOARD_FLOAT_TOLERANCE and fb_target_span > FLOORBOARD_FLOAT_TOLERANCE:
                try:
                    fb_fig = go.Figure()
                    NORMAL_BOARD_COLOR = "#D2B48C"; CUSTOM_BOARD_COLOR = "#8B4513"; GAP_COLOR = "#ADD8E6"; BOARD_OUTLINE_COLOR = "#A0522D"; ANNOTATION_COLOR_DARK = "black"; ANNOTATION_COLOR_LIGHT = "white"; ANNOTATION_SIZE = 9
                    x_center = 0; x_start = x_center - fb_length_across_skids / 2.0; x_end = x_center + fb_length_across_skids / 2.0

                    custom_board_present = False
                    for i, board in enumerate(fb_boards):
                        board_width_dim = board.get("actual_width", 0.0); board_start_y = board.get("position", 0.0); board_end_y = board_start_y + board_width_dim; board_nominal = board.get("nominal", "N/A")
                        board_color = CUSTOM_BOARD_COLOR if board_nominal == "Custom" else NORMAL_BOARD_COLOR
                        if board_nominal == "Custom": custom_board_present = True
                        fb_fig.add_shape(type="rect", x0=x_start, y0=board_start_y, x1=x_end, y1=board_end_y, fillcolor=board_color, line=dict(color=BOARD_OUTLINE_COLOR, width=0.5), name=f"Board {i+1} ({board_nominal})")
                        if board_width_dim > 1.5:
                             # Changed font color for standard boards to white
                            text_color = ANNOTATION_COLOR_LIGHT if board_color in [CUSTOM_BOARD_COLOR, NORMAL_BOARD_COLOR] else ANNOTATION_COLOR_DARK
                            fb_fig.add_annotation(x=x_center, y=(board_start_y + board_end_y) / 2, text=f'{board_width_dim:.2f}"', showarrow=False, font=dict(color=text_color, size=ANNOTATION_SIZE), align="center")

                    # --- Strict Zero Gap Check Visualization Logic ---
                    # Use original fb_center_gap for the check
                    if abs(fb_center_gap) > FLOORBOARD_FLOAT_TOLERANCE: # Use floorboard tolerance for gap check
                        log.debug(f"Attempting to visualize non-zero center gap: {fb_center_gap:.6f}")
                        center_y = fb_target_span / 2.0
                        # Use the original fb_center_gap for accurate height drawing
                        gap_start_y = center_y - fb_center_gap / 2.0
                        gap_end_y = center_y + fb_center_gap / 2.0
                        gap_start_y = max(0.0, gap_start_y); gap_end_y = min(fb_target_span, gap_end_y) # Clamp
                        log.debug(f"Calculated theoretical gap position for drawing: StartY={gap_start_y:.4f}, EndY={gap_end_y:.4f}")

                        # Draw the gap rectangle only if start < end (using tolerance)
                        if gap_end_y > gap_start_y + FLOORBOARD_FLOAT_TOLERANCE: # Use floorboard tolerance for drawing check
                            gap_legend_name = f'Center Gap ({fb_center_gap:.3f}")'; gap_bg_color = "rgba(173, 216, 230, 0.7)"
                            fb_fig.add_shape( type="rect", x0=x_start, y0=gap_start_y, x1=x_end, y1=gap_end_y, fillcolor=GAP_COLOR, line_width=0, opacity=0.7, name="Center Gap" )
                            fb_fig.add_annotation( x=x_center, y=(gap_start_y + gap_end_y) / 2, text=f"Gap:\n{fb_center_gap:.3f}\"", showarrow=False, font=dict(color=ANNOTATION_COLOR_DARK, size=8), bgcolor=gap_bg_color )
                            fb_fig.add_trace(go.Scatter( x=[None], y=[None], mode='markers', name=gap_legend_name, marker=dict(color=GAP_COLOR, size=10, symbol='square', opacity=0.7) ))
                        else:
                             log.warning(f"Could not draw significant gap: Calculated StartY ({gap_start_y:.4f}) >= EndY ({gap_end_y:.4f}) after clamping. Original Gap value was {fb_center_gap:.6f}. Gap magnitude: {abs(fb_center_gap):.6f}, Tolerance: {FLOORBOARD_FLOAT_TOLERANCE:.6f}")
                    else:
                        # If gap is negligible or zero, DO NOT DRAW the gap rectangle
                        log.debug(f"Center gap ({fb_center_gap:.6f}) is negligible or zero based on tolerance {FLOORBOARD_FLOAT_TOLERANCE}. Not drawing gap rectangle.")
                    # --- End Strict Zero Gap Logic ---

                    fb_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Standard Boards', marker=dict(color=NORMAL_BOARD_COLOR, size=10, symbol='square', line=dict(color=BOARD_OUTLINE_COLOR, width=1))))
                    if custom_board_present: fb_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Custom Board', marker=dict(color=CUSTOM_BOARD_COLOR, size=10, symbol='square', line=dict(color=BOARD_OUTLINE_COLOR, width=1))))

                    y_padding = max(5, fb_target_span * 0.05); x_padding = max(5, fb_length_across_skids * 0.05)
                    fb_fig.update_layout(xaxis_title="Floorboard Length (Across Skids)", yaxis_title="Target Span (Board Width Layout)", xaxis=dict(range=[x_start - x_padding, x_end + x_padding], zeroline=False, showgrid=False, showticklabels=True), yaxis=dict(range=[0 - y_padding, fb_target_span + y_padding], zeroline=False, showgrid=False, showticklabels=True), plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=10, r=10, t=30, b=10), showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height = 600)
                    floorboard_plot_generated = True
                except Exception as e: floorboard_plot_error = f"Error generating floorboard plot: {e}"; log.error(floorboard_plot_error, exc_info=True)
            if floorboard_plot_generated: st.plotly_chart(fb_fig, use_container_width=True)
            elif floorboard_plot_error: st.warning(f"⚠️ Could not generate floorboard visualization: {floorboard_plot_error}")
            else: st.info("Floorboard visualization requires valid boards and positive length/target span.")
        elif fb_status not in ["OK", "WARNING"]: st.info("No floorboard layout to display due to calculation status."); st.caption(f"Details: {fb_message}")
    elif skid_status == "OK":
         if not selected_nominal_sizes and not allow_custom_narrow: st.warning("Please select standard lumber or allow custom narrow board in the sidebar.")
         else: st.info("Adjust parameters or check calculation logic if floorboard layout is expected.")
    elif skid_status != "OK": st.info("Floorboard layout requires a successful skid calculation first.")
else: st.warning("Floorboard calculation disabled: `floorboard_logic.py` not found or failed to import.")

# =====================================
# Floorboard Details Table Section
# =====================================
if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
    st.divider(); st.subheader("Floorboard Details")
    fb_boards = floor_results.get("floorboards", [])
    board_data = [ {"Board #": i+1, "Nominal Size": b.get("nominal", "N/A"), "Width (in)": b.get("actual_width", 0.0), "Position Start (in)": b.get("position", 0.0)} for i, b in enumerate(fb_boards) ]
    df_boards = pd.DataFrame(board_data)
    st.dataframe( df_boards, use_container_width=True, hide_index=True, column_config={"Width (in)": st.column_config.NumberColumn(format="%.3f"), "Position Start (in)": st.column_config.NumberColumn(format="%.3f")} )

# --- Footer or Additional Info ---
st.sidebar.divider()
st.sidebar.info("AutoCrate Wizard v0.3.19\n\nVerify designs against official shipping standards.") # Update version

