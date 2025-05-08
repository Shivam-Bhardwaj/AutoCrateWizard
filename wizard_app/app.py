# wizard_app/app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Crate Layout System.
Version 0.6.2 - Regenerate button in sidebar, sidebar UI optimized, Plotly charts fixed range.
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

# 3. Your __main__ block for path adjustments
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
    __package__ = "wizard_app"

# --- Streamlit Page Configuration ---
try: from wizard_app import config as app_config; APP_VERSION = app_config.VERSION # Use config for version
except ImportError: APP_VERSION = "0.6.2" # Fallback if config not loaded yet
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
    APP_VERSION = config.VERSION # Ensure APP_VERSION is from config after successful import
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import 'wizard_app.config': {e}", exc_info=True); CONFIG_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False; config = None
try:
    from wizard_app import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
    LOGIC_IMPORTED = True; log.info("Successfully imported: logic modules & explanations")
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import logic modules: {e}", exc_info=True); LOGIC_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False
try:
    from wizard_app.ui_modules import sidebar, status, metrics, visualizations, details
    UI_MODULES_IMPORTED = True; log.info("Successfully imported: ui_modules")
except ImportError as e: log.error(f"CRITICAL ERROR: Could not import ui_modules: {e}", exc_info=True); UI_MODULES_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False

floorboard_logic_available = LOGIC_IMPORTED and hasattr(floorboard_logic, 'calculate_floorboard_layout')
cap_logic_available = LOGIC_IMPORTED and hasattr(cap_logic, 'calculate_cap_layout')
wall_logic_available = LOGIC_IMPORTED and hasattr(wall_logic, 'calculate_wall_panels')
details_module_available = UI_MODULES_IMPORTED and hasattr(details, 'display_details_tables')

log.info(f"Module Status: Config={CONFIG_IMPORTED}, Logic={LOGIC_IMPORTED}, UI={UI_MODULES_IMPORTED}")

if not APP_INITIALIZATION_SUCCESS or not CONFIG_IMPORTED or not LOGIC_IMPORTED or not UI_MODULES_IMPORTED:
    st.error("Application failed to initialize due to critical import errors. Check console logs.")
    st.stop()

# --- Main Application Title ---
# Title uses APP_VERSION which is now sourced from config if available
st.title(f"⚙️ AutoCrate Wizard v{APP_VERSION}") 
st.caption("Interactively calculates and visualizes industrial shipping crate layouts (Base, Floor, Walls, Top).")
st.divider()

# --- Initialize Session State Flags (if not already done by sidebar) ---
if 'first_run_complete' not in st.session_state:
    st.session_state.first_run_complete = False
# 'regenerate_clicked' is now primarily managed by the button in sidebar.py
# Ensure it exists if sidebar hasn't run yet (though it should have by now)
if 'regenerate_clicked' not in st.session_state:
    st.session_state.regenerate_clicked = False


# --- Caching Wrappers (Unchanged) ---
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

# --- Sidebar Inputs & Regenerate Button ---
# The call to display_sidebar() also handles the "Regenerate Crate" button click
# and updates st.session_state.regenerate_clicked accordingly.
ui_inputs_current = sidebar.display_sidebar()


# --- Determine if Calculations Should Run ---
run_calculations = False
if st.session_state.get('regenerate_clicked', False): # Use .get for safety
    run_calculations = True
    st.session_state.regenerate_clicked = False # Reset flag
elif not st.session_state.first_run_complete:
    run_calculations = True 
    st.session_state.first_run_complete = True

