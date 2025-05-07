# app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid, Floorboard & Cap Layout System.

Provides UI for inputs, displays skid/floorboard/cap metrics, and visualizes layouts.
Recalculates automatically.
Version 0.4.3 - Added Front and Side orthographic views for Cap Assembly.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import logging
import math
from collections import Counter # For counting boards

# --- Global Constants ---
FLOAT_TOLERANCE = 1e-6
STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS = 1.5
DEFAULT_CLEARANCE_ABOVE_PRODUCT = 1.5

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# --- Import Core Logic Modules ---
try:
    from skid_logic import calculate_skid_layout, FLOAT_TOLERANCE as SKID_FLOAT_TOLERANCE
    log.info("Successfully imported calculate_skid_layout from skid_logic.")
except ImportError as e:
    log.error(f"Failed to import from skid_logic: {e}")
    st.error(f"Fatal Error: Could not import `skid_logic.py`. Details: {e}")
    SKID_FLOAT_TOLERANCE = FLOAT_TOLERANCE # Fallback
    st.stop()

try:
    from floorboard_logic import (
        calculate_floorboard_layout, calculate_overall_skid_span, MAX_CENTER_GAP,
        ALL_STANDARD_FLOORBOARDS, FLOAT_TOLERANCE as FLOORBOARD_FLOAT_TOLERANCE
    )
    log.info("Successfully imported from floorboard_logic.")
    floorboard_logic_available = True
    STANDARD_LUMBER_OPTIONS = list(ALL_STANDARD_FLOORBOARDS.keys())
    CUSTOM_NARROW_OPTION_TEXT = "Use Custom Narrow Board (Fill < 5.5\")"
    ALL_UI_LUMBER_OPTIONS = STANDARD_LUMBER_OPTIONS + [CUSTOM_NARROW_OPTION_TEXT]
    DEFAULT_STANDARD_LUMBER = [
        k for k, v in ALL_STANDARD_FLOORBOARDS.items()
        if (v >= 5.5 - FLOORBOARD_FLOAT_TOLERANCE and v <= 11.25 + FLOORBOARD_FLOAT_TOLERANCE)
    ]
    DEFAULT_UI_LUMBER_SELECTION = DEFAULT_STANDARD_LUMBER + [CUSTOM_NARROW_OPTION_TEXT]
except ImportError as e:
    log.warning(f"`floorboard_logic.py` not found or failed to import: {e}")
    def calculate_floorboard_layout(*args, **kwargs): return {"status": "NOT FOUND", "message": f"floorboard_logic.py error: {e}"}
    def calculate_overall_skid_span(*args, **kwargs): return None
    floorboard_logic_available = False; MAX_CENTER_GAP = 0.25
    FLOORBOARD_FLOAT_TOLERANCE = FLOAT_TOLERANCE # Fallback
    STANDARD_LUMBER_OPTIONS = ["2x12", "2x10", "2x8", "2x6"]; CUSTOM_NARROW_OPTION_TEXT = "Use Custom Narrow Board (Fill < 5.5\")"
    ALL_UI_LUMBER_OPTIONS = STANDARD_LUMBER_OPTIONS + [CUSTOM_NARROW_OPTION_TEXT]; DEFAULT_UI_LUMBER_SELECTION = ALL_UI_LUMBER_OPTIONS

try:
    from cap_logic import (
        calculate_cap_layout, DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS,
        DEFAULT_NOMINAL_CAP_CLEAT_WIDTH, FLOAT_TOLERANCE as CAP_FLOAT_TOLERANCE
    )
    log.info("Successfully imported calculate_cap_layout from cap_logic.")
    cap_logic_available = True
except ImportError as e:
    log.warning(f"`cap_logic.py` not found or failed to import: {e}")
    def calculate_cap_layout(*args, **kwargs): return {"status": "NOT FOUND", "message": f"cap_logic.py error: {e}"}
    cap_logic_available = False
    DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS = 0.75 # Fallback
    DEFAULT_NOMINAL_CAP_CLEAT_WIDTH = 3.5   # Fallback
    CAP_FLOAT_TOLERANCE = FLOAT_TOLERANCE     # Fallback

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="AutoCrate Wizard", page_icon="⚙️")
st.title("⚙️ AutoCrate Wizard - Parametric Crate Layout System")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts for skids, floorboards, and caps.")
st.divider()

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Product & Crate Parameters")
    product_weight = st.slider("Product Weight (lbs)", 1.0, 20000.0, 1500.0, 10.0)
    st.caption("Skid type/spacing rules apply based on weight.")
    product_width = st.slider("Product Width (inches)", 1.0, 125.0, 90.0, 0.5, "%.1f", help="Product dimension ACROSS skids.")
    product_length = st.slider("Product Length (inches)", 1.0, 125.0, 90.0, 0.5, "%.1f", help="Product dimension ALONG skids.")
    product_actual_height = st.slider("Product Actual Height (inches)", 1.0, 120.0, 48.0, 0.5, "%.1f", help="Actual height of the product itself.")

    st.subheader("Crate Construction Constants")
    clearance_side_product = st.number_input("Clearance Side (Product W/L) (in)", 0.0, value=2.0, step=0.1, format="%.2f")
    clearance_above_product_ui = st.number_input("Clearance Above Product (to Cap) (in)", 0.0, value=DEFAULT_CLEARANCE_ABOVE_PRODUCT, step=0.1, format="%.2f")
    panel_thickness = st.number_input("Panel Thickness (Wall/Floor/Cap) (in)", 0.01, value=0.75, step=0.01, format="%.2f")
    framing_cleat_thickness = st.number_input("Framing Cleat Thickness (Side/End Walls) (in)", 0.01, value=0.75, step=0.01, format="%.2f")

    st.subheader("Floorboard Options")
    selected_ui_options = st.multiselect("Available Floorboard Lumber", options=ALL_UI_LUMBER_OPTIONS, default=DEFAULT_UI_LUMBER_SELECTION)
    selected_nominal_sizes = [opt for opt in selected_ui_options if opt != CUSTOM_NARROW_OPTION_TEXT]
    allow_custom_narrow = CUSTOM_NARROW_OPTION_TEXT in selected_ui_options

    st.subheader("Cap Options")
    max_top_cleat_spacing_ui = st.number_input("Max Top Cleat Spacing (inches)", 1.0, value=24.0, step=1.0, format="%.1f")

