# wizard_app/app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid, Floorboard & Cap Layout System.
Version 0.4.14 - Added autoscaling for plots and explanation expanders.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import logging
import math
from collections import Counter
import sys
import os

# --- Path Setup for Direct Execution ---
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    __package__ = "wizard_app"

# --- Setup Logging ---
log = logging.getLogger("wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Import Configuration and Logic Modules ---
try:
    from . import config
    from . import skid_logic
    from . import floorboard_logic
    from . import cap_logic
    from . import wall_logic

    floorboard_logic_available = hasattr(floorboard_logic, 'calculate_floorboard_layout')
    cap_logic_available = hasattr(cap_logic, 'calculate_cap_layout')
    wall_logic_available = hasattr(wall_logic, 'calculate_wall_panels')

    log.info("Successfully imported config and logic modules using relative imports.")

except ImportError as e:
    try:
        log.warning(f"Relative import failed: {e}. Attempting direct import as fallback.")
        import config, skid_logic, floorboard_logic, cap_logic, wall_logic
        floorboard_logic_available = hasattr(floorboard_logic, 'calculate_floorboard_layout')
        cap_logic_available = hasattr(cap_logic, 'calculate_cap_layout')
        wall_logic_available = hasattr(wall_logic, 'calculate_wall_panels')
        log.info("Successfully imported config and logic modules using direct imports as fallback.")
    except ImportError as e_fallback:
        log.error(f"Fatal Error: Could not import modules. Relative import error: {e}. Direct import error: {e_fallback}. ", exc_info=True)
        st.error(f"Fatal Error: Could not import critical modules. \n\nOriginal error: {e}\nFallback error: {e_fallback}")
        st.stop()


# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="AutoCrate Wizard", page_icon="⚙️")
st.title("⚙️ AutoCrate Wizard - Parametric Crate Layout System")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts (Base, Floor, Walls, Top).")
st.divider()

# --- Caching Wrappers for Logic Functions ---
@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness):
    log.info("CACHE MISS or RECALC: cached_calculate_skid_layout")
    return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)

@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow):
    skid_results = dict(skid_results_tuple) if isinstance(skid_results_tuple, tuple) else skid_results_tuple
    selected_nominal_sizes = list(selected_nominal_sizes_tuple)
    log.info("CACHE MISS or RECALC: cached_calculate_floorboard_layout")
    if not floorboard_logic_available: return {"status": "NOT FOUND", "message": "floorboard_logic.py missing."}
    return floorboard_logic.calculate_floorboard_layout(skid_results, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)

@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.info("CACHE MISS or RECALC: cached_calculate_cap_layout")
    if not cap_logic_available: return {"status": "NOT FOUND", "message": "cap_logic.py missing."}
    return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)

@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width):
    log.info("CACHE MISS or RECALC: cached_calculate_wall_panels")
    if not wall_logic_available: return {"status": "NOT FOUND", "message": "wall_logic.py missing."}
    return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width)


# --- Helper Function for Combined Slider/Number Input ---
def input_slider_combo(label, min_val, max_val, default_val, step, format_str="%.1f", help_text=""):
    """Creates a slider with a number input box for precise entry."""
    state_key_slider = f"{label}_slider"
    state_key_num = f"{label}_num"
    safe_default = max(min_val, min(max_val, default_val))
    if state_key_slider not in st.session_state: st.session_state[state_key_slider] = safe_default
    if state_key_num not in st.session_state: st.session_state[state_key_num] = safe_default
    if not (min_val <= st.session_state[state_key_slider] <= max_val): st.session_state[state_key_slider] = safe_default
    if not (min_val <= st.session_state[state_key_num] <= max_val): st.session_state[state_key_num] = safe_default
    col1, col2 = st.columns([3, 1])
    with col1:
        new_slider_val = st.slider(label, min_val, max_val, st.session_state[state_key_slider], step, format=format_str, help=help_text, key=f"sl_{label}")
        if new_slider_val != st.session_state[state_key_slider]: st.session_state[state_key_slider] = new_slider_val; st.session_state[state_key_num] = new_slider_val; st.rerun()
    with col2:
        new_num_val = st.number_input("Value", min_value=min_val, max_value=max_val, value=st.session_state[state_key_num], step=step, format=format_str, label_visibility="collapsed", key=f"ni_{label}")
        if new_num_val != st.session_state[state_key_num]: st.session_state[state_key_num] = new_num_val; st.session_state[state_key_slider] = new_num_val; st.rerun()
    return st.session_state[state_key_slider]


# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Product & Crate Parameters")
    product_weight = st.number_input("Product Weight (lbs)", min_value=1.0, max_value=20000.0, value=1500.0, step=10.0, format="%.1f", help="Enter exact product weight.")
    st.caption("Skid type/spacing rules apply based on weight.")
    product_width_input = input_slider_combo("Product Width (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ACROSS skids.")
    product_length_input = input_slider_combo("Product Length (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ALONG skids.")
    product_actual_height = input_slider_combo("Product Actual Height (in)", 1.0, 120.0, 48.0, 0.5, "%.1f", "Actual height of the product itself.")
    st.subheader("Crate Construction Constants")
    clearance_side_product = st.number_input("Clearance Side (Product W/L) (in)", 0.0, value=2.0, step=0.1, format="%.2f")
    clearance_above_product_ui = st.number_input("Clearance Above Product (to Top Panel) (in)", 0.0, value=config.DEFAULT_CLEARANCE_ABOVE_PRODUCT, step=0.1, format="%.2f")
    panel_thickness_ui = st.number_input("Panel Thickness (Wall/Floor/Top) (in)", 0.01, value=config.DEFAULT_PANEL_THICKNESS_UI, step=0.01, format="%.2f", help="Used for floor, top, and wall panels.")
    wall_cleat_thickness_ui = st.number_input("Wall Cleat Actual Thickness (in)", 0.01, value=config.DEFAULT_CLEAT_NOMINAL_THICKNESS, step=0.01, format="%.2f", help="Thickness of side/end wall framing cleats.")
    wall_cleat_width_ui = st.number_input("Wall Cleat Actual Width (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_WIDTH, step=0.1, format="%.1f", help="Width of side/end wall framing cleats.")
    st.subheader("Floorboard Options")
    selected_ui_options = st.multiselect("Available Floorboard Lumber", options=config.ALL_LUMBER_OPTIONS_UI, default=config.DEFAULT_UI_LUMBER_SELECTION_APP)
    selected_nominal_sizes_tuple_for_cache = tuple(sorted([opt for opt in selected_ui_options if opt != config.CUSTOM_NARROW_OPTION_TEXT_UI]))
    allow_custom_narrow = config.CUSTOM_NARROW_OPTION_TEXT_UI in selected_ui_options
    st.subheader("Top Panel Options")
    cap_cleat_actual_thk_ui = st.number_input("Top Panel Cleat Actual Thickness (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_THICKNESS, step=0.01, format="%.2f", help="Actual thickness of the top panel cleat lumber (defaults to wall cleat thickness).")
    cap_cleat_actual_width_ui = st.number_input("Top Panel Cleat Actual Width (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_WIDTH, step=0.1, format="%.1f", help="Actual width of the top panel cleat lumber (defaults to wall cleat width).")
    max_top_cleat_spacing_ui = st.number_input("Max Top Panel Cleat Spacing (C-C, in)", 1.0, value=24.0, step=1.0, format="%.1f")

# --- Core Logic Execution ---
log.info(f"UI Inputs: Wgt={product_weight}, ProdW={product_width_input}, ProdL={product_length_input}, ProdH={product_actual_height}, ClrSide={clearance_side_product}, ClrAbove={clearance_above_product_ui}, PnlThk={panel_thickness_ui}, WallCleatThk={wall_cleat_thickness_ui}, WallCleatW={wall_cleat_width_ui}, MaxCapCleatSpace={max_top_cleat_spacing_ui}")
skid_results = {}; skid_status = "NOT RUN"
try: skid_results = cached_calculate_skid_layout(product_weight, product_width_input, clearance_side_product, panel_thickness_ui, wall_cleat_thickness_ui); skid_status = skid_results.get("status", "UNKNOWN"); log.info(f"Skid calculation status: {skid_status}")
except Exception as e: log.error(f"Skid calculation error: {e}", exc_info=True); st.error(f"Skid calc error: {e}"); skid_results = {"status": "CRITICAL ERROR", "message": f"Skid calculation failed: {e}"}; skid_status = "CRITICAL ERROR"
skid_results_tuple_for_cache = tuple(sorted(skid_results.items())) if isinstance(skid_results, dict) else skid_results
crate_overall_width = skid_results.get('crate_width', 0.0)
crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
skid_actual_height = skid_results.get('skid_height', 0.0)
crate_internal_clear_height = product_actual_height + clearance_above_product_ui
wall_panel_height_calc = crate_internal_clear_height
crate_overall_height_external = (skid_actual_height + panel_thickness_ui + wall_panel_height_calc + panel_thickness_ui + cap_cleat_actual_thk_ui)
log.info(f"Calculated ODs: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, H={crate_overall_height_external:.2f}")
log.info(f"Calculated Wall Panel Height: {wall_panel_height_calc:.2f}")
floor_results = None
if floorboard_logic_available:
    if skid_status == "OK":
        selected_nominal_sizes_for_logic = list(selected_nominal_sizes_tuple_for_cache)
        if not selected_nominal_sizes_for_logic and not allow_custom_narrow: floor_results = {"status": "INPUT ERROR", "message": "No standard lumber selected AND custom narrow not allowed."}
        else:
            try: floor_results = cached_calculate_floorboard_layout(skid_results_tuple_for_cache, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow); log.info(f"Floorboard status: {floor_results.get('status')}")
            except Exception as e: log.error(f"Floorboard calc error: {e}", exc_info=True); st.error(f"Floorboard calc error: {e}"); floor_results = {"status": "CRITICAL ERROR", "message": f"Floorboard calculation failed: {e}"}
    elif skid_status != "OK": floor_results = {"status": "SKIPPED", "message": "Skipped due to Skid status."}
else: floor_results = {"status": "NOT FOUND", "message": "floorboard_logic.py missing."}
top_panel_results = None
if cap_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE:
        try: top_panel_results = cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui); log.info(f"Top Panel status: {top_panel_results.get('status')}")
        except Exception as e: log.error(f"Top Panel calc error: {e}", exc_info=True); st.error(f"Top Panel calc error: {e}"); top_panel_results = {"status": "CRITICAL ERROR", "message": f"Top Panel calculation failed: {e}"}
    elif skid_status != "OK": top_panel_results = {"status": "SKIPPED", "message": "Skipped due to Skid status."}
    else: top_panel_results = {"status": "SKIPPED", "message": "Skipped due to invalid crate dimensions."}
else: top_panel_results = {"status": "NOT FOUND", "message": "cap_logic.py missing."}
wall_results = None
if wall_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE and wall_panel_height_calc > config.FLOAT_TOLERANCE:
         try: wall_results = cached_calculate_wall_panels(crate_overall_width, crate_overall_length, wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui); log.info(f"Wall panel status: {wall_results.get('status')}")
         except Exception as e: log.error(f"Wall panel calc error: {e}", exc_info=True); st.error(f"Wall panel calc error: {e}"); wall_results = {"status": "CRITICAL ERROR", "message": f"Wall panel calculation failed: {e}"}
    elif skid_status != "OK": wall_results = {"status": "SKIPPED", "message": "Skipped due to Skid status."}
    else: wall_results = {"status": "SKIPPED", "message": "Skipped due to invalid crate dimensions for walls."}
else: wall_results = {"status": "NOT FOUND", "message": "wall_logic.py missing."}


# --- Main Area Display ---
st.subheader("📊 Calculation Status")
status_cols = st.columns(4)
with status_cols[0]:
    st.markdown("**Base/Skid Status**")
    skid_message = skid_results.get("message", "N/A")
    if skid_status == "OK": st.success(f"✅ OK: {skid_message}")
    elif skid_status in ["ERROR", "OVER", "CRITICAL ERROR"]: st.error(f"❌ {skid_status}: {skid_message}")
    else: st.info(f"⚪️ {skid_status}: {skid_message}")
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
    st.markdown("**Wall Panel Status**")
    if wall_results:
        wp_status = wall_results.get("status", "UNKNOWN"); wp_message = wall_results.get("message", "N/A")
        if wp_status == "OK": st.success(f"✅ OK: {wp_message}")
        elif wp_status == "WARNING": st.warning(f"⚠️ WARNING: {wp_message}")
        elif wp_status in ["ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {wp_status}: {wp_message}")
        else: st.info(f"⚪️ {wp_status}: {wp_message}")
    else: st.info("⚪️ Calculation pending...")
with status_cols[3]:
    st.markdown("**Top Panel Status**")
    if top_panel_results:
        tp_status_val = top_panel_results.get("status", "UNKNOWN"); tp_message_val = top_panel_results.get("message", "N/A")
        if tp_status_val == "OK": st.success(f"✅ OK: {tp_message_val}")
        elif tp_status_val == "WARNING": st.warning(f"⚠️ WARNING: {tp_message_val}")
        elif tp_status_val in ["ERROR", "NOT FOUND", "CRITICAL ERROR", "SKIPPED"]: st.error(f"❌ {tp_status_val}: {tp_message_val}")
        else: st.info(f"⚪️ {tp_status_val}: {tp_message_val}")
    else: st.info("⚪️ Calculation pending...")

st.divider()
st.subheader("📈 Summary Metrics")
col1, col2, col3, col4, col5 = st.columns(5)
def format_metric(value, unit="\"", decimals=2, default="N/A"):
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value): return default
    try: return f"{value:.{0 if abs(value - round(value)) < config.FLOAT_TOLERANCE else decimals}f}{unit}"
    except (TypeError, ValueError): return str(value)

with col1: st.markdown("##### 📦 Crate Overall"); st.metric("Overall Width (OD)", format_metric(crate_overall_width)); st.metric("Overall Length (OD)", format_metric(crate_overall_length)); st.metric("Overall Height (OD)", format_metric(crate_overall_height_external)); st.metric("Panel Thickness Used", format_metric(panel_thickness_ui))
with col2:
    st.markdown("##### 🔩 Base/Skid Setup"); st.metric("Skid Type", skid_results.get('skid_type', 'N/A')); st.metric("Skid Actual W x H", f"{format_metric(skid_results.get('skid_width'))} x {format_metric(skid_results.get('skid_height'))}")
    skid_count_metric = skid_results.get('skid_count'); st.metric("Skid Count", str(skid_count_metric) if skid_count_metric is not None else "N/A"); spacing_actual_metric = skid_results.get('spacing_actual'); spacing_display = format_metric(spacing_actual_metric) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"; st.metric("Actual Spacing (C-C)", spacing_display); st.metric("Max Allowed Spacing", format_metric(skid_results.get('max_spacing')))
    overall_skid_span_metric = None
    if skid_status == "OK":
        if floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span'): overall_skid_span_metric = floorboard_logic.calculate_overall_skid_span(skid_results)
        else:
            skid_w_m = skid_results.get('skid_width'); pos_m = skid_results.get('skid_positions', []); skid_c_m = skid_results.get('skid_count')
            if skid_c_m == 1 and skid_w_m is not None: overall_skid_span_metric = skid_w_m
            elif skid_c_m is not None and skid_c_m > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_c_m: overall_skid_span_metric = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
    st.metric("Overall Skid Span", format_metric(overall_skid_span_metric), help="Outer edge to outer edge of skids.")
with col3:
    st.markdown("##### 🪵 Floorboard Summary")
    if floor_results and floor_results.get('status') not in ["NOT FOUND", "INPUT ERROR", "CRITICAL ERROR", "SKIPPED"]:
        fb_boards = floor_results.get("floorboards", []); fb_board_counts = floor_results.get("board_counts", {}); st.metric("Total Boards", len(fb_boards) if fb_boards else "N/A"); st.metric("Board Length", format_metric(floor_results.get("floorboard_length_across_skids")), help="= Overall Skid Span"); st.metric("Target Span (Layout)", format_metric(floor_results.get("target_span_along_length")), help="Product Length + 2x Clearance Side")
        gap_val = floor_results.get("center_gap"); gap_disp = f"⚠️ {gap_val:.3f}\"" if floor_results.get("status") == "WARNING" and gap_val is not None else format_metric(gap_val, decimals=3); st.metric("Center Gap", gap_disp); st.metric("Custom Narrow Used", format_metric(floor_results.get("custom_board_width"), decimals=3) if floor_results.get("narrow_board_used") else "Not Used")
        counts_str = ", ".join([f"{nom}: {cnt}" for nom, cnt in sorted(fb_board_counts.items())]); st.markdown(f"**Counts:** {counts_str if counts_str else 'None'}")
        fb_calc_span = floor_results.get("calculated_span_covered"); fb_target_span_check = floor_results.get("target_span_along_length");
        if fb_calc_span is not None and fb_target_span_check is not None:
            if math.isclose(fb_calc_span, fb_target_span_check, abs_tol=config.FLOAT_TOLERANCE * 10): st.success(f"Span Check: OK")
            else: st.error(f"Span Check FAIL: Calc={fb_calc_span:.3f}\" vs Target={fb_target_span_check:.3f}\"")
        else: st.caption("Span Check Pending")
    else: st.caption("No floorboard data.")
with col4:
    st.markdown("##### 🧱 Wall Panel Summary")
    if wall_results and wall_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
        st.metric("Panel Height Used", format_metric(wall_results.get("panel_height_used"))); st.metric("Plywood Thickness", format_metric(wall_results.get("panel_plywood_thickness_used")))
        ws = wall_results.get("wall_cleat_spec", {}); cleat_spec_disp_w = f"{ws.get('thickness', 'N/A'):.2f}x{ws.get('width', 'N/A'):.2f}\" (act.)"; st.metric("Wall Cleat Lumber Spec", cleat_spec_disp_w)
        side_panel_data = wall_results.get("side_panels", [{}])[0]; end_panel_data = wall_results.get("end_panels", [{}])[0]; side_cleat_count = len(side_panel_data.get("cleats", [])); end_cleat_count = len(end_panel_data.get("cleats", [])); st.metric("Side Panel Cleats (ea)", str(side_cleat_count)); st.metric("End Panel Cleats (ea)", str(end_cleat_count)); st.metric("Total Wall Cleats", str(side_cleat_count * 2 + end_cleat_count * 2))
    else: st.caption("No wall panel data.")
with col5:
    st.markdown("##### 🧢 Top Panel Summary")
    if top_panel_results and top_panel_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
        st.metric("Panel W x L", f"{format_metric(top_panel_results.get('cap_panel_width'))} x {format_metric(top_panel_results.get('cap_panel_length'))}"); st.metric("Panel Thickness", format_metric(top_panel_results.get("cap_panel_thickness")))
        lc = top_panel_results.get("longitudinal_cleats", {}); tc = top_panel_results.get("transverse_cleats", {}); cs = top_panel_results.get("cap_cleat_spec", {}); cleat_spec_disp_c = f"{cs.get('thickness', 'N/A'):.2f}x{cs.get('width', 'N/A'):.2f}\" (act.)"; st.metric("Top Cleat Lumber Spec", cleat_spec_disp_c)
        st.metric("Long. Cleats (Count)", str(lc.get("count", "N/A"))); st.metric("Long. Spacing (C-C)", format_metric(lc.get("actual_spacing"))); st.metric("Trans. Cleats (Count)", str(tc.get("count", "N/A"))); st.metric("Trans. Spacing (C-C)", format_metric(tc.get("actual_spacing"))); st.metric("Max Cleat Spacing Used", format_metric(top_panel_results.get("max_allowed_cleat_spacing_used")))
    else: st.caption("No top panel data.")

st.divider()
st.header("📐 Layout Schematics")

# --- Define Plotting Function for Schematic Box Views ---
def create_schematic_view(title, width, height, components=[], annotations=[], background_color="#FFFFFF", border_color=config.OUTLINE_COLOR):
    fig = go.Figure(); max_x = width; max_y = height; padding_x = max(width * 0.05, 5); padding_y = max(height * 0.05, 5); legend_items_added = set()
    for comp in components:
        fig.add_shape(type="rect", x0=comp.get("x0", 0), y0=comp.get("y0", 0), x1=comp.get("x1", 0), y1=comp.get("y1", 0), line=dict(color=comp.get("line_color", border_color), width=comp.get("line_width", 1)), fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"), opacity=comp.get("opacity", 1.0), layer=comp.get("layer", "above"), name=comp.get("name", ""))
        comp_name = comp.get("name");
        if comp_name and comp_name not in legend_items_added: fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=comp_name, marker=dict(color=comp.get("fillcolor", "rgba(0,0,0,0)"), size=10, symbol='square', line=dict(color=comp.get("line_color", border_color), width=1)))); legend_items_added.add(comp_name)
    for ann in annotations: fig.add_annotation(x=ann.get("x"), y=ann.get("y"), text=ann.get("text", ""), showarrow=ann.get("showarrow", False), font=dict(size=ann.get("size", 10), color=ann.get("color", config.DIM_ANNOT_COLOR)), align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0.6)"), xanchor=ann.get("xanchor", "center"), yanchor=ann.get("yanchor", "middle"), yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0))
    # Ensure axes autoscale by default, remove fixedrange
    fig.update_layout(
        title=title,
        xaxis=dict(range=[-padding_x, max_x + padding_x], showgrid=False, zeroline=False, showticklabels=False, visible=False, fixedrange=False), # Allow zoom/pan
        yaxis=dict(range=[-padding_y, max_y + padding_y], showgrid=False, zeroline=False, showticklabels=False, visible=False, scaleanchor="x", scaleratio=1, fixedrange=False), # Allow zoom/pan
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=10),
        height=max(350, int(height*1.2) + 60), # Dynamic height
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=config.LEGEND_FONT_COLOR, size=11))
    )
    return fig