# --- Core Logic Execution & Derived Dimensions (Conditional) ---
# (This section remains largely the same as the previous version, ensuring it uses
#  ui_inputs_current and stores results in session_state)
if run_calculations:
    log.info("Regenerate Crate button clicked or first run: Proceeding with calculations.")
    product_weight = ui_inputs_current.get('product_weight')
    product_width_input = ui_inputs_current.get('product_width')
    product_length_input = ui_inputs_current.get('product_length')
    product_actual_height = ui_inputs_current.get('product_height')
    clearance_side_product = ui_inputs_current.get('clearance_side')
    clearance_above_product_ui = ui_inputs_current.get('clearance_above')
    panel_thickness_ui = ui_inputs_current.get('panel_thickness')
    wall_cleat_thickness_ui = ui_inputs_current.get('wall_cleat_thickness')
    wall_cleat_width_ui = ui_inputs_current.get('wall_cleat_width')
    selected_nominal_sizes_tuple_for_cache = ui_inputs_current.get('selected_floor_nominals', tuple())
    allow_custom_narrow = ui_inputs_current.get('allow_custom_narrow', False)
    cap_cleat_actual_thk_ui = ui_inputs_current.get('cap_cleat_thickness')
    cap_cleat_actual_width_ui = ui_inputs_current.get('cap_cleat_width')
    max_top_cleat_spacing_ui = ui_inputs_current.get('max_top_cleat_spacing')

    log.info(f"UI Inputs for current calculation run: {ui_inputs_current}")
    skid_results = {"status": "NOT RUN", "message": "Init"}
    floor_results = {"status": "NOT RUN", "message": "Init"}
    wall_results = {"status": "NOT RUN", "message": "Init"}
    top_panel_results = {"status": "NOT RUN", "message": "Init"}
    skid_status = "NOT RUN"

    try:
        skid_results = cached_calculate_skid_layout(product_weight, product_width_input, clearance_side_product, panel_thickness_ui, wall_cleat_thickness_ui)
        skid_status = skid_results.get("status", "UNKNOWN"); log.info(f"Skid status: {skid_status} - {skid_results.get('message', '')}")
    except Exception as e: log.error(f"Skid calc error: {e}", exc_info=True); st.error(f"Skid calc failed: {e}"); skid_results = {"status": "CRITICAL ERROR", "message": f"{e}"}; skid_status = "CRITICAL ERROR"
    st.session_state.skid_results = skid_results

    crate_overall_width = skid_results.get('crate_width', 0.0)
    crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
    skid_actual_height = skid_results.get('skid_height', 0.0)
    crate_internal_clear_height = product_actual_height + clearance_above_product_ui
    wall_panel_height_calc = crate_internal_clear_height
    crate_overall_height_external = (skid_actual_height + panel_thickness_ui + wall_panel_height_calc + panel_thickness_ui + cap_cleat_actual_thk_ui)
    log.info(f"Calculated ODs: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, H={crate_overall_height_external:.2f}. Wall H={wall_panel_height_calc:.2f}")

    skid_results_tuple_for_cache = tuple(sorted(skid_results.items())) if isinstance(skid_results, dict) else skid_results

    if floorboard_logic_available:
        if skid_status == "OK":
            if not selected_nominal_sizes_tuple_for_cache and not allow_custom_narrow: floor_results = {"status": "INPUT ERROR", "message": "No std lumber & custom not allowed."}
            else:
                try: floor_results = cached_calculate_floorboard_layout(skid_results_tuple_for_cache, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow); log.info(f"Floor status: {floor_results.get('status')} - {floor_results.get('message', '')}")
                except Exception as e: log.error(f"Floor calc error: {e}", exc_info=True); st.error(f"Floor calc error: {e}"); floor_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
        elif skid_status != "OK" : floor_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
    else: floor_results = {"status": "NOT FOUND", "message": "Module missing."}
    st.session_state.floor_results = floor_results

    if cap_logic_available:
        if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE:
            try: top_panel_results = cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui); log.info(f"Cap status: {top_panel_results.get('status')} - {top_panel_results.get('message', '')}")
            except Exception as e: log.error(f"Cap calc error: {e}", exc_info=True); st.error(f"Cap calc error: {e}"); top_panel_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
        elif skid_status != "OK": top_panel_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
        else: top_panel_results = {"status": "SKIPPED", "message": "Invalid dims for cap."}
    else: top_panel_results = {"status": "NOT FOUND", "message": "Module missing."}
    st.session_state.top_panel_results = top_panel_results

    if wall_logic_available:
        if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE and wall_panel_height_calc > config.FLOAT_TOLERANCE:
            try: wall_results = cached_calculate_wall_panels(crate_overall_width, crate_overall_length, wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui); log.info(f"Wall status: {wall_results.get('status')} - {wall_results.get('message', '')}")
            except Exception as e: log.error(f"Wall calc error: {e}", exc_info=True); st.error(f"Wall calc error: {e}"); wall_results = {"status": "CRITICAL ERROR", "message": f"{e}"}
        elif skid_status != "OK": wall_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}
        else: wall_results = {"status": "SKIPPED", "message": "Invalid dims for wall."}
    else: wall_results = {"status": "NOT FOUND", "message": "Module missing."}
    st.session_state.wall_results = wall_results

    overall_dims_for_display_current_run = {
        'width': crate_overall_width, 'length': crate_overall_length, 'height': crate_overall_height_external,
        'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height,
        'clearance_top': clearance_above_product_ui, 'skid_height': skid_actual_height
    }
    overall_skid_span_metric_val = None
    if skid_results.get("status") == "OK":
        if floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span'):
            overall_skid_span_metric_val = floorboard_logic.calculate_overall_skid_span(skid_results)
        else:
            skid_w_m, pos_m, skid_c_m = skid_results.get('skid_width'), skid_results.get('skid_positions', []), skid_results.get('skid_count')
            if skid_c_m == 1 and skid_w_m is not None: overall_skid_span_metric_val = skid_w_m
            elif skid_c_m is not None and skid_c_m > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_c_m:
                overall_skid_span_metric_val = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
    overall_dims_for_display_current_run['overall_skid_span'] = overall_skid_span_metric_val
    st.session_state.overall_dims_for_display = overall_dims_for_display_current_run