# --- Core Logic Execution ---
log.info(f"UI Inputs: Wgt={product_weight}, ProdW={product_width}, ProdL={product_length}, ProdH={product_actual_height}, ClrSide={clearance_side_product}, ClrAbove={clearance_above_product_ui}, PnlThk={panel_thickness}, FrameCltThk={framing_cleat_thickness}, MaxCapCleatSpace={max_top_cleat_spacing_ui}")
skid_results = {}; skid_status = "NOT RUN"
try:
    skid_results = calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)
    skid_status = skid_results.get("status", "UNKNOWN")
    log.info(f"Skid calculation status: {skid_status}")
except Exception as e:
    log.error(f"Skid calculation error: {e}", exc_info=True); st.error(f"Skid calc error: {e}")
    skid_results = {"status": "CRITICAL ERROR", "message": f"Skid calculation failed: {e}"}; skid_status = "CRITICAL ERROR"

crate_overall_width = skid_results.get('crate_width', 0.0)
crate_overall_length = product_length + 2 * (clearance_side_product + panel_thickness + framing_cleat_thickness)
skid_actual_height = skid_results.get('skid_height', 0.0)
cap_cleat_actual_thickness_for_height_calc = DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS if cap_logic_available else 0.75 # Use default if module fails
crate_overall_height_external = (skid_actual_height + STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS + product_actual_height + clearance_above_product_ui + panel_thickness + cap_cleat_actual_thickness_for_height_calc)
log.info(f"Calculated ODs: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, H={crate_overall_height_external:.2f}")

floor_results = None
if floorboard_logic_available and skid_status == "OK":
    if not selected_nominal_sizes and not allow_custom_narrow:
        floor_results = {"status": "INPUT ERROR", "message": "No standard lumber selected AND custom narrow not allowed."}
    else:
        try:
            floor_results = calculate_floorboard_layout(skid_results, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)
            log.info(f"Floorboard status: {floor_results.get('status')}")
        except Exception as e:
             log.error(f"Floorboard calc error: {e}", exc_info=True); st.error(f"Floorboard calc error: {e}")
             floor_results = {"status": "CRITICAL ERROR", "message": f"Floorboard calculation failed: {e}"}
elif not floorboard_logic_available: floor_results = {"status": "NOT FOUND", "message": "floorboard_logic.py missing."}
elif skid_status != "OK": floor_results = {"status": "SKIPPED", "message": "Skipped due to Skid status."}

cap_results = None
cap_cleat_nominal_thickness_used = DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS if cap_logic_available else 0.75
cap_cleat_nominal_width_used = DEFAULT_NOMINAL_CAP_CLEAT_WIDTH if cap_logic_available else 3.5

if cap_logic_available and skid_status == "OK":
    try:
        cap_results = calculate_cap_layout(
            crate_overall_width, crate_overall_length, panel_thickness,
            cap_cleat_nominal_thickness_used, cap_cleat_nominal_width_used, max_top_cleat_spacing_ui
        )
        log.info(f"Cap status: {cap_results.get('status')}")
    except Exception as e:
        log.error(f"Cap calc error: {e}", exc_info=True); st.error(f"Cap calc error: {e}")
        cap_results = {"status": "CRITICAL ERROR", "message": f"Cap calculation failed: {e}"}
elif not cap_logic_available: cap_results = {"status": "NOT FOUND", "message": "cap_logic.py missing."}
elif skid_status != "OK": cap_results = {"status": "SKIPPED", "message": "Skipped due to Skid status."}

# --- Main Area Display ---
st.subheader("📊 Calculation Status")
status_cols = st.columns(3)
with status_cols[0]:
    st.markdown("**Skid Status**"); skid_message = skid_results.get("message", "N/A")
    if skid_status == "OK": st.success(f"✅ OK: {skid_message}")
    elif skid_status in ["ERROR", "OVER", "CRITICAL ERROR"]: st.error(f"❌ {skid_status}: {skid_message}")
    elif skid_status == "INIT": st.info(f"⚪️ {skid_status}: {skid_message}")
    else: st.warning(f"⚠️ {skid_status}: {skid_message}")
