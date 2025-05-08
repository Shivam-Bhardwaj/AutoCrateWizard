# wizard_app/app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Crate Layout System.
Version 0.6.0 - Major update: Implemented multi-view assembly visualizations
(Base, Walls, Top), added variable annotations, refactored UI,
added local BOM table display. PDF generation disabled for stability.
"""

# 1. Standard library imports
import sys
import os
import logging
import math
from collections import Counter, defaultdict
import io

# 2. Third-party library imports
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# PDF/Image libraries are NOT imported here

# 3. Your __main__ block for path adjustments
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
    __package__ = "wizard_app"

# --- Streamlit Page Configuration ---
# Use version from config if loaded, otherwise fallback
try: from wizard_app import config as app_config; APP_VERSION = app_config.VERSION
except: APP_VERSION = "0.6.0" # Fallback version
st.set_page_config(layout="wide", page_title=f"AutoCrate Wizard v{APP_VERSION}", page_icon="⚙️")

# --- Setup Logging ---
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log.info(f"Logger '{log.name}' configured.")

# --- Import Your Project Modules & Dependencies ---
APP_INITIALIZATION_SUCCESS = True
CONFIG_IMPORTED = False
LOGIC_IMPORTED = False
UI_MODULES_IMPORTED = False

try:
    from wizard_app import config
    CONFIG_IMPORTED = True; log.info("Successfully imported: config")
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import 'wizard_app.config': {e}", exc_info=True); CONFIG_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False; config = None
try:
    from wizard_app import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
    LOGIC_IMPORTED = True; log.info("Successfully imported: logic modules & explanations")
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import logic modules: {e}", exc_info=True); LOGIC_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False
try:
    from wizard_app.ui_modules import sidebar, status, metrics, visualizations, details
    UI_MODULES_IMPORTED = True; log.info("Successfully imported: ui_modules")
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import ui_modules: {e}", exc_info=True); UI_MODULES_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False

# Availability checks
floorboard_logic_available = LOGIC_IMPORTED and hasattr(floorboard_logic, 'calculate_floorboard_layout')
cap_logic_available = LOGIC_IMPORTED and hasattr(cap_logic, 'calculate_cap_layout')
wall_logic_available = LOGIC_IMPORTED and hasattr(wall_logic, 'calculate_wall_panels')
details_module_available = UI_MODULES_IMPORTED and hasattr(details, 'display_details_tables')

log.info(f"Module Status: Config={CONFIG_IMPORTED}, Logic={LOGIC_IMPORTED}, UI={UI_MODULES_IMPORTED}")

# Stop App if Critical Imports Failed
if not APP_INITIALIZATION_SUCCESS or not CONFIG_IMPORTED or not LOGIC_IMPORTED or not UI_MODULES_IMPORTED:
    st.error("Application failed to initialize due to critical import errors. Check console logs.")
    st.stop()

# --- Main Application Title ---
st.title(f"⚙️ AutoCrate Wizard v{config.VERSION}") # Use config for version display
st.caption("Interactively calculates and visualizes industrial shipping crate layouts (Base, Floor, Walls, Top).")
st.divider()

# --- Caching Wrappers ---
@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness):
    log.debug("CACHE MISS or RECALC: cached_calculate_skid_layout"); return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)
@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple_or_dict, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow):
    skid_results_dict = dict(skid_results_tuple_or_dict) if isinstance(skid_results_tuple_or_dict, tuple) else skid_results_tuple_or_dict; selected_nominal_sizes = list(selected_nominal_sizes_tuple)
    log.debug("CACHE MISS or RECALC: cached_calculate_floorboard_layout");
    if not floorboard_logic_available: return {"status": "NOT FOUND", "message": "floorboard_logic not loaded."}
    return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)
@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.debug("CACHE MISS or RECALC: cached_calculate_cap_layout");
    if not cap_logic_available: return {"status": "NOT FOUND", "message": "cap_logic not loaded."}
    return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)
@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width):
    log.debug("CACHE MISS or RECALC: cached_calculate_wall_panels");
    if not wall_logic_available: return {"status": "NOT FOUND", "message": "wall_logic not loaded."}
    return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width)

# --- Sidebar Inputs ---
ui_inputs = sidebar.display_sidebar()

# --- Core Logic Execution & Derived Dimensions ---
product_weight = ui_inputs.get('product_weight'); product_width_input = ui_inputs.get('product_width'); product_length_input = ui_inputs.get('product_length'); product_actual_height = ui_inputs.get('product_height')
clearance_side_product = ui_inputs.get('clearance_side'); clearance_above_product_ui = ui_inputs.get('clearance_above'); panel_thickness_ui = ui_inputs.get('panel_thickness')
wall_cleat_thickness_ui = ui_inputs.get('wall_cleat_thickness'); wall_cleat_width_ui = ui_inputs.get('wall_cleat_width')
selected_nominal_sizes_tuple_for_cache = ui_inputs.get('selected_floor_nominals', tuple()); allow_custom_narrow = ui_inputs.get('allow_custom_narrow', False)
cap_cleat_actual_thk_ui = ui_inputs.get('cap_cleat_thickness'); cap_cleat_actual_width_ui = ui_inputs.get('cap_cleat_width'); max_top_cleat_spacing_ui = ui_inputs.get('max_top_cleat_spacing')
log.info(f"UI Inputs captured: {ui_inputs}")
skid_results = {"status": "NOT RUN", "message": "Init"}; floor_results = {"status": "NOT RUN", "message": "Init"}; wall_results = {"status": "NOT RUN", "message": "Init"}; top_panel_results = {"status": "NOT RUN", "message": "Init"}; skid_status = "NOT RUN"
try:
    skid_results = cached_calculate_skid_layout(product_weight, product_width_input, clearance_side_product, panel_thickness_ui, wall_cleat_thickness_ui)
    skid_status = skid_results.get("status", "UNKNOWN"); log.info(f"Skid status: {skid_status} - {skid_results.get('message', '')}")
except Exception as e: log.error(f"Skid calc error: {e}", exc_info=True); st.error(f"Skid calc failed: {e}"); skid_results = {"status": "CRITICAL ERROR", "message": f"{e}"}; skid_status = "CRITICAL ERROR"
skid_results_tuple_for_cache = tuple(sorted(skid_results.items())) if isinstance(skid_results, dict) else skid_results
crate_overall_width = skid_results.get('crate_width', 0.0); crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
skid_actual_height = skid_results.get('skid_height', 0.0); crate_internal_clear_height = product_actual_height + clearance_above_product_ui; wall_panel_height_calc = crate_internal_clear_height
crate_overall_height_external = (skid_actual_height + panel_thickness_ui + wall_panel_height_calc + panel_thickness_ui + cap_cleat_actual_thk_ui)
log.info(f"ODs: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, H={crate_overall_height_external:.2f}. Wall H={wall_panel_height_calc:.2f}")
if floorboard_logic_available:
    if skid_status == "OK":
        if not selected_nominal_sizes_tuple_for_cache and not allow_custom_narrow: floor_results = {"status": "INPUT ERROR", "message": "No std lumber & custom not allowed."}
        else:
            try: floor_results = cached_calculate_floorboard_layout(skid_results_tuple_for_cache, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow); log.info(f"Floor status: {floor_results.get('status')} - {floor_results.get('message', '')}")
            except Exception as e: log.error(f"Floor calc error: {e}", exc_info=True); st.error(f"Floor calc error: {e}"); floor_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
    elif skid_status != "OK" : floor_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
else: floor_results = {"status": "NOT FOUND", "message": "Module missing."}
if cap_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE:
        try: top_panel_results = cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui); log.info(f"Cap status: {top_panel_results.get('status')} - {top_panel_results.get('message', '')}")
        except Exception as e: log.error(f"Cap calc error: {e}", exc_info=True); st.error(f"Cap calc error: {e}"); top_panel_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
    elif skid_status != "OK": top_panel_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
    else: top_panel_results = {"status": "SKIPPED", "message": "Invalid dims."}
else: top_panel_results = {"status": "NOT FOUND", "message": "Module missing."}
if wall_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE and wall_panel_height_calc > config.FLOAT_TOLERANCE:
        try: wall_results = cached_calculate_wall_panels(crate_overall_width, crate_overall_length, wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui); log.info(f"Wall status: {wall_results.get('status')} - {wall_results.get('message', '')}")
        except Exception as e: log.error(f"Wall calc error: {e}", exc_info=True); st.error(f"Wall calc error: {e}"); wall_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
    elif skid_status != "OK": wall_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
    else: wall_results = {"status": "SKIPPED", "message": "Invalid dims."}
else: wall_results = {"status": "NOT FOUND", "message": "Module missing."}

# --- Display Status ---
if UI_MODULES_IMPORTED: status.display_status(skid_results, floor_results, wall_results, top_panel_results)

# --- Prepare Overall Dimensions & Metrics ---
overall_dims_for_display = {'width': crate_overall_width, 'length': crate_overall_length, 'height': crate_overall_height_external,'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height,'clearance_top': clearance_above_product_ui, 'skid_height': skid_actual_height}
overall_skid_span_metric = None
if skid_results.get("status") == "OK":
    if floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span'): overall_skid_span_metric = floorboard_logic.calculate_overall_skid_span(skid_results)
    else:
        skid_w_m, pos_m, skid_c_m = skid_results.get('skid_width'), skid_results.get('skid_positions', []), skid_results.get('skid_count')
        if skid_c_m == 1 and skid_w_m is not None: overall_skid_span_metric = skid_w_m
        elif skid_c_m is not None and skid_c_m > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_c_m: overall_skid_span_metric = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
overall_dims_for_display['overall_skid_span'] = overall_skid_span_metric
if UI_MODULES_IMPORTED: metrics.display_metrics(skid_results, floor_results, wall_results, top_panel_results, overall_dims_for_display)

# --- Main Area Display (Schematics) ---
st.divider(); st.header("📐 Layout Schematics")
if UI_MODULES_IMPORTED:
    visualizations.display_base_assembly_views(skid_results, floor_results, wall_results, overall_dims_for_display, ui_inputs)
    st.divider(); st.subheader("Wall Panel Assembly Schematics")
    if wall_logic_available and wall_results and wall_results.get("status") == "OK":
        side_panel_data = wall_results.get("side_panels", [{}])[0]; back_panel_data = wall_results.get("back_panels", [{}])[0]
        visualizations.display_wall_assembly(side_panel_data, "Side Panel", ui_inputs, overall_dims_for_display)
        st.markdown("<br>", unsafe_allow_html=True)
        visualizations.display_wall_assembly(back_panel_data, "Back Panel", ui_inputs, overall_dims_for_display)
    elif wall_results: st.info(f"Wall schematics not displayed. Status: {wall_results.get('status', 'N/A')}")
    else: st.info("Wall logic/calculation pending.")
    st.divider(); st.subheader("Top Panel Assembly Schematics")
    if cap_logic_available and top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
        visualizations.display_top_panel_assembly(top_panel_results, ui_inputs, overall_dims_for_display)
    elif top_panel_results: st.info(f"Top panel schematics not displayed. Status: {top_panel_results.get('status', 'N/A')}")
    else: st.info("Top panel logic/calculation pending.")
else: st.warning("Visualizations module failed to load. Cannot display schematics.")

# --- Details Tables ---
if details_module_available: details.display_details_tables(wall_results, floor_results, top_panel_results)
else: st.warning("Details display module not available.")


# --- !! Local BOM Compilation Function !! ---
# (Moved from bom_utils.py to simplify dependencies)
def compile_bom_data_local(skid_results, floor_results, wall_results, top_panel_results, overall_dims):
    """ Compiles BOM data directly within app.py. """
    if not CONFIG_IMPORTED or config is None: log.error("Cannot compile BOM: Config object not loaded."); return pd.DataFrame()
    bom_list = []; item_counter = 1; log.debug("Starting LOCAL BOM data compilation.")
    def add_bom_item(qty, part_no_placeholder, description):
        nonlocal item_counter
        if qty is not None and qty > 0:
            bom_list.append({"Item No.": item_counter, "Qty": int(qty), "Part No.": part_no_placeholder, "Description": description})
            item_counter += 1
        else: log.warning(f"Skipped adding BOM item: {description}")

    # Skids
    if skid_results and skid_results.get("status") == "OK":
        skid_count=skid_results.get('skid_count',0); skid_len=overall_dims.get('length'); skid_w=skid_results.get('skid_width'); skid_h=skid_results.get('skid_height'); skid_type=skid_results.get('skid_type','')
        if skid_len and skid_w and skid_h: desc=f"SKID, LUMBER, {skid_type}, {skid_len:.2f} x {skid_w:.2f} x {skid_h:.2f}"; add_bom_item(skid_count,"TBD_SKID_PN",desc)
    # Floorboards
    if floor_results and floor_results.get("status") in ["OK", "WARNING"]:
        boards=floor_results.get("floorboards",[]); board_len=floor_results.get("floorboard_length_across_skids")
        board_thickness = getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', None)
        board_groups=defaultdict(int)
        if board_thickness is None: log.error("Floorboard thickness constant missing in config.")
        else:
            for board in boards: key=(board.get("nominal"), round(board.get("actual_width",0),3)); board_groups[key]+=1
            if board_len:
                for (nominal,actual_width), quantity in board_groups.items(): spec=nominal if nominal!="Custom" else f"Custom {actual_width:.2f}\" W"; desc=f"FLOORBOARD, LUMBER, {spec}, {board_len:.2f} x {actual_width:.2f} x {board_thickness:.3f}"; add_bom_item(quantity,"TBD_FLOOR_PN",desc)
            else: log.warning("Missing board_len for Floorboards.")
    # Wall Panel Assemblies
    if wall_results and wall_results.get("status") == "OK":
        ply_thick=wall_results.get("panel_plywood_thickness_used"); ply_spec=f"{ply_thick:.3f}\" PLYWOOD" if ply_thick else "PLYWOOD"; cleat_ref="CLEATED PER 0251-70054"
        if wall_results.get("side_panels"): side_panel_data=wall_results["side_panels"][0]; side_w,side_h=side_panel_data.get("panel_width"),side_panel_data.get("panel_height");
        if side_w and side_h: desc=f"SIDE PANEL ASSY, {ply_spec}, {cleat_ref} ({side_w:.2f} x {side_h:.2f})"; add_bom_item(2,"TBD_SIDE_PN",desc)
        if wall_results.get("back_panels"): back_panel_data=wall_results["back_panels"][0]; back_w,back_h=back_panel_data.get("panel_width"),back_panel_data.get("panel_height");
        if back_w and back_h: desc=f"BACK PANEL ASSY, {ply_spec}, {cleat_ref} ({back_w:.2f} x {back_h:.2f})"; add_bom_item(2,"TBD_BACK_PN",desc)
    # Top Panel Assembly
    if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
        cap_w=top_panel_results.get("cap_panel_width"); cap_l=top_panel_results.get("cap_panel_length"); cap_ply_thick=top_panel_results.get("cap_panel_thickness"); ply_spec=f"{cap_ply_thick:.3f}\" PLYWOOD" if cap_ply_thick else "PLYWOOD"; cleat_ref="CLEATED PER 0251-70054"
        if cap_w and cap_l: desc=f"TOP PANEL ASSY, {ply_spec}, {cleat_ref} ({cap_l:.2f} x {cap_w:.2f})"; add_bom_item(1,"TBD_TOP_PN",desc)
    log.info(f"Local BOM data compilation finished. Found {item_counter-1} items.")
    final_columns = ["Item No.", "Qty", "Part No.", "Description"]; bom_df = pd.DataFrame(bom_list, columns=final_columns)
    if bom_list: bom_df["Item No."] = bom_df["Item No."].astype(int); bom_df["Qty"] = bom_df["Qty"].astype(int)
    else: bom_df = pd.DataFrame(columns=final_columns).astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str})
    return bom_df

# --- BOM Section (Display Table Only) ---
st.divider(); st.subheader("📦 Bill of Materials (BOM)")
BOM_COMPILER_LOADED = 'compile_bom_data_local' in locals() or 'compile_bom_data_local' in globals()
if BOM_COMPILER_LOADED:
    try:
        bom_dataframe = compile_bom_data_local(
            skid_results, floor_results, wall_results,
            top_panel_results, overall_dims_for_display
        )
        if bom_dataframe is not None and not bom_dataframe.empty:
            st.dataframe(bom_dataframe, hide_index=True, use_container_width=True, column_config={"Item No.": st.column_config.NumberColumn(format="%d"), "Qty": st.column_config.NumberColumn(format="%d")})
        elif bom_dataframe is not None: st.info("No components found for Bill of Materials.")
        else: st.error("BOM data compilation failed.")
        # PDF Generation is disabled
        st.caption("PDF export currently disabled.")
    except Exception as e: log.error(f"Error during BOM section: {e}", exc_info=True); st.error(f"An error occurred while preparing the BOM section: {e}")
else: st.warning("Local BOM compilation function failed to load.")

log.info("Streamlit app script execution finished.")