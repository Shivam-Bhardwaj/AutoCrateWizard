# wizard_app/app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Crate Layout System.
Version 0.6.8 - Corrected indentation error in local BOM compilation function.
"""

import sys
import os
import logging
import math
from collections import Counter, defaultdict
import streamlit as st
import pandas as pd
# plotly.graph_objects is used by visualizations.py

# --- Path Setup ---
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
    __package__ = os.path.basename(current_script_dir) 

# --- Page Config & Logging ---
APP_VERSION = "0.6.8" # Start with fallback
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers: logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'); log.info(f"Logger '{log.name}' configured.")

# --- Import Project Modules ---
APP_INITIALIZATION_SUCCESS = True; CONFIG_IMPORTED = False; LOGIC_IMPORTED = False; UI_MODULES_IMPORTED = False; config = None
try: 
    from . import config; CONFIG_IMPORTED = True; APP_VERSION = config.VERSION; log.info("Imported config (absolute/package)")
except ImportError: 
    log.warning("Absolute config import failed, trying relative...")
    try: import config; CONFIG_IMPORTED = True; APP_VERSION = config.VERSION; log.info("Imported config (relative/direct)")
    except ImportError as e: log.error(f"CRITICAL: config import failed: {e}", exc_info=True); CONFIG_IMPORTED=False; APP_INITIALIZATION_SUCCESS=False
try: 
    from . import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations; LOGIC_IMPORTED = True; log.info("Imported logic (absolute/package)")
except ImportError: 
    log.warning("Absolute logic import failed, trying relative...")
    try: import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations; LOGIC_IMPORTED = True; log.info("Imported logic (relative/direct)")
    except ImportError as e: log.error(f"CRITICAL: logic import failed: {e}", exc_info=True); LOGIC_IMPORTED=False; APP_INITIALIZATION_SUCCESS=False
try: 
    from .ui_modules import sidebar, status, metrics, visualizations, details; UI_MODULES_IMPORTED = True; log.info("Imported ui_modules (absolute/package)")
except ImportError: 
    log.warning("Absolute ui_modules import failed, trying relative...")
    try: from ui_modules import sidebar, status, metrics, visualizations, details; UI_MODULES_IMPORTED = True; log.info("Imported ui_modules (relative/direct)")
    except ImportError as e: log.error(f"CRITICAL: ui_modules import failed: {e}", exc_info=True); UI_MODULES_IMPORTED=False; APP_INITIALIZATION_SUCCESS=False

st.set_page_config(layout="wide", page_title=f"AutoCrate Wizard v{APP_VERSION}", page_icon="⚙️")

# --- Module Availability Checks ---
floorboard_logic_available = LOGIC_IMPORTED and hasattr(floorboard_logic, 'calculate_floorboard_layout')
cap_logic_available = LOGIC_IMPORTED and hasattr(cap_logic, 'calculate_cap_layout')
wall_logic_available = LOGIC_IMPORTED and hasattr(wall_logic, 'calculate_wall_panels')
details_module_available = UI_MODULES_IMPORTED and hasattr(details, 'display_details_tables')
visualizations_available = UI_MODULES_IMPORTED and hasattr(visualizations, 'generate_base_assembly_figures') and hasattr(visualizations, 'generate_wall_panel_figures') and hasattr(visualizations, 'generate_top_panel_figures')

if not APP_INITIALIZATION_SUCCESS or not CONFIG_IMPORTED or not LOGIC_IMPORTED or not UI_MODULES_IMPORTED or not visualizations_available:
    st.error("Application failed to initialize due to critical import errors or missing functions. Check console logs."); st.stop()

st.title(f"⚙️ AutoCrate Wizard v{APP_VERSION}")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts.")
st.divider()

# --- Initialize Session State ---
# (Initialization remains the same: flags, data, figures)
if 'first_data_run_complete' not in st.session_state: st.session_state.first_data_run_complete = False
if 'regenerate_data_clicked' not in st.session_state: st.session_state.regenerate_data_clicked = False 
if 'visuals_are_stale' not in st.session_state: st.session_state.visuals_are_stale = True 
if 'visuals_generated_at_least_once' not in st.session_state: st.session_state.visuals_generated_at_least_once = False
if 'visuals_toggle_state' not in st.session_state: st.session_state.visuals_toggle_state = False 
for key in ['skid_results', 'floor_results', 'wall_results', 'top_panel_results', 'overall_dims_for_display', 'bom_dataframe']:
    if key not in st.session_state: st.session_state[key] = None if key != 'bom_dataframe' else pd.DataFrame()
for fig_key in ['fig_base_top', 'fig_base_front', 'fig_base_side', 'fig_side_panel_front', 'fig_side_panel_profile', 'fig_back_panel_front', 'fig_back_panel_profile', 'fig_top_panel_front', 'fig_top_panel_profile']:
    if fig_key not in st.session_state: st.session_state[fig_key] = None

# --- Caching Wrappers (Unchanged) ---
@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness): log.debug("CACHE MISS/RECALC: cached_calculate_skid_layout"); return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)
@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple_or_dict, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow): skid_results_dict = dict(skid_results_tuple_or_dict) if isinstance(skid_results_tuple_or_dict, tuple) else skid_results_tuple_or_dict; selected_nominal_sizes = list(selected_nominal_sizes_tuple); log.debug("CACHE MISS/RECALC: cached_calculate_floorboard_layout"); return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow) if floorboard_logic_available else {"status":"NOT FOUND"}
@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing): log.debug("CACHE MISS/RECALC: cached_calculate_cap_layout"); return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing) if cap_logic_available else {"status":"NOT FOUND"}
@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width): log.debug("CACHE MISS/RECALC: cached_calculate_wall_panels"); return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width) if wall_logic_available else {"status":"NOT FOUND"}


# --- Sidebar Inputs ---
ui_inputs_current = sidebar.display_sidebar() 

# --- Data Calculation Logic ---
# (Same logic as previous version)
run_data_calculations = False
if st.session_state.get('regenerate_data_clicked', False): run_data_calculations = True; st.session_state.regenerate_data_clicked = False
elif not st.session_state.first_data_run_complete: run_data_calculations = True
else: run_data_calculations = True 

data_actually_changed = False 
if run_data_calculations:
    log.info("Running data calculations check...")
    # --- Fetch inputs ---
    product_weight = ui_inputs_current.get('product_weight'); product_width_input = ui_inputs_current.get('product_width'); product_length_input = ui_inputs_current.get('product_length'); product_actual_height = ui_inputs_current.get('product_height')
    clearance_side_product = ui_inputs_current.get('clearance_side'); clearance_above_product_ui = ui_inputs_current.get('clearance_above'); panel_thickness_ui = ui_inputs_current.get('panel_thickness')
    wall_cleat_thickness_ui = ui_inputs_current.get('wall_cleat_thickness'); wall_cleat_width_ui = ui_inputs_current.get('wall_cleat_width')
    selected_nominal_sizes_tuple_for_cache = ui_inputs_current.get('selected_floor_nominals', tuple()); allow_custom_narrow = ui_inputs_current.get('allow_custom_narrow', False)
    cap_cleat_actual_thk_ui = ui_inputs_current.get('cap_cleat_thickness'); cap_cleat_actual_width_ui = ui_inputs_current.get('cap_cleat_width'); max_top_cleat_spacing_ui = ui_inputs_current.get('max_top_cleat_spacing')

    # --- Perform Calculations & Check for Changes ---
    _skid_results = cached_calculate_skid_layout(product_weight, product_width_input, clearance_side_product, panel_thickness_ui, wall_cleat_thickness_ui)
    if _skid_results != st.session_state.skid_results: st.session_state.skid_results = _skid_results; data_actually_changed = True; log.info("Skid results changed.")
    skid_status = _skid_results.get("status", "UNKNOWN")
    _crate_overall_width = _skid_results.get('crate_width', 0.0)
    _crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
    _wall_panel_height_calc = product_actual_height + clearance_above_product_ui

    _floor_results = st.session_state.floor_results 
    if floorboard_logic_available:
        if skid_status == "OK":
             skid_input_for_floor = tuple(sorted(_skid_results.items())) if isinstance(_skid_results, dict) else _skid_results
             _temp_floor_results = cached_calculate_floorboard_layout(skid_input_for_floor, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow)
             if _temp_floor_results != _floor_results: _floor_results = _temp_floor_results; data_actually_changed = True; log.info("Floor results changed.")
        elif _floor_results is None or _floor_results.get("status") != "SKIPPED": _floor_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}; data_actually_changed = True
    st.session_state.floor_results = _floor_results
    
    _wall_results = st.session_state.wall_results
    if wall_logic_available:
        if skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE and _wall_panel_height_calc > config.FLOAT_TOLERANCE:
            _temp_wall_results = cached_calculate_wall_panels(_crate_overall_width, _crate_overall_length, _wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui)
            if _temp_wall_results != _wall_results: _wall_results = _temp_wall_results; data_actually_changed = True; log.info("Wall results changed.")
        elif _wall_results is None or _wall_results.get("status") != "SKIPPED": _wall_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed = True
    st.session_state.wall_results = _wall_results
    
    _top_panel_results = st.session_state.top_panel_results
    if cap_logic_available:
        if skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE:
            _temp_top_results = cached_calculate_cap_layout(_crate_overall_width, _crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui)
            if _temp_top_results != _top_panel_results: _top_panel_results = _temp_top_results; data_actually_changed = True; log.info("Top Panel results changed.")
        elif _top_panel_results is None or _top_panel_results.get("status") != "SKIPPED": _top_panel_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed = True
    st.session_state.top_panel_results = _top_panel_results
    
    _skid_actual_height = _skid_results.get('skid_height', 0.0)
    _crate_overall_height_external = (_skid_actual_height + panel_thickness_ui + _wall_panel_height_calc + panel_thickness_ui + cap_cleat_actual_thk_ui)
    _overall_dims_new = { 'width': _crate_overall_width, 'length': _crate_overall_length, 'height': _crate_overall_height_external, 'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height, 'clearance_top': clearance_above_product_ui, 'skid_height': _skid_actual_height, 'overall_skid_span': None }
    if skid_status == "OK": _overall_dims_new['overall_skid_span'] = floorboard_logic.calculate_overall_skid_span(_skid_results) if floorboard_logic_available else None
    if _overall_dims_new != st.session_state.overall_dims_for_display: st.session_state.overall_dims_for_display = _overall_dims_new; data_actually_changed = True; log.info("Overall dimensions changed.")
    
    # --- Compile BOM ---
    if data_actually_changed or st.session_state.bom_dataframe is None:
        log.info("Recompiling BOM data...")
        
        # Local BOM Compilation Function Definition with corrected indentation
        def compile_bom_data_local(skid_res, floor_res, wall_res, top_res, overall_dims_bom): 
            # Indent level 1 (inside compile_bom_data_local)
            if config is None: 
                log.error("Config not loaded, cannot compile BOM.")
                return pd.DataFrame()
            bom_list = [] 
            item_counter = 1 
            
            # Nested Function Definition with corrected indentation
            def add_bom_item(qty, part_no_placeholder, description): 
                # Indent level 2 (inside add_bom_item)
                nonlocal item_counter 
                if qty is not None and qty > 0: 
                    # Indent level 3 (inside if)
                    bom_list.append({ 
                        "Item No.": item_counter, 
                        "Qty": int(qty), 
                        "Part No.": part_no_placeholder, 
                        "Description": description
                    })
                    item_counter += 1 # Still indent level 3
                # else block can be added here if needed at indent level 3

            # Rest of compile_bom_data_local logic starts at Indent level 1
            if skid_res and skid_res.get("status") == "OK": # Skids
                skid_count=skid_res.get('skid_count',0); skid_len_val=overall_dims_bom.get('length'); skid_w=skid_res.get('skid_width'); skid_h=skid_res.get('skid_height'); skid_type=skid_res.get('skid_type','')
                if skid_len_val and skid_w and skid_h: desc=f"SKID, LUMBER, {skid_type}, {skid_len_val:.2f}L x {skid_w:.2f}W x {skid_h:.2f}H"; add_bom_item(skid_count,"TBD_SKID_PN",desc) 
            
            if floor_res and floor_res.get("status") in ["OK", "WARNING"]: # Floor
                boards=floor_res.get("floorboards",[]); board_len_val=floor_res.get("floorboard_length_across_skids"); board_thickness = getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', 1.5) 
                board_groups=defaultdict(int); 
                for board in boards: key=(board.get("nominal"), round(board.get("actual_width",0),3)); board_groups[key]+=1 # Indent level 2 (inside if)
                if board_len_val: # Indent level 2
                    for (nominal,actual_width), quantity in board_groups.items(): # Indent level 3
                        spec=nominal if nominal!="Custom" else f"Custom {actual_width:.2f}\" W"; desc=f"FLOORBOARD, LUMBER, {spec}, {board_len_val:.2f}L x {actual_width:.2f}W x {board_thickness:.3f}T"; add_bom_item(quantity,"TBD_FLOOR_PN",desc) 
            
            if wall_res and wall_res.get("status") == "OK": # Walls
                 ply_thick_val=wall_res.get("panel_plywood_thickness_used"); ply_spec=f"{ply_thick_val:.3f}\" PLY" if ply_thick_val else "PLY"; cleat_ref="CLEATED" 
                 if wall_res.get("side_panels"): side_w_bom,side_h_bom=wall_res["side_panels"][0].get("panel_width"),wall_res["side_panels"][0].get("panel_height"); desc=f"SIDE PANEL ASSY, {ply_spec}, {cleat_ref} ({side_w_bom:.2f}L x {side_h_bom:.2f}H)"; add_bom_item(2,"TBD_SIDE_PN",desc) 
                 if wall_res.get("back_panels"): back_w_bom,back_h_bom=wall_res["back_panels"][0].get("panel_width"),wall_res["back_panels"][0].get("panel_height"); desc=f"BACK PANEL ASSY, {ply_spec}, {cleat_ref} ({back_w_bom:.2f}W x {back_h_bom:.2f}H)"; add_bom_item(2,"TBD_BACK_PN",desc) 
            
            if top_res and top_res.get("status") in ["OK", "WARNING"]: # Top
                 cap_w_bom=top_res.get("cap_panel_width"); cap_l_bom=top_res.get("cap_panel_length"); cap_ply_thick_val=top_res.get("cap_panel_thickness"); ply_spec=f"{cap_ply_thick_val:.3f}\" PLY" if cap_ply_thick_val else "PLY"; cleat_ref="CLEATED" 
                 if cap_w_bom and cap_l_bom: desc=f"TOP PANEL ASSY, {ply_spec}, {cleat_ref} ({cap_l_bom:.2f}L x {cap_w_bom:.2f}W)"; add_bom_item(1,"TBD_TOP_PN",desc) 
            
            # Finalizing BOM df (Indent level 1)
            final_columns = ["Item No.", "Qty", "Part No.", "Description"]
            bom_df = pd.DataFrame(bom_list, columns=final_columns)
            if bom_list: 
                bom_df["Item No."] = bom_df["Item No."].astype(int)
                bom_df["Qty"] = bom_df["Qty"].astype(int)
            else: 
                bom_df = pd.DataFrame(columns=final_columns).astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str})
            return bom_df 
        
        # --- Call BOM function --- (Indent level 2)
        st.session_state.bom_dataframe = compile_bom_data_local(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
        # data_actually_changed = True # Already potentially set above

    # --- Mark Visuals Stale ---
    if data_actually_changed:
        log.info("Data changed, marking visuals as stale.")
        st.session_state.visuals_are_stale = True
        st.session_state.visuals_generated_at_least_once = False 

    st.session_state.first_data_run_complete = True


# --- Display Data-Driven UI Elements ---
if st.session_state.first_data_run_complete:
    status.display_status(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results)
    if st.session_state.overall_dims_for_display: metrics.display_metrics(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
else:
    st.info("Welcome! Adjust parameters and click '🔄 Regenerate Crate' in the sidebar.")


# --- Visualization Control and Generation/Display ---
st.divider()
st.subheader("📐 Layout Schematics")

current_toggle_value = st.session_state.get('visuals_toggle_state', False) 
show_visuals_toggle = st.toggle(
    "Show/Update Visuals", 
    value=current_toggle_value, 
    key="visuals_toggle_widget",
    help="Toggle ON to generate/update and view schematics."
)
if show_visuals_toggle != current_toggle_value:
    st.session_state.visuals_toggle_state = show_visuals_toggle
    log.info(f"Visuals toggle changed to: {show_visuals_toggle}")
    if not show_visuals_toggle: 
         for fig_k in st.session_state.keys():
            if fig_k.startswith('fig_'): st.session_state[fig_k] = None
         st.session_state.visuals_generated_at_least_once = False
         st.session_state.visuals_are_stale = True 

# --- Generation and Display Block (Only if Toggle is ON) ---
if show_visuals_toggle:
    if not st.session_state.first_data_run_complete:
        st.info("Calculate data first using '🔄 Regenerate Crate'.")
    else:
        needs_generation = not st.session_state.visuals_generated_at_least_once or st.session_state.visuals_are_stale
        
        if needs_generation:
            log.info("Toggle is ON and visuals need generation/update.")
            with st.spinner("Generating visualization figures..."):
                _skid_res = st.session_state.skid_results; _floor_res = st.session_state.floor_results
                _wall_res = st.session_state.wall_results; _top_res = st.session_state.top_panel_results
                _overall_dims = st.session_state.overall_dims_for_display
                can_generate_base = _skid_res and _skid_res.get('status') == 'OK' and _floor_res and _floor_res.get('status') in ['OK', 'WARNING'] and _overall_dims
                can_generate_walls = _wall_res and _wall_res.get('status') == 'OK' and _overall_dims
                can_generate_top = _top_res and _top_res.get('status') in ['OK', 'WARNING'] and _overall_dims

                # Clear previous figures first
                for fig_k in st.session_state.keys():
                     if fig_k.startswith('fig_'): st.session_state[fig_k] = None

                # Generate figures only if data is valid
                if visualizations_available:
                    if can_generate_base:
                         try: st.session_state.fig_base_top, st.session_state.fig_base_front, st.session_state.fig_base_side = visualizations.generate_base_assembly_figures(_skid_res, _floor_res, _wall_res, _overall_dims, ui_inputs_current)
                         except Exception as e: log.error(f"Error generating base figures: {e}", exc_info=True)
                    else: log.warning("Skipping base figure generation due to invalid data.")
                    if can_generate_walls:
                         try: st.session_state.fig_side_panel_front, st.session_state.fig_side_panel_profile = visualizations.generate_wall_panel_figures(_wall_res.get("side_panels", [{}])[0], "Side Panel", ui_inputs_current, _overall_dims); st.session_state.fig_back_panel_front, st.session_state.fig_back_panel_profile = visualizations.generate_wall_panel_figures(_wall_res.get("back_panels", [{}])[0], "Back Panel", ui_inputs_current, _overall_dims)
                         except Exception as e: log.error(f"Error generating wall figures: {e}", exc_info=True)
                    else: log.warning("Skipping wall figure generation due to invalid data.")
                    if can_generate_top:
                         try: st.session_state.fig_top_panel_front, st.session_state.fig_top_panel_profile = visualizations.generate_top_panel_figures(_top_res, ui_inputs_current, _overall_dims)
                         except Exception as e: log.error(f"Error generating top panel figures: {e}", exc_info=True)
                    else: log.warning("Skipping top panel figure generation due to invalid data.")
            
            st.session_state.visuals_are_stale = False 
            st.session_state.visuals_generated_at_least_once = True
            log.info("Visual generation attempt complete.")
            # No explicit rerun here - display happens below in same script run

        # --- Attempt Display ---
        if not st.session_state.visuals_generated_at_least_once and not needs_generation:
             st.info("Visuals not generated yet (data might be invalid).") 
        elif st.session_state.visuals_are_stale: 
             st.warning("Visuals are outdated. Toggle OFF/ON to refresh.") 
        else: # Visuals should be ready
            log.debug("Displaying figures from session state.")
            
            # --- Display Figures with Corrected Structure ---
            st.subheader("⚙️ BASE ASSEMBLY")
            col_base1, col_base2, col_base3 = st.columns(3)
            with col_base1: 
                st.caption("Top View (XY)")
                fig = st.session_state.get('fig_base_top')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True) # Display if fig exists
                else: 
                    st.caption("Not Available") # Fallback caption
            with col_base2: 
                st.caption("Front View (XZ)")
                fig = st.session_state.get('fig_base_front')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")
            with col_base3: 
                st.caption("Side View (YZ)")
                fig = st.session_state.get('fig_base_side')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")

            st.divider(); st.subheader("🧱 Wall Panel Assemblies")
            st.markdown("#### SIDE PANEL ASSY")
            col_wall_side1, col_wall_side2 = st.columns(2)
            with col_wall_side1: 
                st.caption("Front View")
                fig = st.session_state.get('fig_side_panel_front')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")
            with col_wall_side2: 
                st.caption("Profile View")
                fig = st.session_state.get('fig_side_panel_profile')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")
            _wall_res_exp = st.session_state.get('wall_results'); _overall_dims_exp = st.session_state.get('overall_dims_for_display')
            if _wall_res_exp and _overall_dims_exp and _wall_res_exp.get("side_panels"):
                 with st.expander("Logic Explanation (Side Panel)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(panel_data=_wall_res_exp["side_panels"][0], panel_type_label="Side Panel", overall_dims=_overall_dims_exp))
            
            st.markdown("<br>", unsafe_allow_html=True); st.markdown("#### BACK PANEL ASSY") 
            col_wall_back1, col_wall_back2 = st.columns(2) 
            with col_wall_back1: 
                st.caption("Front View")
                fig = st.session_state.get('fig_back_panel_front')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True) 
                else: 
                    st.caption("Not Available")
            with col_wall_back2: 
                st.caption("Profile View")
                fig = st.session_state.get('fig_back_panel_profile')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True) 
                else: 
                    st.caption("Not Available")
            if _wall_res_exp and _overall_dims_exp and _wall_res_exp.get("back_panels"):
                 with st.expander("Logic Explanation (Back Panel)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(panel_data=_wall_res_exp["back_panels"][0], panel_type_label="Back Panel", overall_dims=_overall_dims_exp)) 
                     
            st.divider(); st.subheader("🧢 Top Panel Assembly")
            col_top1, col_top2 = st.columns(2)
            with col_top1: 
                st.caption("Front View")
                fig = st.session_state.get('fig_top_panel_front')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")
            with col_top2: 
                st.caption("Profile View")
                fig = st.session_state.get('fig_top_panel_profile')
                if fig: 
                    st.plotly_chart(fig, use_container_width=True)
                else: 
                    st.caption("Not Available")
            _top_res_exp = st.session_state.get('top_panel_results')
            if _top_res_exp and _overall_dims_exp : 
                with st.expander("Logic Explanation (Top Panel)", expanded=False): st.markdown(explanations.get_top_panel_explanation(top_panel_results=_top_res_exp, ui_inputs=ui_inputs_current))

# --- Display Details and BOM ---
if st.session_state.first_data_run_complete:
    if details_module_available: details.display_details_tables(st.session_state.wall_results, st.session_state.floor_results, st.session_state.top_panel_results)
    st.divider(); st.subheader("📦 Bill of Materials (BOM)")
    bom_df_display = st.session_state.get("bom_dataframe")
    if bom_df_display is not None and not bom_df_display.empty:
        st.dataframe(bom_df_display, hide_index=True, use_container_width=True, column_config={"Item No.": st.column_config.NumberColumn(format="%d"), "Qty": st.column_config.NumberColumn(format="%d")})
    elif bom_df_display is not None: st.info("No components found for Bill of Materials.")
    else: st.error("BOM data not available or compilation failed.")
    st.caption("PDF export currently disabled.")

log.info("Streamlit app script execution finished.")