with status_cols[1]:
    st.markdown("**Floorboard Status**")
    if floor_results:
        fb_status = floor_results.get("status", "UNKNOWN"); fb_message = floor_results.get("message", "N/A")
        if fb_status == "OK": st.success(f"✅ OK: {fb_message}")
        elif fb_status == "WARNING": st.warning(f"⚠️ WARNING: {fb_message}")
        elif fb_status in ["ERROR", "INPUT ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {fb_status}: {fb_message}")
        else: st.info(f"⚪️ {fb_status}: {fb_message}")
    else: st.info("⚪️ Calculation pending...")
with status_cols[2]:
    st.markdown("**Cap Status**")
    if cap_results:
        cap_status_val = cap_results.get("status", "UNKNOWN"); cap_message = cap_results.get("message", "N/A") # Renamed cap_status to cap_status_val
        if cap_status_val == "OK": st.success(f"✅ OK: {cap_message}")
        elif cap_status_val == "WARNING": st.warning(f"⚠️ WARNING: {cap_message}")
        elif cap_status_val in ["ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {cap_status_val}: {cap_message}")
        else: st.info(f"⚪️ {cap_status_val}: {cap_message}")
    else: st.info("⚪️ Calculation pending...")

st.divider()
st.subheader("📈 Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
def format_metric(value, unit="\"", decimals=2, default="N/A"):
    if value is None or not isinstance(value, (int, float)): return default
    if not math.isfinite(value): return "Calc Err"
    try:
        if abs(value - round(value)) < FLOAT_TOLERANCE: decimals = 0
        return f"{value:.{decimals}f}{unit}"
    except (TypeError, ValueError): return str(value) if value is not None else default

with col1:
    st.markdown("##### 📦 Crate Overall"); st.metric("Overall Width (OD)", format_metric(crate_overall_width))
    st.metric("Overall Length (OD)", format_metric(crate_overall_length)); st.metric("Overall Height (OD)", format_metric(crate_overall_height_external))
    st.metric("Panel Thickness Used", format_metric(panel_thickness))
with col2:
    st.markdown("##### 🔩 Skid Setup"); st.metric("Skid Type", skid_results.get('skid_type', 'N/A'))
    st.metric("Skid Actual W x H", f"{format_metric(skid_results.get('skid_width'))} x {format_metric(skid_results.get('skid_height'))}")
    skid_count_metric = skid_results.get('skid_count'); st.metric("Skid Count", str(skid_count_metric) if skid_count_metric is not None else "N/A")
    spacing_actual_metric = skid_results.get('spacing_actual'); spacing_display = format_metric(spacing_actual_metric) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"
    st.metric("Actual Spacing (C-C)", spacing_display); st.metric("Max Allowed Spacing", format_metric(skid_results.get('max_spacing')))
    overall_skid_span_metric = None
    if skid_status == "OK":
        if floorboard_logic_available: overall_skid_span_metric = calculate_overall_skid_span(skid_results)
        else:
             skid_w_m = skid_results.get('skid_width'); pos_m = skid_results.get('skid_positions', [])
             if skid_count_metric == 1 and skid_w_m is not None: overall_skid_span_metric = skid_w_m
             elif skid_count_metric > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_count_metric:
                 overall_skid_span_metric = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
    st.metric("Overall Skid Span", format_metric(overall_skid_span_metric), help="Outer edge to outer edge of skids.")
with col3:
    st.markdown("##### 🪵 Floorboard Summary")
    if floor_results and floor_results.get('status') not in ["NOT FOUND", "INPUT ERROR", "CRITICAL ERROR", "SKIPPED"]:
        fb_boards = floor_results.get("floorboards", []); fb_board_counts = floor_results.get("board_counts", {})
        st.metric("Total Boards", len(fb_boards) if fb_boards else "N/A"); st.metric("Board Length", format_metric(floor_results.get("floorboard_length_across_skids")), help="= Overall Skid Span")
        st.metric("Target Span (Layout)", format_metric(floor_results.get("target_span_along_length")), help="Product Length + 2x Clearance Side")
        gap_val = floor_results.get("center_gap"); gap_disp = f"⚠️ {gap_val:.3f}\"" if floor_results.get("status") == "WARNING" and gap_val is not None else format_metric(gap_val, decimals=3)
        st.metric("Center Gap", gap_disp); st.metric("Custom Narrow Used", format_metric(floor_results.get("custom_board_width"), decimals=3) if floor_results.get("narrow_board_used") else "Not Used")
        counts_str = ", ".join([f"{nom}: {cnt}" for nom, cnt in sorted(fb_board_counts.items())]); st.markdown(f"**Counts:** {counts_str if counts_str else 'None'}")
        fb_calc_span = floor_results.get("calculated_span_covered"); fb_target_span_check = floor_results.get("target_span_along_length")
        if fb_calc_span is not None and fb_target_span_check is not None:
             tol_check = FLOORBOARD_FLOAT_TOLERANCE if floorboard_logic_available else FLOAT_TOLERANCE
             if math.isclose(fb_calc_span, fb_target_span_check, abs_tol=tol_check * 10): st.success(f"Span Check: OK")
             else: st.error(f"Span Check FAIL: Calc={fb_calc_span:.3f}\" vs Target={fb_target_span_check:.3f}\""); log.error(f"Floorboard span check FAIL: Calc={fb_calc_span}, Target={fb_target_span_check}")
        else: st.caption("Span Check Pending")
    else: st.caption("No floorboard data to display.")
with col4:
    st.markdown("##### 🧢 Cap Summary")
    if cap_results and cap_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
        st.metric("Panel W x L", f"{format_metric(cap_results.get('cap_panel_width'))} x {format_metric(cap_results.get('cap_panel_length'))}")
        st.metric("Panel Thickness", format_metric(cap_results.get("cap_panel_thickness")))
        lc = cap_results.get("longitudinal_cleats", {}); tc = cap_results.get("transverse_cleats", {}); cs = cap_results.get("cap_cleat_spec", {})
        cleat_spec_disp = f"{cs.get('thickness', 'N/A'):.2f}x{cs.get('width', 'N/A'):.2f}\" (act.)"; st.metric("Cleat Lumber Spec", cleat_spec_disp)
        st.metric("Long. Cleats (Count)", str(lc.get("count", "N/A"))); st.metric("Long. Spacing (C-C)", format_metric(lc.get("actual_spacing")))
        st.metric("Trans. Cleats (Count)", str(tc.get("count", "N/A"))); st.metric("Trans. Spacing (C-C)", format_metric(tc.get("actual_spacing")))
        st.metric("Max Cleat Spacing Used", format_metric(cap_results.get("max_allowed_cleat_spacing_used")))
    else: st.caption("No cap data to display.")

st.divider()
st.header("📐 Layout Visualizations")

# --- Skid Visualization ---
st.subheader("Skid Layout (Top-Down View)")
skid_fig = go.Figure(); skid_plot_generated = False; skid_plot_error = None
if skid_status == "OK":
    try:
        skid_w_viz = skid_results.get('skid_width'); skid_count_viz = skid_results.get('skid_count'); positions_viz = skid_results.get('skid_positions'); spacing_viz = skid_results.get('spacing_actual'); max_spacing_viz = skid_results.get('max_spacing'); skid_h_viz = skid_results.get('skid_height', 3.5)
        tol_viz = SKID_FLOAT_TOLERANCE if 'SKID_FLOAT_TOLERANCE' in globals() else FLOAT_TOLERANCE
        if (skid_w_viz is not None and skid_w_viz > tol_viz and skid_count_viz is not None and skid_count_viz > 0 and positions_viz is not None and len(positions_viz) == skid_count_viz):
            SKID_COLOR = "#8B4513"; SKID_OUTLINE_COLOR = "#654321"; FONT_S, FONT_M, FONT_L = 10, 11, 13; SPACING_COLOR = "purple"
            viz_skid_h_display = max(skid_h_viz * 0.5, skid_w_viz * 0.5, 5.0); y_center, y_bottom, y_top = 0, -viz_skid_h_display / 2, viz_skid_h_display / 2; y_padding = viz_skid_h_display * 1.2
            for i, pos in enumerate(positions_viz):
                x0, x1 = pos - skid_w_viz / 2, pos + skid_w_viz / 2
                skid_fig.add_shape(type="rect", x0=x0, y0=y_bottom, x1=x1, y1=y_top, fillcolor=SKID_COLOR, line=dict(color=SKID_OUTLINE_COLOR, width=1.5), name=f"Skid {i+1}")
                skid_fig.add_annotation(x=pos, y=y_top, text=f"<b>Skid {i+1}</b>", showarrow=False, font=dict(size=FONT_M, color="white"), yshift=15)
                skid_fig.add_annotation(x=pos, y=y_bottom, text=f'{pos:.2f}"', showarrow=False, font=dict(size=FONT_S, color="white"), yshift=-15)
            skid_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Skids', marker=dict(color=SKID_COLOR, size=10, symbol='square', line=dict(color=SKID_OUTLINE_COLOR, width=1))))
            if skid_count_viz > 1 and spacing_viz is not None and max_spacing_viz is not None:
                 y_spacing_ann = y_bottom - y_padding * 0.4
                 for i in range(skid_count_viz - 1):
                     mid_x = (positions_viz[i] + positions_viz[i+1]) / 2
                     skid_fig.add_annotation(x=mid_x, y=y_spacing_ann, text=f'↔ {spacing_viz:.2f}"<br>(Max: {max_spacing_viz:.2f}")', showarrow=False, align="center", font=dict(color=SPACING_COLOR, size=FONT_S), yshift=-10)
            overall_skid_span_viz = overall_skid_span_metric
            if overall_skid_span_viz is not None and overall_skid_span_viz > tol_viz:
                 y_top_ann = y_top + y_padding * 0.6; plot_center_x = 0
                 skid_fig.add_annotation(x=plot_center_x, y=y_top_ann, text=f'<b>Overall Skid Span: {overall_skid_span_viz:.2f}"</b>', showarrow=False, font=dict(color="black", size=FONT_L), yshift=10)
            min_x_pos = positions_viz[0] - skid_w_viz / 2; max_x_pos = positions_viz[-1] + skid_w_viz / 2; x_padding_viz = max(skid_w_viz * 1.5, (max_x_pos - min_x_pos) * 0.15, 10.0)
            x_range = [min_x_pos - x_padding_viz, max_x_pos + x_padding_viz]; y_extent = y_padding * 1.5; y_range = [y_center - y_extent, y_center + y_extent]
            skid_fig.update_layout(xaxis_title=f"Crate Width Direction ({crate_overall_width:.2f}\" OD)", yaxis_title=None,
                                   xaxis=dict(range=x_range, showline=False, showgrid=False, showticklabels=False, zeroline=False, fixedrange=True),
                                   yaxis=dict(range=y_range, showline=False, showgrid=False, showticklabels=False, zeroline=False, fixedrange=True),
                                   plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=10, r=10, t=30, b=10),
                                   showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=300, autosize=True)
            skid_plot_generated = True
        else: skid_plot_error = "Missing/invalid skid data."; log.warning(skid_plot_error)
    except Exception as e: skid_plot_error = f"Skid viz error: {e}"; log.error(skid_plot_error, exc_info=True)