# --- Base/Skid Visualization ---
st.subheader("Base/Skid Layout (Top-Down Schematic)")
skid_plot_generated = False; skid_plot_error = None
if skid_status == "OK":
    try:
        skid_w_viz = skid_results.get('skid_width'); skid_count_viz = skid_results.get('skid_count'); positions_viz = skid_results.get('skid_positions'); spacing_viz = skid_results.get('spacing_actual'); usable_w_skids_viz = skid_results.get('usable_width', 0); overall_skid_span_viz = overall_skid_span_metric
        if (skid_w_viz and skid_count_viz and positions_viz and len(positions_viz) == skid_count_viz and usable_w_skids_viz):
            components = []; annotations = []; plot_width = usable_w_skids_viz; plot_height = skid_w_viz * 1.5; origin_x = plot_width / 2.0
            for i, pos in enumerate(positions_viz): x0 = origin_x + pos - skid_w_viz / 2.0; x1 = origin_x + pos + skid_w_viz / 2.0; y0 = plot_height * 0.25; y1 = y0 + skid_w_viz; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.SKID_COLOR_VIZ, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "name": "Skids" if i == 0 else ""}); annotations.append({"x": (x0 + x1) / 2.0, "y": y1 + 5, "text": f"@{pos:.2f}\"", "size": 9, "color": "#555555"})
            if skid_count_viz > 1 and spacing_viz is not None:
                 for i in range(skid_count_viz - 1): x_start = origin_x + positions_viz[i]; x_end = origin_x + positions_viz[i+1]; mid_x = (x_start + x_end) / 2.0; annotations.append({"x": mid_x, "y": y0 - 10, "text": f'↔ {spacing_viz:.2f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
            annotations.append({"x": plot_width / 2.0, "y": -10, "text": f"Usable Width: {usable_w_skids_viz:.2f}\"", "size": 10});
            if overall_skid_span_viz: annotations.append({"x": plot_width / 2.0, "y": plot_height + 15, "text": f"Overall Skid Span: {overall_skid_span_viz:.2f}\"", "size": 10})
            skid_fig = create_schematic_view(title=f"Base/Skid Layout", width=plot_width, height=plot_height, components=components, annotations=annotations); skid_plot_generated = True
        else: skid_plot_error = "Missing/invalid skid data."
    except Exception as e: skid_plot_error = f"Skid schematic error: {e}"; log.error(skid_plot_error, exc_info=True)
if skid_plot_generated:
    st.plotly_chart(skid_fig, use_container_width=True)
    with st.expander("Logic Explanation"):
        st.markdown(f"""
        - **Skid Type Selection:** Based on Product Weight ({product_weight:.1f} lbs). Rule applied: `{skid_results.get('skid_type', 'N/A')}` with max C-C spacing of `{format_metric(skid_results.get('max_spacing'))}`.
        - **Usable Width:** Calculated as Crate Width (`{format_metric(skid_results.get('crate_width'))}`) minus allowances for side panels and cleats = `{format_metric(usable_w_skids_viz)}`.
        - **Skid Count & Spacing:** Calculated to fit within the Usable Width, ensuring spacing (`{format_metric(spacing_viz)}`) does not exceed the maximum allowed. Skids are centered within the Usable Width.
        - **Positions:** Show the centerline position of each skid relative to the center of the Usable Width.
        """)
elif skid_plot_error: st.warning(f"⚠️ {skid_plot_error}")
elif skid_status != "OK": st.info("Base/Skid schematic requires 'OK' skid status.")
else: st.info("Enter parameters.")

# --- Floorboard Visualization ---
st.divider(); st.subheader("Floorboard Layout (Top-Down Schematic)")
floorboard_plot_generated = False; floorboard_plot_error = None
if floorboard_logic_available:
    if floor_results and floor_results.get('status') in ["OK", "WARNING"]:
        fb_boards_viz = floor_results.get("floorboards", []); fb_target_span_viz = floor_results.get("target_span_along_length", 0.0); fb_length_across_skids_viz = floor_results.get("floorboard_length_across_skids", 0.0); fb_center_gap_viz = floor_results.get("center_gap", 0.0)
        if fb_boards_viz and fb_length_across_skids_viz > config.FLOAT_TOLERANCE and fb_target_span_viz > config.FLOAT_TOLERANCE:
            try:
                components = []; annotations = []; plot_width = fb_length_across_skids_viz; plot_height = fb_target_span_viz; custom_added_legend = False; std_added_legend = False
                for i, board in enumerate(fb_boards_viz):
                    board_width_dim_fb = board.get("actual_width", 0.0); board_start_y_fb = board.get("position", 0.0); board_end_y_fb = board_start_y_fb + board_width_dim_fb; board_nominal_fb = board.get("nominal", "N/A"); is_custom = board_nominal_fb == "Custom"; board_color_fb = config.FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else config.FLOORBOARD_STD_COLOR_VIZ
                    comp_name = "";
                    if is_custom and not custom_added_legend: comp_name = "Custom Board"; custom_added_legend = True
                    elif not is_custom and not std_added_legend: comp_name = "Standard Boards"; std_added_legend = True
                    components.append({"x0": 0, "y0": board_start_y_fb, "x1": plot_width, "y1": board_end_y_fb, "fillcolor": board_color_fb, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": comp_name})
                    if board_width_dim_fb > 0.5: annotations.append({"x": plot_width / 2.0, "y": (board_start_y_fb + board_end_y_fb) / 2.0, "text": f'{board_nominal_fb}<br>{board_width_dim_fb:.2f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR if is_custom else "#333333"})
                if abs(fb_center_gap_viz) > config.FLOAT_TOLERANCE:
                    gap_start_y_viz = floor_results.get("total_board_width", 0.0); gap_end_y_viz = gap_start_y_viz + fb_center_gap_viz
                    if gap_end_y_viz > gap_start_y_viz + config.FLOAT_TOLERANCE: components.append({"x0": 0, "y0": gap_start_y_viz, "x1": plot_width, "y1": gap_end_y_viz, "fillcolor": config.GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, "name": f'Center Gap ({fb_center_gap_viz:.3f}")'}); annotations.append({"x": plot_width / 2.0, "y": (gap_start_y_viz + gap_end_y_viz) / 2.0, "text": f"Gap\n{fb_center_gap_viz:.3f}\"", "size": 8, "color": config.DIM_ANNOT_COLOR, "bgcolor": "rgba(255,255,255,0.0)"})
                annotations.append({"x": -5, "y": plot_height / 2.0, "text": f'{plot_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
                annotations.append({"x": plot_width / 2.0, "y": -10, "text": f'{plot_width:.2f}"', "size": 10, "yanchor": "top"})
                fb_fig = create_schematic_view(title=f"Floorboard Layout (Target Span: {fb_target_span_viz:.2f}\")", width=plot_width, height=plot_height, components=components, annotations=annotations); floorboard_plot_generated = True
            except Exception as e: floorboard_plot_error = f"FB schematic error: {e}"; log.error(floorboard_plot_error, exc_info=True)
        if floorboard_plot_generated:
            st.plotly_chart(fb_fig, use_container_width=True)
            with st.expander("Logic Explanation"):
                st.markdown(f"""
                - **Target Span:** Calculated as Product Length (`{format_metric(product_length_input)}`) + 2 * Side Clearance (`{format_metric(clearance_side_product)}`) = `{format_metric(fb_target_span_viz)}`.
                - **Board Length:** Equal to the Overall Skid Span (`{format_metric(fb_length_across_skids_viz)}`).
                - **Placement Method:** `{floor_results.get("placement_method", "N/A")}`.
                - **Logic:**
                    1. Place widest available standard boards symmetrically from edges inwards.
                    2. Calculate remaining center span.
                    3. Fill center span with best single board (standard or custom if allowed) to minimize gap.
                    4. If custom allowed, first fill wasn't custom, and gap >= `{config.MIN_CUSTOM_NARROW_WIDTH}"`, add a second custom board (up to `{config.MAX_CUSTOM_NARROW_WIDTH}"` wide).
                - **Result:** Final calculated gap is `{format_metric(fb_center_gap_viz, decimals=3)}`. Custom board used: `{'Yes (' + format_metric(floor_results.get("custom_board_width"), decimals=3) + ')' if floor_results.get("narrow_board_used") else 'No'}`.
                """)
        elif floorboard_plot_error: st.warning(f"⚠️ {floorboard_plot_error}")
        elif not fb_boards_viz: st.info("No floorboards were placed.")
        else: st.info("FB schematic needs valid boards & positive dims.")
    elif floor_results: st.info(f"No FB layout: {floor_results.get('message', 'Status: '+floor_results.get('status','N/A'))}")
    elif skid_status != "OK": st.info("FB layout needs OK skid status.")
else: st.warning("Floorboard logic not available.")

# --- Wall Panel Visualization ---
st.divider(); st.subheader("Wall Panel Layout Schematics")
def create_wall_panel_schematic(panel_data=None, panel_label="Wall Panel"):
    if not panel_data or not panel_data.get("cleats"): return go.Figure(layout=dict(title=f"{panel_label} Layout (Data Unavailable)")), f"{panel_label} data not valid."
    panel_w = panel_data.get("panel_width", 0); panel_h = panel_data.get("panel_height", 0); cleats = panel_data.get("cleats", [])
    if panel_w <= config.FLOAT_TOLERANCE or panel_h <= config.FLOAT_TOLERANCE: return go.Figure(layout=dict(title=f"{panel_label} Layout (Invalid Dimensions)")), f"{panel_label} dimensions invalid."
    components = []; annotations = []; cleats_added_legend = False
    components.append({"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h, "fillcolor": config.WALL_PANEL_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": "Plywood"})
    for cleat in cleats:
        c_orient = cleat.get("orientation"); c_len = cleat.get("length"); c_width = cleat.get("width"); c_x = cleat.get("position_x"); c_y = cleat.get("position_y"); abs_center_x = c_x + panel_w / 2.0; abs_center_y = c_y + panel_h / 2.0
        if c_orient == "horizontal": x0, x1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0; y0, y1 = abs_center_y - c_width / 2.0, abs_center_y + c_width / 2.0; text_annot = f'{c_len:.1f}" L'
        elif c_orient == "vertical": x0, x1 = abs_center_x - c_width / 2.0, abs_center_x + c_width / 2.0; y0, y1 = abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0; text_annot = f'{c_len:.1f}" H'
        else: continue
        comp_name = "";
        if not cleats_added_legend: comp_name = "Cleats"; cleats_added_legend = True
        components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.WALL_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name})
        if c_len > 1.0 and c_width > 1.0: annotations.append({"x": abs_center_x, "y": abs_center_y, "text": text_annot, "size": 8, "color": config.CLEAT_FONT_COLOR})
    annotations.append({"x": -5, "y": panel_h / 2.0, "text": f'{panel_h:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
    annotations.append({"x": panel_w / 2.0, "y": -10, "text": f'{panel_w:.2f}"', "size": 10, "yanchor": "top"})
    fig = create_schematic_view(title=f"{panel_label} Layout", width=panel_w, height=panel_h, components=components, annotations=annotations)
    return fig, None
wall_view_tabs = st.tabs(["Side Panel View", "End Panel View"])
with wall_view_tabs[0]:
    st.markdown("#### Side Panel (Along Crate Length)")
    side_panel_data_to_plot = wall_results.get("side_panels", [None])[0] if wall_results else None
    fig_side_wall, error_side_wall = create_wall_panel_schematic(panel_data=side_panel_data_to_plot, panel_label="Side Panel")
    if error_side_wall: st.info(error_side_wall)
    else:
        st.plotly_chart(fig_side_wall, use_container_width=True)
        with st.expander("Logic Explanation"):
            st.markdown(f"""
            - **Dimensions:** Width = Crate Overall Length (`{format_metric(side_panel_data_to_plot.get('panel_width'))}`), Height = Internal Clear Height (`{format_metric(side_panel_data_to_plot.get('panel_height'))}`).
            - **Cleats:** Edge cleats are placed along all four sides. Horizontal edge cleats run the full panel width. Vertical edge cleats run between the horizontal edge cleats.
            - **Intermediate Cleats:** (Simplified) A central vertical cleat is added if panel width > `{config.INTERMEDIATE_CLEAT_THRESHOLD}"`. A central horizontal cleat is added if panel height > `{config.INTERMEDIATE_CLEAT_THRESHOLD}"`.
            """)
with wall_view_tabs[1]:
    st.markdown("#### End Panel (Along Crate Width)")
    end_panel_data_to_plot = wall_results.get("end_panels", [None])[0] if wall_results else None
    fig_end_wall, error_end_wall = create_wall_panel_schematic(panel_data=end_panel_data_to_plot, panel_label="End Panel")
    if error_end_wall: st.info(error_end_wall)
    else:
        st.plotly_chart(fig_end_wall, use_container_width=True)
        with st.expander("Logic Explanation"):
            st.markdown(f"""
            - **Dimensions:** Width = Crate Overall Width (`{format_metric(end_panel_data_to_plot.get('panel_width'))}`), Height = Internal Clear Height (`{format_metric(end_panel_data_to_plot.get('panel_height'))}`).
            - **Cleats:** Edge cleats are placed along all four sides. Vertical edge cleats run the full panel height. Horizontal edge cleats run between the vertical edge cleats.
            - **Intermediate Cleats:** (Simplified) A central vertical cleat is added if panel width > `{config.INTERMEDIATE_CLEAT_THRESHOLD}"`. A central horizontal cleat is added if panel height > `{config.INTERMEDIATE_CLEAT_THRESHOLD}"`.
            """)

# --- Top Panel Visualization ---
st.divider(); st.subheader("Top Panel Layout (Top-Down Schematic)")
top_panel_plot_generated = False; top_panel_plot_error = None
if cap_logic_available and top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
    try:
        panel_w = top_panel_results.get("cap_panel_width", 0); panel_l = top_panel_results.get("cap_panel_length", 0); long_cleats = top_panel_results.get("longitudinal_cleats", {}); trans_cleats = top_panel_results.get("transverse_cleats", {})
        if panel_w > config.FLOAT_TOLERANCE and panel_l > config.FLOAT_TOLERANCE:
            components = []; annotations = []; plot_width = panel_w; plot_height = panel_l; origin_x = plot_width / 2.0; origin_y = plot_height / 2.0; long_cleats_added = False; trans_cleats_added = False
            components.append({"x0": 0, "y0": 0, "x1": plot_width, "y1": plot_height, "fillcolor": config.CAP_PANEL_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": "Top Panel"})
            if long_cleats.get("count", 0) > 0:
                lc_w = long_cleats.get("cleat_width_each", 0); lc_l = long_cleats.get("cleat_length_each", 0); lc_pos = long_cleats.get("positions", [])
                for i, x_center_rel in enumerate(lc_pos): abs_x_center = origin_x + x_center_rel; x0 = abs_x_center - lc_w / 2.0; x1 = abs_x_center + lc_w / 2.0; y0 = origin_y - lc_l / 2.0; y1 = origin_y + lc_l / 2.0; comp_name = "";
                if not long_cleats_added: comp_name = "Longitudinal Cleats"; long_cleats_added = True; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.CAP_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name});
                if lc_w > 0.5: annotations.append({"x": abs_x_center, "y": origin_y, "text": f'{lc_w:.1f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR})
                if len(lc_pos) > 1: lc_space = long_cleats.get("actual_spacing", 0);
                for i in range(len(lc_pos) - 1): mid_x = origin_x + (lc_pos[i] + lc_pos[i+1]) / 2.0; annotations.append({"x": mid_x, "y": plot_height * 0.9, "text": f'↔{lc_space:.1f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
            if trans_cleats.get("count", 0) > 0:
                tc_w = trans_cleats.get("cleat_width_each", 0); tc_l = trans_cleats.get("cleat_length_each", 0); tc_pos = trans_cleats.get("positions", [])
                for i, y_center_rel in enumerate(tc_pos): abs_y_center = origin_y + y_center_rel; x0 = origin_x - tc_l / 2.0; x1 = origin_x + tc_l / 2.0; y0 = abs_y_center - tc_w / 2.0; y1 = abs_y_center + tc_w / 2.0; comp_name = "";
                if not trans_cleats_added: comp_name = "Transverse Cleats"; trans_cleats_added = True; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.CAP_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name});
                if tc_w > 0.5: annotations.append({"x": origin_x, "y": abs_y_center, "text": f'{tc_w:.1f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR})
                if len(tc_pos) > 1: tc_space = trans_cleats.get("actual_spacing", 0);
                for i in range(len(tc_pos) - 1): mid_y = origin_y + (tc_pos[i] + tc_pos[i+1]) / 2.0; annotations.append({"x": plot_width * 0.9, "y": mid_y, "text": f'↕{tc_space:.1f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
            annotations.append({"x": -5, "y": plot_height / 2.0, "text": f'{plot_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"}); annotations.append({"x": plot_width / 2.0, "y": -10, "text": f'{plot_width:.2f}"', "size": 10, "yanchor": "top"})
            top_panel_fig = create_schematic_view(title="Top Panel Layout", width=plot_width, height=plot_height, components=components, annotations=annotations); top_panel_plot_generated = True
        else: top_panel_plot_error = "Top panel dimensions invalid."
    except Exception as e: top_panel_plot_error = f"Top Panel schematic error: {e}"; log.error(top_panel_plot_error, exc_info=True)
if top_panel_plot_generated:
    st.plotly_chart(top_panel_fig, use_container_width=True)
    with st.expander("Logic Explanation"):
        st.markdown(f"""
        - **Panel Dimensions:** Width = Crate Overall Width (`{format_metric(panel_w)}`), Length = Crate Overall Length (`{format_metric(panel_l)}`).
        - **Cleat Calculation:** Longitudinal and Transverse cleats are calculated independently based on the panel dimension they span across and the Max Top Panel Cleat Spacing (`{format_metric(max_top_cleat_spacing_ui)}`).
        - **Cleat Count:** Minimum of 1 (if dimension allows) or 2 (if dimension allows > 2x cleat width). Otherwise, calculated based on `ceil(centerline_span / max_spacing) + 1`.
        - **Transverse Cleat Rule:** A minimum of 2 transverse cleats are enforced if the panel length allows.
        - **Positions:** Show the centerline position of each cleat relative to the center of the panel dimension it spans.
        """)
elif top_panel_plot_error: st.warning(f"⚠️ {top_panel_plot_error}")
elif not cap_logic_available: st.info("Top Panel logic not available.")
elif not top_panel_results or top_panel_results.get("status") not in ["OK","WARNING"]: st.info(f"Top Panel schematic needs OK/Warning. Got: {top_panel_results.get('status') if top_panel_results else 'N/A'}")
else: st.info("Enter params for Top Panel schematic.")

# --- Details Tables ---
st.divider(); st.subheader("📋 Component Details")
with st.expander("Wall Panel Cleat Details", expanded=False):
    if wall_results and wall_results.get("status") == "OK":
        wall_details_data = []; side_panel_cleats = wall_results.get("side_panels", [{}])[0].get("cleats", []); end_panel_cleats = wall_results.get("end_panels", [{}])[0].get("cleats", [])
        for i, cleat in enumerate(side_panel_cleats): wall_details_data.append({"Panel Type": "Side", "Cleat #": i + 1, "Cleat Type": cleat.get("type"), "Length (in)": cleat.get("length"), "Width (in)": cleat.get("width"), "Thickness (in)": cleat.get("thickness"), "Center Pos X (rel)": cleat.get("position_x"), "Center Pos Y (rel)": cleat.get("position_y")})
        for i, cleat in enumerate(end_panel_cleats): wall_details_data.append({"Panel Type": "End", "Cleat #": i + 1, "Cleat Type": cleat.get("type"), "Length (in)": cleat.get("length"), "Width (in)": cleat.get("width"), "Thickness (in)": cleat.get("thickness"), "Center Pos X (rel)": cleat.get("position_x"), "Center Pos Y (rel)": cleat.get("position_y")})
        if wall_details_data: df_wall_details = pd.DataFrame(wall_details_data); st.dataframe(df_wall_details, use_container_width=True, hide_index=True, column_config={"Length (in)": st.column_config.NumberColumn(format="%.2f"), "Width (in)": st.column_config.NumberColumn(format="%.2f"), "Thickness (in)": st.column_config.NumberColumn(format="%.2f"), "Center Pos X (rel)": st.column_config.NumberColumn(format="%.2f"), "Center Pos Y (rel)": st.column_config.NumberColumn(format="%.2f")})
        else: st.caption("No wall cleat details.")
    else: st.caption("No wall panel details available.")
with st.expander("Floorboard Details", expanded=False):
    if floor_results and floor_results.get("status") in ["OK", "WARNING"] and floor_results.get("floorboards"):
        fb_boards_table = floor_results.get("floorboards", []); board_data_table = [ {"Board #": i+1, "Nominal Size": b.get("nominal", "N/A"), "Actual Width (in)": b.get("actual_width", 0.0), "Position Start Y (in)": b.get("position", 0.0)} for i, b in enumerate(fb_boards_table) ]
        df_boards_table = pd.DataFrame(board_data_table); st.dataframe( df_boards_table, use_container_width=True, hide_index=True, column_config={"Actual Width (in)": st.column_config.NumberColumn(format="%.3f"), "Position Start Y (in)": st.column_config.NumberColumn(format="%.3f")} )
    else: st.caption("No floorboard details available.")
with st.expander("Top Panel Cleat Details", expanded=False):
    if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
        cap_details_data = []; lc_data = top_panel_results.get("longitudinal_cleats",{}); tc_data = top_panel_results.get("transverse_cleats",{})
        if lc_data.get("count",0)>0:
            for i,pos_x in enumerate(lc_data.get("positions",[])): cap_details_data.append({"Type":"Longitudinal","Cleat #":i+1,"Length (in)":lc_data.get("cleat_length_each"),"Width (in)":lc_data.get("cleat_width_each"),"Thickness (in)":lc_data.get("cleat_thickness_each"),"Center Pos X (rel)":pos_x,"Center Pos Y":"N/A"})
        if tc_data.get("count",0)>0:
            for i,pos_y in enumerate(tc_data.get("positions",[])): cap_details_data.append({"Type":"Transverse","Cleat #":i+1,"Length (in)":tc_data.get("cleat_length_each"),"Width (in)":tc_data.get("cleat_width_each"),"Thickness (in)":tc_data.get("cleat_thickness_each"),"Center Pos X":"N/A","Center Pos Y (rel)":pos_y})
        if cap_details_data:
            df_cap_details = pd.DataFrame(cap_details_data); st.dataframe(df_cap_details,use_container_width=True,hide_index=True,column_config={"Length (in)":st.column_config.NumberColumn(format="%.2f"),"Width (in)":st.column_config.NumberColumn(format="%.2f"),"Thickness (in)":st.column_config.NumberColumn(format="%.2f"),"Center Pos X (rel)":st.column_config.NumberColumn(format="%.2f"),"Center Pos Y (rel)":st.column_config.NumberColumn(format="%.2f")})
        else: st.caption("No top panel cleat details.")
    else: st.caption("No top panel cleat details available.")

# --- Footer ---
st.sidebar.divider()
st.sidebar.info(f"AutoCrate Wizard v{config.VERSION if hasattr(config, 'VERSION') else '0.4.13'}\nFor inquiries, contact Shivam Bhardwaj.")