# --- Display Section (Uses data from session_state) ---
# (This section remains largely the same, ensuring it uses ui_inputs_current for viz parameters if needed)
skid_results_to_display = st.session_state.get('skid_results', {"status": "NOT RUN", "message": "Press '🔄 Regenerate Crate'"})
floor_results_to_display = st.session_state.get('floor_results', {"status": "NOT RUN", "message": ""})
wall_results_to_display = st.session_state.get('wall_results', {"status": "NOT RUN", "message": ""})
top_panel_results_to_display = st.session_state.get('top_panel_results', {"status": "NOT RUN", "message": ""})
overall_dims_to_display = st.session_state.get('overall_dims_for_display', None)

if overall_dims_to_display is not None:
    if UI_MODULES_IMPORTED:
        status.display_status(skid_results_to_display, floor_results_to_display, wall_results_to_display, top_panel_results_to_display)
        metrics.display_metrics(skid_results_to_display, floor_results_to_display, wall_results_to_display, top_panel_results_to_display, overall_dims_to_display)

        st.divider(); st.header("📐 Layout Schematics")
        # Pass ui_inputs_current for visualization functions that might need current UI settings not stored in overall_dims
        visualizations.display_base_assembly_views(skid_results_to_display, floor_results_to_display, wall_results_to_display, overall_dims_to_display, ui_inputs_current)

        st.divider(); st.subheader("Wall Panel Assembly Schematics")
        if wall_logic_available and wall_results_to_display and wall_results_to_display.get("status") == "OK":
            side_panel_data = wall_results_to_display.get("side_panels", [{}])[0]
            back_panel_data = wall_results_to_display.get("back_panels", [{}])[0]
            visualizations.display_wall_assembly(side_panel_data, "Side Panel", ui_inputs_current, overall_dims_to_display)
            st.markdown("<br>", unsafe_allow_html=True)
            visualizations.display_wall_assembly(back_panel_data, "Back Panel", ui_inputs_current, overall_dims_to_display)
        elif wall_results_to_display and wall_results_to_display.get("status") not in ["NOT RUN", "SKIPPED"] : st.info(f"Wall schematics not displayed. Status: {wall_results_to_display.get('status', 'N/A')}. Reason: {wall_results_to_display.get('message', 'N/A')}")
        elif wall_results_to_display and wall_results_to_display.get("status") == "SKIPPED" : st.info(f"Wall schematics skipped. Reason: {wall_results_to_display.get('message', 'N/A')}")


        st.divider(); st.subheader("Top Panel Assembly Schematics")
        if cap_logic_available and top_panel_results_to_display and top_panel_results_to_display.get("status") in ["OK", "WARNING"]:
            visualizations.display_top_panel_assembly(top_panel_results_to_display, ui_inputs_current, overall_dims_to_display)
        elif top_panel_results_to_display and top_panel_results_to_display.get("status") not in ["NOT RUN", "SKIPPED"]: st.info(f"Top panel schematics not displayed. Status: {top_panel_results_to_display.get('status', 'N/A')}. Reason: {top_panel_results_to_display.get('message', 'N/A')}")
        elif top_panel_results_to_display and top_panel_results_to_display.get("status") == "SKIPPED" : st.info(f"Top panel schematics skipped. Reason: {top_panel_results_to_display.get('message', 'N/A')}")


    if details_module_available:
        details.display_details_tables(wall_results_to_display, floor_results_to_display, top_panel_results_to_display)
    else: st.warning("Details display module not available.")

    # BOM Compilation and Display (Unchanged from previous version)
    def compile_bom_data_local(skid_res, floor_res, wall_res, top_res, overall_dims_bom):
        if not CONFIG_IMPORTED or config is None: log.error("Cannot compile BOM: Config object not loaded."); return pd.DataFrame()
        bom_list = []; item_counter = 1; log.debug("Starting LOCAL BOM data compilation.")
        def add_bom_item(qty, part_no_placeholder, description):
            nonlocal item_counter
            if qty is not None and qty > 0:
                bom_list.append({"Item No.": item_counter, "Qty": int(qty), "Part No.": part_no_placeholder, "Description": description})
                item_counter += 1
            else: log.warning(f"Skipped adding BOM item (qty 0 or None): {description}")

        if skid_res and skid_res.get("status") == "OK":
            skid_count=skid_res.get('skid_count',0); skid_len_val=overall_dims_bom.get('length'); skid_w=skid_res.get('skid_width'); skid_h=skid_res.get('skid_height'); skid_type=skid_res.get('skid_type','')
            if skid_len_val and skid_w and skid_h: desc=f"SKID, LUMBER, {skid_type}, {skid_len_val:.2f}L x {skid_w:.2f}W x {skid_h:.2f}H"; add_bom_item(skid_count,"TBD_SKID_PN",desc)
        if floor_res and floor_res.get("status") in ["OK", "WARNING"]:
            boards=floor_res.get("floorboards",[]); board_len_val=floor_res.get("floorboard_length_across_skids")
            board_thickness = getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', None)
            board_groups=defaultdict(int)
            if board_thickness is None: log.error("Floorboard thickness constant missing in config.")
            else:
                for board in boards: key=(board.get("nominal"), round(board.get("actual_width",0),3)); board_groups[key]+=1
                if board_len_val:
                    for (nominal,actual_width), quantity in board_groups.items(): spec=nominal if nominal!="Custom" else f"Custom {actual_width:.2f}\" W"; desc=f"FLOORBOARD, LUMBER, {spec}, {board_len_val:.2f}L x {actual_width:.2f}W x {board_thickness:.3f}T"; add_bom_item(quantity,"TBD_FLOOR_PN",desc)
                else: log.warning("Missing board_len for Floorboards in BOM.")
        if wall_res and wall_res.get("status") == "OK":
            ply_thick_val=wall_res.get("panel_plywood_thickness_used"); ply_spec=f"{ply_thick_val:.3f}\" PLYWOOD" if ply_thick_val else "PLYWOOD"; cleat_ref="CLEATED PER DESIGN"
            if wall_res.get("side_panels"): side_panel_data_bom=wall_res["side_panels"][0]; side_w_bom,side_h_bom=side_panel_data_bom.get("panel_width"),side_panel_data_bom.get("panel_height");
            if side_w_bom and side_h_bom: desc=f"SIDE PANEL ASSY, {ply_spec}, {cleat_ref} ({side_w_bom:.2f}L x {side_h_bom:.2f}H)"; add_bom_item(2,"TBD_SIDE_PN",desc)
            if wall_res.get("back_panels"): back_panel_data_bom=wall_res["back_panels"][0]; back_w_bom,back_h_bom=back_panel_data_bom.get("panel_width"),back_panel_data_bom.get("panel_height");
            if back_w_bom and back_h_bom: desc=f"BACK PANEL ASSY, {ply_spec}, {cleat_ref} ({back_w_bom:.2f}W x {back_h_bom:.2f}H)"; add_bom_item(2,"TBD_BACK_PN",desc)
        if top_res and top_res.get("status") in ["OK", "WARNING"]:
            cap_w_bom=top_res.get("cap_panel_width"); cap_l_bom=top_res.get("cap_panel_length"); cap_ply_thick_val=top_res.get("cap_panel_thickness"); ply_spec=f"{cap_ply_thick_val:.3f}\" PLYWOOD" if cap_ply_thick_val else "PLYWOOD"; cleat_ref="CLEATED PER DESIGN"
            if cap_w_bom and cap_l_bom: desc=f"TOP PANEL ASSY, {ply_spec}, {cleat_ref} ({cap_l_bom:.2f}L x {cap_w_bom:.2f}W)"; add_bom_item(1,"TBD_TOP_PN",desc)
        log.info(f"Local BOM data compilation finished. Found {item_counter-1} items.")
        final_columns = ["Item No.", "Qty", "Part No.", "Description"]; bom_df = pd.DataFrame(bom_list, columns=final_columns)
        if bom_list: bom_df["Item No."] = bom_df["Item No."].astype(int); bom_df["Qty"] = bom_df["Qty"].astype(int)
        else: bom_df = pd.DataFrame(columns=final_columns).astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str})
        return bom_df

    st.divider(); st.subheader("📦 Bill of Materials (BOM)")
    BOM_COMPILER_LOADED = 'compile_bom_data_local' in locals() or 'compile_bom_data_local' in globals()
    if BOM_COMPILER_LOADED:
        try:
            bom_dataframe = compile_bom_data_local(
                skid_results_to_display, floor_results_to_display, wall_results_to_display,
                top_panel_results_to_display, overall_dims_to_display
            )
            if bom_dataframe is not None and not bom_dataframe.empty:
                st.dataframe(bom_dataframe, hide_index=True, use_container_width=True, column_config={"Item No.": st.column_config.NumberColumn(format="%d"), "Qty": st.column_config.NumberColumn(format="%d")})
            elif bom_dataframe is not None: st.info("No components found for Bill of Materials. Adjust inputs and 'Regenerate Crate'.")
            else: st.error("BOM data compilation failed (returned None).")
            st.caption("PDF export currently disabled.")
        except Exception as e: log.error(f"Error during BOM section: {e}", exc_info=True); st.error(f"An error occurred while preparing the BOM section: {e}")
    else: st.warning("Local BOM compilation function failed to load.")

else: # if overall_dims_to_display is None
    st.info("Welcome to the AutoCrate Wizard! Please adjust parameters in the sidebar and click '🔄 Regenerate Crate' to design your crate.")

log.info("Streamlit app script execution finished.")