if skid_plot_generated: st.plotly_chart(skid_fig, use_container_width=True)
elif skid_plot_error: st.warning(f"⚠️ {skid_plot_error}")
elif skid_status != "OK": st.info("Skid viz needs 'OK' status.")
else: st.info("Enter params for skid viz.")

# --- Floorboard Visualization ---
st.divider(); st.subheader("Floorboard Layout (Top-Down View)")
floorboard_plot_generated = False; floorboard_plot_error = None
fb_tol_viz = FLOORBOARD_FLOAT_TOLERANCE if floorboard_logic_available else FLOAT_TOLERANCE
if floorboard_logic_available:
    if floor_results and floor_results.get('status') in ["OK", "WARNING"]:
        fb_boards_viz = floor_results.get("floorboards", []); fb_target_span_viz = floor_results.get("target_span_along_length", 0.0); fb_center_gap_viz = floor_results.get("center_gap", 0.0); fb_length_across_skids_viz = floor_results.get("floorboard_length_across_skids", 0.0)
        if fb_boards_viz and fb_length_across_skids_viz > fb_tol_viz and fb_target_span_viz > fb_tol_viz:
            try:
                fb_fig = go.Figure(); NORMAL_BOARD_COLOR = "#D2B48C"; CUSTOM_BOARD_COLOR = "#8B4513"; GAP_COLOR = "rgba(173, 216, 230, 0.7)"; BOARD_OUTLINE_COLOR = "#A0522D"; ANNOTATION_COLOR_DARK = "black"; ANNOTATION_COLOR_LIGHT = "white"; ANNOTATION_SIZE = 9
                x_center_fb = 0; x_start_fb = x_center_fb - fb_length_across_skids_viz / 2.0; x_end_fb = x_center_fb + fb_length_across_skids_viz / 2.0; custom_board_present_fb = False
                for i, board in enumerate(fb_boards_viz):
                    board_width_dim_fb = board.get("actual_width", 0.0); board_start_y_fb = board.get("position", 0.0); board_end_y_fb = board_start_y_fb + board_width_dim_fb; board_nominal_fb = board.get("nominal", "N/A"); board_color_fb = CUSTOM_BOARD_COLOR if board_nominal_fb == "Custom" else NORMAL_BOARD_COLOR
                    if board_nominal_fb == "Custom": custom_board_present_fb = True
                    fb_fig.add_shape(type="rect", x0=x_start_fb, y0=board_start_y_fb, x1=x_end_fb, y1=board_end_y_fb, fillcolor=board_color_fb, line=dict(color=BOARD_OUTLINE_COLOR, width=0.5), name=f"Board {i+1} ({board_nominal_fb})")
                    if board_width_dim_fb > 1.5: text_color_fb = ANNOTATION_COLOR_LIGHT; fb_fig.add_annotation(x=x_center_fb, y=(board_start_y_fb + board_end_y_fb) / 2, text=f'{board_width_dim_fb:.2f}"', showarrow=False, font=dict(color=text_color_fb, size=ANNOTATION_SIZE), align="center")
                if abs(fb_center_gap_viz) > fb_tol_viz:
                    gap_start_y_viz = floor_results.get("calculated_span_covered", fb_target_span_viz) - fb_center_gap_viz; gap_end_y_viz = gap_start_y_viz + fb_center_gap_viz
                    if gap_end_y_viz > gap_start_y_viz + fb_tol_viz:
                        gap_legend_name = f'Center Gap ({fb_center_gap_viz:.3f}")'; gap_bg_color = "rgba(173, 216, 230, 0.7)"
                        fb_fig.add_shape(type="rect", x0=x_start_fb, y0=gap_start_y_viz, x1=x_end_fb, y1=gap_end_y_viz, fillcolor=GAP_COLOR, line_width=0, opacity=0.7, name="Center Gap")
                        fb_fig.add_annotation(x=x_center_fb, y=(gap_start_y_viz + gap_end_y_viz) / 2, text=f"Gap:\n{fb_center_gap_viz:.3f}\"", showarrow=False, font=dict(color=ANNOTATION_COLOR_DARK, size=8), bgcolor=gap_bg_color)
                        fb_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=gap_legend_name, marker=dict(color=GAP_COLOR, size=10, symbol='square', opacity=0.7)))
                fb_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Std Boards', marker=dict(color=NORMAL_BOARD_COLOR, size=10, symbol='square', line=dict(color=BOARD_OUTLINE_COLOR, width=1))))
                if custom_board_present_fb: fb_fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name='Custom Board', marker=dict(color=CUSTOM_BOARD_COLOR, size=10, symbol='square', line=dict(color=BOARD_OUTLINE_COLOR, width=1))))
                y_padding_fb = max(5, fb_target_span_viz*0.05); x_padding_fb = max(5, fb_length_across_skids_viz*0.05)
                fb_fig.update_layout(xaxis_title=f"Floorboard Length ({fb_length_across_skids_viz:.2f}\")", yaxis_title=f"Board Width Layout (Target: {fb_target_span_viz:.2f}\")",
                                     xaxis=dict(range=[x_start_fb-x_padding_fb, x_end_fb+x_padding_fb], zeroline=False, showgrid=False), yaxis=dict(range=[0-y_padding_fb, fb_target_span_viz+y_padding_fb], zeroline=False, showgrid=False),
                                     plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=10,r=10,t=40,b=10), showlegend=True, legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1), height=600)
                floorboard_plot_generated = True
            except Exception as e: floorboard_plot_error = f"FB viz error: {e}"; log.error(floorboard_plot_error, exc_info=True)
        if floorboard_plot_generated: st.plotly_chart(fb_fig, use_container_width=True)
        elif floorboard_plot_error: st.warning(f"⚠️ {floorboard_plot_error}")
        else: st.info("FB viz needs valid boards & positive dims.")
    elif floor_results: st.info(f"No FB layout: {floor_results.get('message', 'Status: '+floor_results.get('status','N/A'))}")
    elif skid_status != "OK": st.info("FB layout needs OK skid status.")
else: st.warning("Floorboard logic not available.")

# --- Cap Visualization ---
st.divider()
st.subheader("Cap Layout Views")
cap_tol_viz = CAP_FLOAT_TOLERANCE if cap_logic_available else FLOAT_TOLERANCE
CAP_PANEL_COLOR = "#E0E0E0"; CAP_CLEAT_COLOR = "#A0522D"; OUTLINE_COLOR = "#505050"
CLEAT_FONT_COLOR = "white"; DIM_ANNOT_COLOR = "darkblue"

def create_cap_ortho_view(view_type="front", cap_data=None):
    if not cap_data or cap_data.get("status") not in ["OK", "WARNING"]:
        return go.Figure(), "Cap data not available or not valid for view."
    fig = go.Figure()
    panel_w = cap_data.get("cap_panel_width", 0)
    panel_l = cap_data.get("cap_panel_length", 0)
    panel_t = cap_data.get("cap_panel_thickness", 0)
    cleat_spec = cap_data.get("cap_cleat_spec", {})
    cleat_t = cleat_spec.get("thickness", DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS)
    cap_total_height = panel_t + cleat_t

    if view_type == "front":
        dim_across = panel_w; dim_label_across = "Cap Width"
        cleats_on_top_profiles = cap_data.get("longitudinal_cleats", {})
    elif view_type == "side":
        dim_across = panel_l; dim_label_across = "Cap Length"
        cleats_on_top_profiles = cap_data.get("transverse_cleats", {})
    else: return go.Figure(), "Invalid view type for ortho."

    if dim_across <= cap_tol_viz or panel_t <= cap_tol_viz: return go.Figure(), f"{dim_label_across} or panel thickness is zero."

    fig.add_shape(type="rect", x0=0, y0=0, x1=dim_across, y1=panel_t, fillcolor=CAP_PANEL_COLOR, line=dict(color=OUTLINE_COLOR, width=1), name="Panel Sheathing")
    if cleats_on_top_profiles.get("count", 0) > 0:
        cleat_profile_width = cleats_on_top_profiles.get("cleat_width_each", 0)
        cleat_positions_relative_to_center = cleats_on_top_profiles.get("positions", [])
        cleat_positions_view_x = [pos + dim_across / 2 for pos in cleat_positions_relative_to_center]
        for x_center_profile in cleat_positions_view_x:
            x0_profile = x_center_profile - cleat_profile_width / 2; x1_profile = x_center_profile + cleat_profile_width / 2
            fig.add_shape(type="rect", x0=x0_profile, y0=panel_t, x1=x1_profile, y1=panel_t + cleat_t, fillcolor=CAP_CLEAT_COLOR, line=dict(color=OUTLINE_COLOR, width=1))
            if cleat_profile_width > 0.5 and cleat_t > 0.5:
                fig.add_annotation(x=(x0_profile + x1_profile)/2, y=panel_t + cleat_t/2, text=f"{cleat_profile_width:.1f}\"W", showarrow=False, font=dict(color=CLEAT_FONT_COLOR, size=8))
    # Simplified representation of cleats running across the view (typically end cleats)
    fig.add_shape(type="rect", x0=0, y0=panel_t, x1=dim_across, y1=panel_t + cleat_t, fillcolor=CAP_CLEAT_COLOR, line=dict(color=OUTLINE_COLOR, width=1), layer="above", name="End Cleat (Full)")

    fig.update_layout(title=f"Cap Assembly - {view_type.capitalize()} View", xaxis_title=f"{dim_label_across} ({dim_across:.2f}\")", yaxis_title=f"Cap Height ({cap_total_height:.2f}\")",
                      xaxis=dict(range=[-dim_across*0.05, dim_across*1.05], showgrid=True, zeroline=True),
                      yaxis=dict(range=[-cap_total_height*0.1, cap_total_height*1.1], showgrid=True, zeroline=True, scaleanchor="x", scaleratio=1),
                      plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=20, r=20, t=50, b=20), height=350,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.add_trace(go.Scatter(x=[None],y=[None],mode='markers',name='Panel', marker=dict(color=CAP_PANEL_COLOR,size=10)))
    fig.add_trace(go.Scatter(x=[None],y=[None],mode='markers',name='Cleat', marker=dict(color=CAP_CLEAT_COLOR,size=10)))
    return fig, None

cap_view_tabs = st.tabs(["Top View", "Front View", "Side View"])
with cap_view_tabs[0]:
    st.markdown("#### Top-Down View")
    cap_plot_generated_top = False; cap_plot_error_top = None
    if cap_logic_available and cap_results and cap_results.get("status") in ["OK", "WARNING"]:
        try:
            cap_panel_w_top = cap_results.get("cap_panel_width",0); cap_panel_l_top = cap_results.get("cap_panel_length",0)
            long_cleats_data_top = cap_results.get("longitudinal_cleats",{}); trans_cleats_data_top = cap_results.get("transverse_cleats",{})
            if cap_panel_w_top > cap_tol_viz and cap_panel_l_top > cap_tol_viz:
                cap_fig_top = go.Figure()
                panel_x0_top, panel_y0_top, panel_x1_top, panel_y1_top = -cap_panel_w_top/2, -cap_panel_l_top/2, cap_panel_w_top/2, cap_panel_l_top/2
                cap_fig_top.add_shape(type="rect", x0=panel_x0_top, y0=panel_y0_top, x1=panel_x1_top, y1=panel_y1_top, fillcolor=CAP_PANEL_COLOR, line=dict(color=OUTLINE_COLOR,width=1), name="Cap Panel")
                cap_fig_top.add_trace(go.Scatter(x=[None],y=[None],mode='markers',name='Panel Sheathing', marker=dict(color=CAP_PANEL_COLOR,size=10,symbol='square',line=dict(color=OUTLINE_COLOR,width=1))))
                if long_cleats_data_top.get("count",0) > 0:
                    lc_w_top = long_cleats_data_top.get("cleat_width_each",0); lc_l_top = long_cleats_data_top.get("cleat_length_each",0); lc_positions_x_top = long_cleats_data_top.get("positions",[])
                    for i,x_center_top in enumerate(lc_positions_x_top):
                        cleat_x0_top,cleat_x1_top,cleat_y0_top,cleat_y1_top = x_center_top-lc_w_top/2, x_center_top+lc_w_top/2, -lc_l_top/2, lc_l_top/2
                        cap_fig_top.add_shape(type="rect",x0=cleat_x0_top,y0=cleat_y0_top,x1=cleat_x1_top,y1=cleat_y1_top,fillcolor=CAP_CLEAT_COLOR,line=dict(color=OUTLINE_COLOR,width=1))
                        if lc_w_top > 1.0 and lc_l_top > 1.0: cap_fig_top.add_annotation(x=x_center_top,y=0,text=f'{lc_w_top:.1f}"',showarrow=False,font=dict(color=CLEAT_FONT_COLOR,size=8))
                    if len(lc_positions_x_top)>1:
                        lc_spacing_top = long_cleats_data_top.get("actual_spacing",0); y_pos_spacing_ann_top = panel_y1_top*0.8
                        for i in range(len(lc_positions_x_top)-1): mid_x_spacing_top=(lc_positions_x_top[i]+lc_positions_x_top[i+1])/2; cap_fig_top.add_annotation(x=mid_x_spacing_top,y=y_pos_spacing_ann_top,text=f'↔{lc_spacing_top:.1f}"',showarrow=False,font=dict(color=DIM_ANNOT_COLOR,size=9),bgcolor="rgba(255,255,255,0.6)")
                if trans_cleats_data_top.get("count",0) > 0:
                    tc_w_top = trans_cleats_data_top.get("cleat_width_each",0); tc_l_top = trans_cleats_data_top.get("cleat_length_each",0); tc_positions_y_top = trans_cleats_data_top.get("positions",[])
                    for i,y_center_top in enumerate(tc_positions_y_top):
                        cleat_x0_top,cleat_x1_top,cleat_y0_top,cleat_y1_top = -tc_l_top/2, tc_l_top/2, y_center_top-tc_w_top/2, y_center_top+tc_w_top/2
                        cap_fig_top.add_shape(type="rect",x0=cleat_x0_top,y0=cleat_y0_top,x1=cleat_x1_top,y1=cleat_y1_top,fillcolor=CAP_CLEAT_COLOR,line=dict(color=OUTLINE_COLOR,width=1))
                        if tc_w_top > 1.0 and tc_l_top > 1.0: cap_fig_top.add_annotation(x=0,y=y_center_top,text=f'{tc_w_top:.1f}"',showarrow=False,font=dict(color=CLEAT_FONT_COLOR,size=8))
                    if len(tc_positions_y_top)>1:
                        tc_spacing_top = trans_cleats_data_top.get("actual_spacing",0); x_pos_spacing_ann_top = panel_x1_top*0.8
                        for i in range(len(tc_positions_y_top)-1): mid_y_spacing_top=(tc_positions_y_top[i]+tc_positions_y_top[i+1])/2; cap_fig_top.add_annotation(x=x_pos_spacing_ann_top,y=mid_y_spacing_top,text=f'↕{tc_spacing_top:.1f}"',showarrow=False,font=dict(color=DIM_ANNOT_COLOR,size=9),bgcolor="rgba(255,255,255,0.6)")
                if long_cleats_data_top.get("count",0)>0 or trans_cleats_data_top.get("count",0)>0: cap_fig_top.add_trace(go.Scatter(x=[None],y=[None],mode='markers',name='Cleats',marker=dict(color=CAP_CLEAT_COLOR,size=10,symbol='square',line=dict(color=OUTLINE_COLOR,width=1))))
                cap_fig_top.add_annotation(x=0,y=panel_y1_top,text=f'<b>Panel L: {cap_panel_l_top:.2f}"</b>',showarrow=False,yshift=20,font=dict(color=DIM_ANNOT_COLOR,size=11))
                cap_fig_top.add_annotation(x=panel_x1_top,y=0,text=f'<b>Panel W: {cap_panel_w_top:.2f}"</b>',showarrow=False,xshift=40,textangle=-90,font=dict(color=DIM_ANNOT_COLOR,size=11))
                padding_factor_top=0.15; width_extent_top=cap_panel_w_top*(1+padding_factor_top); length_extent_top=cap_panel_l_top*(1+padding_factor_top); axis_max_top=max(width_extent_top/2,length_extent_top/2)
                cap_fig_top.update_layout(title="Cap Assembly - Top View", xaxis_title=None,yaxis_title=None,xaxis=dict(range=[-axis_max_top,axis_max_top],zeroline=True,showgrid=True,showticklabels=False),yaxis=dict(range=[-axis_max_top,axis_max_top],zeroline=True,showgrid=True,showticklabels=False,scaleanchor="x",scaleratio=1),
                                      plot_bgcolor='white',paper_bgcolor='white',margin=dict(l=20,r=20,t=60,b=20),showlegend=True,legend=dict(orientation="h",yanchor="bottom",y=1.05,xanchor="right",x=1),height=550)
                cap_plot_generated_top = True
            else: cap_plot_error_top = "Cap panel dims invalid."
        except Exception as e: cap_plot_error_top = f"Cap Top viz error: {e}"; log.error(cap_plot_error_top, exc_info=True)
    if cap_plot_generated_top: st.plotly_chart(cap_fig_top, use_container_width=True)
    elif cap_plot_error_top: st.warning(f"⚠️ {cap_plot_error_top}")
    elif not cap_logic_available: st.info("Cap logic not loaded.")
    elif not cap_results or cap_results.get("status") not in ["OK","WARNING"]: st.info(f"Cap Top viz needs OK/Warning. Got: {cap_results.get('status') if cap_results else 'N/A'}")
    else: st.info("Enter params for cap Top viz.")
with cap_view_tabs[1]:
    st.markdown("#### Front View (Along Width)")
    fig_front, error_front = create_cap_ortho_view(view_type="front", cap_data=cap_results)
    if error_front: st.info(error_front)
    else: st.plotly_chart(fig_front, use_container_width=True)
with cap_view_tabs[2]:
    st.markdown("#### Side View (Along Length)")
    fig_side, error_side = create_cap_ortho_view(view_type="side", cap_data=cap_results)
    if error_side: st.info(error_side)
    else: st.plotly_chart(fig_side, use_container_width=True)

# --- Details Tables ---
st.divider(); st.subheader("📋 Component Details")
with st.expander("Floorboard Details", expanded=False):
    if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
        fb_boards_table = floor_results.get("floorboards", []); board_data_table = [ {"Board #": i+1, "Nominal Size": b.get("nominal", "N/A"), "Width (in)": b.get("actual_width", 0.0), "Position Start (in)": b.get("position", 0.0)} for i, b in enumerate(fb_boards_table) ]
        df_boards_table = pd.DataFrame(board_data_table); st.dataframe( df_boards_table, use_container_width=True, hide_index=True, column_config={"Width (in)": st.column_config.NumberColumn(format="%.3f"), "Position Start (in)": st.column_config.NumberColumn(format="%.3f")} )
    else: st.caption("No floorboard details available.")
with st.expander("Cap Cleat Details", expanded=False):
    if cap_results and cap_results.get("status") in ["OK", "WARNING"]:
        cap_details_data = []; lc_data = cap_results.get("longitudinal_cleats",{}); tc_data = cap_results.get("transverse_cleats",{})
        if lc_data.get("count",0)>0:
            for i,pos_x in enumerate(lc_data.get("positions",[])): cap_details_data.append({"Type":"Longitudinal","Cleat #":i+1,"Length (in)":lc_data.get("cleat_length_each"),"Width (in)":lc_data.get("cleat_width_each"),"Thickness (in)":lc_data.get("cleat_thickness_each"),"Center Position (X)":pos_x,"Center Position (Y)":"N/A"})
        if tc_data.get("count",0)>0:
            for i,pos_y in enumerate(tc_data.get("positions",[])): cap_details_data.append({"Type":"Transverse","Cleat #":i+1,"Length (in)":tc_data.get("cleat_length_each"),"Width (in)":tc_data.get("cleat_width_each"),"Thickness (in)":tc_data.get("cleat_thickness_each"),"Center Position (X)":"N/A","Center Position (Y)":pos_y})
        if cap_details_data:
            df_cap_details = pd.DataFrame(cap_details_data); st.dataframe(df_cap_details,use_container_width=True,hide_index=True,column_config={"Length (in)":st.column_config.NumberColumn(format="%.2f"),"Width (in)":st.column_config.NumberColumn(format="%.2f"),"Thickness (in)":st.column_config.NumberColumn(format="%.2f"),"Center Position (X)":st.column_config.NumberColumn(format="%.2f"),"Center Position (Y)":st.column_config.NumberColumn(format="%.2f")})
        else: st.caption("No cap cleat details.")
    else: st.caption("No cap cleat details available.")

# --- Footer ---
st.sidebar.divider()
st.sidebar.info("AutoCrate Wizard v0.4.3\nFor inquiries, contact Shivam Bhardwaj.")
