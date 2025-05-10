# wizard_app/app.py
# REV: R_Revert_v3 - Task 1 & 3 Mods, Syntax Fixes, UI Order, Plotly Keys
"""
Streamlit application for the AutoCrate Wizard - Parametric Crate Layout System.
Version 0.8.12
MODIFIED FOR TASK 1: Robust UI - "Regenerate Crate" Button & Static Output
MODIFIED FOR TASK 3: Pass overall_crate_actual_height to wall_logic for decals
SYNTAX FIX: Corrected list comprehension in compile_bom_data_local
SYNTAX FIX: Corrected f-string backslash error in compile_bom_data_local
UI DISPLAY ORDER: Changed display order of wall and top panel assemblies.
BUG FIX: Added unique keys to st.plotly_chart calls to prevent DuplicateElementId error.
"""

import sys
import os
import logging
import math
from collections import Counter, defaultdict
import streamlit as st
import pandas as pd

# --- Path Setup ---
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path: sys.path.insert(0, parent_dir)
    __package__ = os.path.basename(current_script_dir)

# --- Page Config & Logging ---
APP_VERSION_FALLBACK = "0.8.12"
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log.info(f"Logger '{log.name}' configured with basicConfig.")

# --- Import Project Modules ---
APP_INITIALIZATION_SUCCESS = True
CONFIG_IMPORTED = False
LOGIC_IMPORTED = False
UI_MODULES_IMPORTED = False
config = None
APP_VERSION = APP_VERSION_FALLBACK

NX_LABEL_STYLE_CSS = "color:green; font-weight:bold; font-family: 'Courier New', Courier, monospace;"

def get_nx_label_html(label_text):
    return f"<span style='{NX_LABEL_STYLE_CSS}'>{label_text}</span>"

try:
    from . import config
    CONFIG_IMPORTED = True
    APP_VERSION = config.VERSION
    log.info(f"Imported config (relative) - Version: {APP_VERSION}")
except ImportError:
    log.warning("Relative config import failed, trying direct...")
    try:
        import config
        CONFIG_IMPORTED = True
        APP_VERSION = config.VERSION
        log.info(f"Imported config (direct) - Version: {APP_VERSION}")
    except ImportError as e:
        log.error(f"CRITICAL: config import failed: {e}", exc_info=True)
        CONFIG_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False
try:
    from . import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
    from . import pdf_generator # ADDED FOR PDF GENERATION
    LOGIC_IMPORTED = True; log.info("Imported logic modules (relative, including pdf_generator)")
except ImportError:
    log.warning("Relative logic import failed, trying direct...")
    try:
        import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
        LOGIC_IMPORTED = True; log.info("Imported logic modules (direct)")
    except ImportError as e:
        log.error(f"CRITICAL: logic modules import failed: {e}", exc_info=True)
        if 'pdf_generator' in str(e): log.error("pdf_generator module failed to import.")
        LOGIC_IMPORTED = False; APP_INITIALIZATION_SUCCESS = False
try:
    from .ui_modules import status, metrics, visualizations, details
    UI_MODULES_IMPORTED = True; log.info("Imported specific ui_modules")
except ImportError:
    log.warning("Relative specific ui_modules import failed, trying direct...")
    try:
        from ui_modules import status, metrics, visualizations, details
        UI_MODULES_IMPORTED = True; log.info("Imported specific ui_modules (direct)")
    except ImportError as e:
        log.error(f"CRITICAL: specific ui_modules import failed: {e}", exc_info=True)
        APP_INITIALIZATION_SUCCESS = False

st.set_page_config(layout="wide", page_title=f"AutoCrate Wizard v{APP_VERSION}", page_icon="⚙️")

floorboard_logic_available = LOGIC_IMPORTED and hasattr(floorboard_logic, 'calculate_floorboard_layout')
cap_logic_available = LOGIC_IMPORTED and hasattr(cap_logic, 'calculate_cap_layout')
wall_logic_available = LOGIC_IMPORTED and hasattr(wall_logic, 'calculate_wall_panels')
details_module_available = UI_MODULES_IMPORTED and hasattr(details, 'display_details_tables')
visualizations_available = UI_MODULES_IMPORTED and hasattr(visualizations, 'generate_base_assembly_figures')
status_module_available = UI_MODULES_IMPORTED and hasattr(status, 'display_status')
metrics_module_available = UI_MODULES_IMPORTED and hasattr(metrics, 'display_metrics')

if not APP_INITIALIZATION_SUCCESS or not CONFIG_IMPORTED or not LOGIC_IMPORTED or not UI_MODULES_IMPORTED:
    st.error(f"Application v{APP_VERSION} failed to initialize. Check console logs."); st.stop()

@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness):
    log.debug("CACHE MISS/RECALC: cached_calculate_skid_layout")
    if LOGIC_IMPORTED and hasattr(skid_logic, 'calculate_skid_layout'):
        return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)
    return {"status": "ERROR", "message": "Skid logic module not available."}

@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple_or_dict, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow):
    skid_results_dict = dict(skid_results_tuple_or_dict) if isinstance(skid_results_tuple_or_dict, tuple) else skid_results_tuple_or_dict
    log.debug("CACHE MISS/RECALC: cached_calculate_floorboard_layout")
    if floorboard_logic_available:
        return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, list(selected_nominal_sizes_tuple), allow_custom_narrow)
    return {"status":"NOT FOUND", "message":"Floorboard logic module not available."}

@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.debug("CACHE MISS/RECALC: cached_calculate_cap_layout")
    if cap_logic_available:
        return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)
    return {"status":"NOT FOUND", "message":"Cap logic module not available."}

@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness,
                                 overall_crate_actual_height, 
                                 wall_cleat_thickness, wall_cleat_width):
    log.debug(f"CACHE MISS/RECALC: cached_calculate_wall_panels with OverallH: {overall_crate_actual_height}")
    if wall_logic_available:
        return wall_logic.calculate_wall_panels(
            crate_overall_width, crate_overall_length, panel_height, panel_thickness,
            overall_crate_actual_height, 
            wall_cleat_thickness, wall_cleat_width
        )
    return {"status":"NOT FOUND", "message":"Wall logic module not available."}

def set_visuals_stale(): st.session_state.visuals_are_stale = True; log.debug("Visuals marked stale.")
def manage_input_state(widget_key, session_value_key, default_value):
    if session_value_key not in st.session_state: st.session_state[session_value_key] = default_value
    if widget_key in st.session_state and st.session_state[widget_key] != st.session_state[session_value_key]:
        st.session_state[session_value_key] = st.session_state[widget_key]
    return st.session_state[session_value_key]
def input_slider_combo(label_text, min_val, max_val, default_val_from_ss, step, format_str="%.1f", help_text="", key_prefix=""):
    sanitized_label_for_key = label_text.replace(' (in)', '').replace(' (lbs)', '').replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('.', '').lower()
    session_key_value = f"{key_prefix}_value_ss_{sanitized_label_for_key}"
    widget_slider_key, widget_num_key = f"{key_prefix}_widget_slider_{sanitized_label_for_key}", f"{key_prefix}_widget_num_{sanitized_label_for_key}"
    if session_key_value not in st.session_state: st.session_state[session_key_value] = default_val_from_ss
    current_val_from_state = st.session_state[session_key_value]
    if not (min_val <= current_val_from_state <= max_val):
        current_val_from_state = max(min_val, min(max_val, default_val_from_ss)); st.session_state[session_key_value] = current_val_from_state
    slider_col, num_col = st.columns([0.75, 0.25])
    with slider_col:
        new_slider_widget_val = st.slider(label_text, min_val, max_val, value=current_val_from_state, step=step, format=format_str, help=help_text, key=widget_slider_key, on_change=set_visuals_stale)
        if new_slider_widget_val != st.session_state[session_key_value]: st.session_state[session_key_value] = new_slider_widget_val
    with num_col:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        new_num_widget_val = st.number_input("num_for_" + sanitized_label_for_key, min_value=min_val, max_value=max_val, value=st.session_state[session_key_value], step=step, format=format_str, label_visibility="collapsed", key=widget_num_key, help=help_text, on_change=set_visuals_stale)
        if new_num_widget_val != st.session_state[session_key_value]: st.session_state[session_key_value] = new_num_widget_val
    return st.session_state[session_key_value]

st.title(f"⚙️ AutoCrate Wizard v{APP_VERSION}")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts.")

if 'first_data_run_complete' not in st.session_state: st.session_state.first_data_run_complete = False
if 'regenerate_data_clicked' not in st.session_state: st.session_state.regenerate_data_clicked = False
if 'visuals_are_stale' not in st.session_state: st.session_state.visuals_are_stale = True
if 'visuals_generated_at_least_once' not in st.session_state: st.session_state.visuals_generated_at_least_once = False
if 'visuals_toggle_state' not in st.session_state: st.session_state.visuals_toggle_state = True
for key in ['skid_results', 'floor_results', 'wall_results', 'top_panel_results', 'overall_dims_for_display', 'bom_dataframe', 'ui_inputs_current']:
    if key not in st.session_state: st.session_state[key] = pd.DataFrame() if key == 'bom_dataframe' else ({} if key == 'ui_inputs_current' else None)
for fig_key in ['fig_base_top', 'fig_base_front', 'fig_base_side', 'fig_side_panel_front', 'fig_side_panel_profile', 'fig_back_panel_front', 'fig_back_panel_profile', 'fig_top_panel_front', 'fig_top_panel_profile']:
    if fig_key not in st.session_state: st.session_state[fig_key] = None

default_inputs_init = {
    'prod_weight_ss': 1500.0, 'prod_w_main_value_ss_ctrl_prod_width_in': 90.0,
    'prod_l_main_value_ss_ctrl_prod_length_in': 90.0, 'prod_h_main_value_ss_ctrl_prod_height_in': 48.0,
    'clearance_side_ss': 2.0, 'clearance_above_ss': config.DEFAULT_CLEARANCE_ABOVE_PRODUCT if config else 1.5,
    'panel_thick_ss': config.DEFAULT_PANEL_THICKNESS_UI if config else 0.25,
    'wall_cleat_thick_ss': config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75,
    'wall_cleat_width_ss': config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5,
    'floor_lumber_ss': config.DEFAULT_UI_LUMBER_SELECTION_APP if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"],
    'cap_cleat_thick_ss': config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75,
    'cap_cleat_width_ss': config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5, 'max_top_cleat_space_ss': 24.0,
}
for key, val in default_inputs_init.items():
    if key not in st.session_state: st.session_state[key] = val

with st.container(): # TOP DASHBOARD
    st.subheader("Input Parameters")
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1: manage_input_state('prod_weight_widget_main', 'prod_weight_ss', st.session_state.prod_weight_ss); st.number_input("CTRL_Prod_Weight (lbs)", value=st.session_state.prod_weight_ss, min_value=1.0, max_value=20000.0, step=10.0, format="%.1f", key='prod_weight_widget_main', help="Product Weight", on_change=set_visuals_stale)
    with r1c2: input_slider_combo("CTRL_Prod_Width (in)", 1.0, 125.0, st.session_state.prod_w_main_value_ss_ctrl_prod_width_in, 0.5, "%.1f", "Product Width", key_prefix='prod_w_main')
    with r1c3: input_slider_combo("CTRL_Prod_Length (in)", 1.0, 125.0, st.session_state.prod_l_main_value_ss_ctrl_prod_length_in, 0.5, "%.1f", "Product Length", key_prefix='prod_l_main')
    with r1c4: input_slider_combo("CTRL_Prod_Height (in)", 1.0, 120.0, st.session_state.prod_h_main_value_ss_ctrl_prod_height_in, 0.5, "%.1f", "Product Height", key_prefix='prod_h_main')
    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    with r2c1: manage_input_state('clearance_side_widget_main', 'clearance_side_ss', st.session_state.clearance_side_ss); st.number_input("CTRL_Clearance_Side (in)", value=st.session_state.clearance_side_ss, min_value=0.0, step=0.1, format="%.2f", key='clearance_side_widget_main', help="Side Clearance", on_change=set_visuals_stale)
    with r2c2: manage_input_state('clearance_above_widget_main', 'clearance_above_ss', st.session_state.clearance_above_ss); st.number_input("CTRL_Clearance_Top (in)", value=st.session_state.clearance_above_ss, min_value=0.0, step=0.1, format="%.2f", key='clearance_above_widget_main', help="Top Clearance", on_change=set_visuals_stale)
    with r2c3: manage_input_state('panel_thick_widget_main', 'panel_thick_ss', st.session_state.panel_thick_ss); st.number_input("CTRL_Panel_Thickness (in)", value=st.session_state.panel_thick_ss, min_value=0.01, step=0.01, format="%.2f", key='panel_thick_widget_main', help="Panel Thickness", on_change=set_visuals_stale)
    with r2c4: manage_input_state('wall_cleat_thick_widget_main', 'wall_cleat_thick_ss', st.session_state.wall_cleat_thick_ss); st.number_input("CTRL_Wall_Cleat_Thk (in)", value=st.session_state.wall_cleat_thick_ss, min_value=0.01, step=0.01, format="%.2f", key='wall_cleat_thick_widget_main', help="Wall Cleat Thickness", on_change=set_visuals_stale)
    with r2c5: manage_input_state('wall_cleat_width_widget_main', 'wall_cleat_width_ss', st.session_state.wall_cleat_width_ss); st.number_input("CTRL_Wall_Cleat_Wdh (in)", value=st.session_state.wall_cleat_width_ss, min_value=0.1, step=0.1, format="%.1f", key='wall_cleat_width_widget_main', help="Wall Cleat Width", on_change=set_visuals_stale)
    r3c1, r3c2, r3c3 = st.columns([2.5, 2.5, 1])
    with r3c1:
        st.caption("CTRL_Floor_Lumber_Options")
        all_lumber_opts = config.ALL_LUMBER_OPTIONS_UI if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"]
        manage_input_state('floor_lumber_widget_main', 'floor_lumber_ss', st.session_state.floor_lumber_ss); st.multiselect("Floor Lumber Options", options=all_lumber_opts, default=st.session_state.floor_lumber_ss, key='floor_lumber_widget_main', help="Available Floorboard Lumber", on_change=set_visuals_stale)
    with r3c2:
        st.caption("CTRL_Cap_Cleat_Options"); tc1,tc2,tc3 = st.columns(3)
        with tc1: manage_input_state('cap_cleat_thick_widget_main', 'cap_cleat_thick_ss', st.session_state.cap_cleat_thick_ss); st.number_input("CapThk (in)", value=st.session_state.cap_cleat_thick_ss, min_value=0.1, step=0.01, format="%.2f", key='cap_cleat_thick_widget_main', help="Top Cleat Thickness", on_change=set_visuals_stale)
        with tc2: manage_input_state('cap_cleat_width_widget_main', 'cap_cleat_width_ss', st.session_state.cap_cleat_width_ss); st.number_input("CapWdh (in)", value=st.session_state.cap_cleat_width_ss, min_value=0.1, step=0.1, format="%.1f", key='cap_cleat_width_widget_main', help="Top Cleat Width", on_change=set_visuals_stale)
        with tc3: manage_input_state('max_top_cleat_space_widget_main', 'max_top_cleat_space_ss', st.session_state.max_top_cleat_space_ss); st.number_input("CapSpace (in)", value=st.session_state.max_top_cleat_space_ss, min_value=1.0, step=1.0, format="%.1f", key='max_top_cleat_space_widget_main', help="Max Top Cleat Spacing", on_change=set_visuals_stale)
    with r3c3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Regenerate", type="primary", key="main_regenerate_button_compact", use_container_width=True): st.session_state.regenerate_data_clicked = True
    st.markdown("---"); st.subheader("Calculation Summary")
    if st.session_state.first_data_run_complete:
        if status_module_available: status.display_status(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results)
        if metrics_module_available and st.session_state.overall_dims_for_display: metrics.display_metrics(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
    else: st.info("Welcome! Adjust parameters above and click '🔄 Regenerate' to begin.")

custom_narrow_text_final = config.CUSTOM_NARROW_OPTION_TEXT_UI if config else "Use Custom Narrow Board (Fill < 5.5\")"
ui_inputs_current = {
    'product_weight': st.session_state.get('prod_weight_ss'), 'product_width': st.session_state.get('prod_w_main_value_ss_ctrl_prod_width_in'),
    'product_length': st.session_state.get('prod_l_main_value_ss_ctrl_prod_length_in'), 'product_height': st.session_state.get('prod_h_main_value_ss_ctrl_prod_height_in'),
    'clearance_side': st.session_state.get('clearance_side_ss'), 'clearance_above': st.session_state.get('clearance_above_ss'),
    'panel_thickness': st.session_state.get('panel_thick_ss'), 'wall_cleat_thickness': st.session_state.get('wall_cleat_thick_ss'),
    'wall_cleat_width': st.session_state.get('wall_cleat_width_ss'),
    'selected_floor_nominals': tuple(sorted([opt for opt in st.session_state.get('floor_lumber_ss', []) if opt != custom_narrow_text_final])),
    'allow_custom_narrow': custom_narrow_text_final in st.session_state.get('floor_lumber_ss', []),
    'cap_cleat_thickness': st.session_state.get('cap_cleat_thick_ss'), 'cap_cleat_width': st.session_state.get('cap_cleat_width_ss'),
    'max_top_cleat_spacing': st.session_state.get('max_top_cleat_space_ss'),
}
st.session_state.ui_inputs_current = ui_inputs_current

run_data_calculations = False
if st.session_state.get('regenerate_data_clicked', False):
    run_data_calculations = True; st.session_state.regenerate_data_clicked = False; st.session_state.visuals_are_stale = True
    log.info("Regenerate button clicked. Forcing data and visual recalculation.")
elif not st.session_state.first_data_run_complete:
    run_data_calculations = True; st.session_state.visuals_are_stale = True
    log.info("First run. Forcing data and visual calculation.")

data_actually_changed_in_this_run = False
if run_data_calculations:
    log.info("Running data calculations...")
    product_weight = ui_inputs_current.get('product_weight', default_inputs_init['prod_weight_ss'])
    product_width_input = ui_inputs_current.get('product_width', default_inputs_init['prod_w_main_value_ss_ctrl_prod_width_in'])
    product_length_input = ui_inputs_current.get('product_length', default_inputs_init['prod_l_main_value_ss_ctrl_prod_length_in'])
    product_actual_height = ui_inputs_current.get('product_height', default_inputs_init['prod_h_main_value_ss_ctrl_prod_height_in'])
    clearance_side_product = ui_inputs_current.get('clearance_side', default_inputs_init['clearance_side_ss'])
    clearance_above_product_ui = ui_inputs_current.get('clearance_above', default_inputs_init['clearance_above_ss'])
    panel_thickness_ui = ui_inputs_current.get('panel_thickness', default_inputs_init['panel_thick_ss'])
    wall_cleat_thickness_ui = ui_inputs_current.get('wall_cleat_thickness', default_inputs_init['wall_cleat_thick_ss'])
    wall_cleat_width_ui = ui_inputs_current.get('wall_cleat_width', default_inputs_init['wall_cleat_width_ss'])
    selected_nominal_sizes_tuple_for_cache = ui_inputs_current.get('selected_floor_nominals', tuple())
    allow_custom_narrow = ui_inputs_current.get('allow_custom_narrow', False)
    cap_cleat_actual_thk_ui = ui_inputs_current.get('cap_cleat_thickness', default_inputs_init['cap_cleat_thick_ss'])
    cap_cleat_actual_width_ui = ui_inputs_current.get('cap_cleat_width', default_inputs_init['cap_cleat_width_ss'])
    max_top_cleat_spacing_ui = ui_inputs_current.get('max_top_cleat_spacing', default_inputs_init['max_top_cleat_space_ss'])

    _skid_results = cached_calculate_skid_layout(product_weight, product_width_input, clearance_side_product, panel_thickness_ui, wall_cleat_thickness_ui)
    if _skid_results != st.session_state.skid_results: st.session_state.skid_results = _skid_results; data_actually_changed_in_this_run = True; log.info("Skid results changed.")
    skid_status = _skid_results.get("status", "UNKNOWN") if _skid_results else "ERROR"
    _crate_overall_width = _skid_results.get('crate_width', 0.0) if _skid_results else 0.0
    _crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
    _wall_panel_height_calc = product_actual_height + clearance_above_product_ui

    _floor_results = st.session_state.floor_results
    if floorboard_logic_available and skid_status == "OK" and _skid_results:
        _temp_floor_results = cached_calculate_floorboard_layout(tuple(sorted(_skid_results.items())), product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow)
        if _temp_floor_results != _floor_results: _floor_results = _temp_floor_results; data_actually_changed_in_this_run = True; log.info("Floor results changed.")
    elif _floor_results is None or _floor_results.get("status") != "SKIPPED": _floor_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}; data_actually_changed_in_this_run = True
    st.session_state.floor_results = _floor_results
    
    _skid_actual_height_temp = _skid_results.get('skid_height', 0.0) if _skid_results and skid_status == "OK" else 0.0
    _floor_thickness_temp = config.STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS if config else 1.5
    _cap_panel_thk_prelim_calc = st.session_state.top_panel_results.get("cap_panel_thickness", panel_thickness_ui) if st.session_state.top_panel_results and st.session_state.top_panel_results.get("status") in ["OK", "WARNING"] else panel_thickness_ui
    _cap_cleat_thk_prelim_calc = st.session_state.top_panel_results.get("cap_cleat_spec", {}).get("thickness", cap_cleat_actual_thk_ui) if st.session_state.top_panel_results and st.session_state.top_panel_results.get("status") in ["OK", "WARNING"] else cap_cleat_actual_thk_ui
    _overall_crate_actual_height_for_walls = (_skid_actual_height_temp + _floor_thickness_temp + _wall_panel_height_calc + _cap_panel_thk_prelim_calc + _cap_cleat_thk_prelim_calc)

    _wall_results = st.session_state.wall_results
    if wall_logic_available and config and skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE and _wall_panel_height_calc > config.FLOAT_TOLERANCE:
        _temp_wall_results = cached_calculate_wall_panels(
            _crate_overall_width, _crate_overall_length, _wall_panel_height_calc, 
            panel_thickness_ui, 
            _overall_crate_actual_height_for_walls, 
            wall_cleat_thickness_ui, wall_cleat_width_ui
        )
        if _temp_wall_results != _wall_results: _wall_results = _temp_wall_results; data_actually_changed_in_this_run = True; log.info("Wall results changed.")
    elif _wall_results is None or _wall_results.get("status") != "SKIPPED": _wall_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed_in_this_run = True
    st.session_state.wall_results = _wall_results

    _top_panel_results = st.session_state.top_panel_results
    if cap_logic_available and config and skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE:
        _temp_top_results = cached_calculate_cap_layout(_crate_overall_width, _crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui)
        if _temp_top_results != _top_panel_results: _top_panel_results = _temp_top_results; data_actually_changed_in_this_run = True; log.info("Top Panel results changed.")
    elif _top_panel_results is None or _top_panel_results.get("status") != "SKIPPED": _top_panel_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed_in_this_run = True
    st.session_state.top_panel_results = _top_panel_results

    _skid_actual_height = _skid_results.get('skid_height', 0.0) if _skid_results and skid_status == "OK" else 0.0
    _floor_thickness_actual = config.STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS if config else 1.5
    _cap_panel_thk_final = _top_panel_results.get("cap_panel_thickness", panel_thickness_ui) if _top_panel_results and _top_panel_results.get("status") in ["OK", "WARNING"] else panel_thickness_ui
    _cap_cleat_thk_final = _top_panel_results.get("cap_cleat_spec", {}).get("thickness", cap_cleat_actual_thk_ui) if _top_panel_results and _top_panel_results.get("status") in ["OK", "WARNING"] else cap_cleat_actual_thk_ui
    _crate_overall_height_external = (_skid_actual_height + _floor_thickness_actual + _wall_panel_height_calc + _cap_panel_thk_final + _cap_cleat_thk_final)

    _overall_dims_new = {
        'width': _crate_overall_width, 'length': _crate_overall_length, 'height': _crate_overall_height_external,
        'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height,
        'clearance_top': clearance_above_product_ui, 'skid_height': _skid_actual_height, 'overall_skid_span': None
    }
    if skid_status == "OK" and floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span') and _skid_results:
        _overall_dims_new['overall_skid_span'] = floorboard_logic.calculate_overall_skid_span(_skid_results)
    if _overall_dims_new != st.session_state.overall_dims_for_display:
        st.session_state.overall_dims_for_display = _overall_dims_new; data_actually_changed_in_this_run = True; log.info("Overall dimensions changed.")

    if data_actually_changed_in_this_run or st.session_state.bom_dataframe is None or \
       (isinstance(st.session_state.bom_dataframe, pd.DataFrame) and st.session_state.bom_dataframe.empty and \
        any(st.session_state[res] for res in ['skid_results', 'floor_results', 'wall_results', 'top_panel_results'])):
        log.info("Recompiling BOM data...")
        def compile_bom_data_local(skid_res, floor_res, wall_res, top_res, overall_dims_bom):
            if config is None: log.error("Config not loaded, cannot compile BOM."); return pd.DataFrame()
            bom_list, item_counter = [], 1
            def add_bom_item(qty, part_no, desc): nonlocal item_counter; bom_list.append({"Item No.": item_counter, "Qty": int(qty), "Part No.": part_no, "Description": desc}); item_counter += 1
            if skid_res and skid_res.get("status") == "OK":
                s_cnt, s_len, s_w, s_h, s_type = skid_res.get('skid_count',0), overall_dims_bom.get('length'), skid_res.get('skid_width'), skid_res.get('skid_height'), skid_res.get('skid_type','')
                if s_len and s_w and s_h and s_cnt > 0: add_bom_item(s_cnt,"TBD_SKID_PN",f"SKID, LUMBER, {s_type}, {s_len:.2f}L x {s_w:.2f}W x {s_h:.2f}H")
            if floor_res and floor_res.get("status") in ["OK", "WARNING"]:
                boards, b_len, b_thk = floor_res.get("floorboards",[]), floor_res.get("floorboard_length_across_skids"), getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', 1.5)
                b_groups=defaultdict(int)
                for b in boards: 
                    b_groups[(b.get("nominal"), round(b.get("actual_width",0),3))]+=1
                if b_len and b_groups:
                    for (nom,act_w), qty in b_groups.items():
                        if nom != 'Custom': spec_text = nom
                        else: spec_text = f'Custom {act_w:.2f}" W'
                        desc = f"FLOORBOARD, LUMBER, {spec_text}, {b_len:.2f}L x {act_w:.2f}W x {b_thk:.3f}T"
                        add_bom_item(qty,"TBD_FLOOR_PN",desc)
            if wall_res and wall_res.get("status") == "OK":
                 ply_t, clt_ref = wall_res.get("panel_plywood_thickness_used"), "CLEATED"; ply_s=f"{ply_t:.3f}\" PLY" if ply_t else "PLYWOOD"
                 if wall_res.get("side_panels") and wall_res["side_panels"][0]: sd=wall_res["side_panels"][0]; s_w,s_h=sd.get("panel_width"),sd.get("panel_height"); add_bom_item(2,"TBD_SIDE_PN",f"SIDE PANEL ASSY, {ply_s}, {clt_ref} ({s_w:.2f}L x {s_h:.2f}H)")
                 if wall_res.get("back_panels") and wall_res["back_panels"][0]: bk=wall_res["back_panels"][0]; b_w,b_h=bk.get("panel_width"),bk.get("panel_height"); add_bom_item(2,"TBD_BACK_PN",f"BACK PANEL ASSY, {ply_s}, {clt_ref} ({b_w:.2f}W x {b_h:.2f}H)")
            if top_res and top_res.get("status") in ["OK", "WARNING"]:
                 cap_w,cap_l,cap_ply_t = top_res.get("cap_panel_width"),top_res.get("cap_panel_length"),top_res.get("cap_panel_thickness"); ply_s=f"{cap_ply_t:.3f}\" PLY" if cap_ply_t else "PLYWOOD"
                 if cap_w and cap_l: add_bom_item(1,"TBD_TOP_PN",f"TOP PANEL ASSY, {ply_s}, CLEATED ({cap_l:.2f}L x {cap_w:.2f}W)")
            cols = ["Item No.", "Qty", "Part No.", "Description"]; bom_df = pd.DataFrame(bom_list, columns=cols)
            return bom_df.astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str}) if bom_list else pd.DataFrame(columns=cols).astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str})
        st.session_state.bom_dataframe = compile_bom_data_local(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
        st.session_state.visuals_are_stale = True
    if data_actually_changed_in_this_run: st.session_state.visuals_are_stale = True; st.session_state.visuals_generated_at_least_once = False
    st.session_state.first_data_run_complete = True

st.divider(); st.header("Layout Schematics & Details")
show_visuals_toggle = st.toggle("Show/Update Visuals", value=st.session_state.visuals_toggle_state, key="visuals_toggle_widget_main", help="Toggle ON to generate/update and view schematics. Toggle OFF to hide them.")
if show_visuals_toggle != st.session_state.visuals_toggle_state:
    st.session_state.visuals_toggle_state = show_visuals_toggle; log.info(f"Visuals toggle: {show_visuals_toggle}")
    if not show_visuals_toggle: [st.session_state.update({fig_k: None}) for fig_k in st.session_state if fig_k.startswith('fig_')]; st.session_state.visuals_generated_at_least_once = False
    st.rerun()

if show_visuals_toggle:
    if not st.session_state.first_data_run_complete: st.info("Calculate data via '🔄 Regenerate'.")
    else:
        needs_generation = st.session_state.visuals_are_stale or not st.session_state.visuals_generated_at_least_once
        if needs_generation:
            log.info(f"Visuals need generation. Stale: {st.session_state.visuals_are_stale}, Not generated: {not st.session_state.visuals_generated_at_least_once}")
            with st.spinner("Generating visualization figures..."):
                _s, _f, _w, _t, _od, _ui = st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display, st.session_state.ui_inputs_current
                can_gen_base = _s and _s.get('status')=='OK' and _f and _f.get('status') in ['OK','WARNING'] and _od
                can_gen_walls = _w and _w.get('status')=='OK' and _od
                can_gen_top = _t and _t.get('status') in ['OK','WARNING'] and _od
                [st.session_state.update({fig_k: None}) for fig_k in st.session_state if fig_k.startswith('fig_')] 
                if visualizations_available:
                    if can_gen_base: st.session_state.fig_base_top, st.session_state.fig_base_front, st.session_state.fig_base_side = visualizations.generate_base_assembly_figures(_s, _f, _w, _od, _ui)
                    if can_gen_walls:
                        if _w.get("side_panels") and _w["side_panels"][0]: st.session_state.fig_side_panel_front, st.session_state.fig_side_panel_profile = visualizations.generate_wall_panel_figures(_w["side_panels"][0], "Side Panel", _ui, _od)
                        if _w.get("back_panels") and _w["back_panels"][0]: st.session_state.fig_back_panel_front, st.session_state.fig_back_panel_profile = visualizations.generate_wall_panel_figures(_w["back_panels"][0], "Back Panel", _ui, _od)
                    if can_gen_top: st.session_state.fig_top_panel_front, st.session_state.fig_top_panel_profile = visualizations.generate_top_panel_figures(_t, _ui, _od)
            st.session_state.visuals_are_stale = False; st.session_state.visuals_generated_at_least_once = True; log.info("Visuals generated."); st.rerun()

        if st.session_state.visuals_generated_at_least_once and not st.session_state.visuals_are_stale:
            log.debug("Displaying figures.") 
            
            st.subheader("⚙️ BASE ASSEMBLY")
            _skid_res_exp, _floor_res_exp, _ui_inputs_exp = st.session_state.skid_results, st.session_state.floor_results, st.session_state.ui_inputs_current
            if LOGIC_IMPORTED and hasattr(explanations, 'get_skid_explanation') and _skid_res_exp and _ui_inputs_exp :
                with st.expander("Logic Explanation (Skid/Base)", expanded=False): st.markdown(explanations.get_skid_explanation(_skid_res_exp, _ui_inputs_exp))
            if LOGIC_IMPORTED and hasattr(explanations, 'get_floorboard_explanation') and _floor_res_exp and _ui_inputs_exp:
                with st.expander("Logic Explanation (Floorboard)", expanded=False): st.markdown(explanations.get_floorboard_explanation(_floor_res_exp, _ui_inputs_exp))
            c1,c2,c3=st.columns(3)
            base_views = {'fig_base_top': "Top View (XY)", 'fig_base_front': "Front View (XZ)", 'fig_base_side': "Side View (YZ)"}
            cols = [c1,c2,c3]
            for i, (fig_key, caption) in enumerate(base_views.items()):
                with cols[i]:
                    st.caption(caption)
                    fig_obj = st.session_state.get(fig_key)
                    if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data: # Check if fig_obj and its data attribute are not None
                        st.plotly_chart(fig_obj, use_container_width=True, key=f"base_view_{fig_key}") # Added unique key
                    else: st.caption(f"{caption.split(' (')[0]}: N/A")
            st.divider()

            _wall_res_exp, _od_exp = st.session_state.wall_results, st.session_state.overall_dims_for_display
            _top_res_exp = st.session_state.top_panel_results

            st.subheader("🧱 FRONT ASSEMBLY")
            if LOGIC_IMPORTED and hasattr(explanations, 'get_wall_panel_explanation') and _wall_res_exp and _wall_res_exp.get("back_panels") and _wall_res_exp["back_panels"][0]:
                with st.expander("Logic Explanation (Front Assembly - End Panel Type)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(_wall_res_exp["back_panels"][0], "Front Assembly (End Panel)", _od_exp))
            fc1, fc2 = st.columns(2)
            with fc1:
                st.caption("Front View")
                fig_obj = st.session_state.get('fig_back_panel_front')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="front_assy_fv") # Unique key
                else: st.caption("Front View: N/A")
            with fc2:
                st.caption("Side/Profile View")
                fig_obj = st.session_state.get('fig_back_panel_profile')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="front_assy_pv") # Unique key
                else: st.caption("Side/Profile View: N/A")
            st.divider()

            st.subheader("🧱 BACK PLATE ASSEMBLY")
            if LOGIC_IMPORTED and hasattr(explanations, 'get_wall_panel_explanation') and _wall_res_exp and _wall_res_exp.get("back_panels") and _wall_res_exp["back_panels"][0]:
                with st.expander("Logic Explanation (Back Plate Assembly - End Panel Type)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(_wall_res_exp["back_panels"][0], "Back Plate Assembly (End Panel)", _od_exp))
            bpc1, bpc2 = st.columns(2)
            with bpc1:
                st.caption("Front View")
                fig_obj = st.session_state.get('fig_back_panel_front') # Same figure data as front assembly
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="back_plate_assy_fv") # Unique key
                else: st.caption("Front View: N/A")
            with bpc2:
                st.caption("Side/Profile View")
                fig_obj = st.session_state.get('fig_back_panel_profile') # Same figure data as front assembly
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="back_plate_assy_pv") # Unique key
                else: st.caption("Side/Profile View: N/A")
            st.divider()

            st.subheader("🧱 SIDE PLATE ASSEMBLY")
            if LOGIC_IMPORTED and hasattr(explanations, 'get_wall_panel_explanation') and _wall_res_exp and _wall_res_exp.get("side_panels") and _wall_res_exp["side_panels"][0]:
                with st.expander("Logic Explanation (Side Plate Assembly)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(_wall_res_exp["side_panels"][0], "Side Plate Assembly", _od_exp))
            spc1, spc2 = st.columns(2)
            with spc1:
                st.caption("Front View")
                fig_obj = st.session_state.get('fig_side_panel_front')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="side_plate_assy_fv") # Unique key
                else: st.caption("Front View: N/A")
            with spc2:
                st.caption("Side/Profile View")
                fig_obj = st.session_state.get('fig_side_panel_profile')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="side_plate_assy_pv") # Unique key
                else: st.caption("Side/Profile View: N/A")
            st.divider()

            st.subheader("🧢 TOP PLATE ASSEMBLY")
            if LOGIC_IMPORTED and hasattr(explanations, 'get_top_panel_explanation') and _top_res_exp and _ui_inputs_exp:
                 with st.expander("Logic Explanation (Top Plate Assembly)", expanded=False): st.markdown(explanations.get_top_panel_explanation(_top_res_exp, _ui_inputs_exp))
            tpc1, tpc2 = st.columns(2)
            with tpc1:
                st.caption("Front View (XY)")
                fig_obj = st.session_state.get('fig_top_panel_front')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="top_plate_assy_fv") # Unique key
                else: st.caption("Front View: N/A")
            with tpc2:
                st.caption("Side/Profile View")
                fig_obj = st.session_state.get('fig_top_panel_profile')
                if fig_obj and hasattr(fig_obj, 'data') and fig_obj.data:
                    st.plotly_chart(fig_obj, use_container_width=True, key="top_plate_assy_pv") # Unique key
                else: st.caption("Side/Profile View: N/A")

        elif not st.session_state.visuals_generated_at_least_once and st.session_state.first_data_run_complete : st.info("Visuals will appear on next '🔄 Regenerate'.")
        elif st.session_state.visuals_are_stale and st.session_state.first_data_run_complete: st.warning("Inputs changed. Click '🔄 Regenerate' to update visuals.")

if st.session_state.first_data_run_complete: 
    if details_module_available: details.display_details_tables(st.session_state.wall_results, st.session_state.floor_results, st.session_state.top_panel_results)
    st.divider(); st.subheader("📦 Bill of Materials (BOM)")
    bom_df = st.session_state.get("bom_dataframe")
    if bom_df is not None and not bom_df.empty:
        st.dataframe(bom_df, hide_index=True, use_container_width=True, column_config={"Item No.": st.column_config.NumberColumn(format="%d"), "Qty": st.column_config.NumberColumn(format="%d")})
        try: w,l,h=str(ui_inputs_current.get('product_width','W')).replace('.','_'),str(ui_inputs_current.get('product_length','L')).replace('.','_'),str(ui_inputs_current.get('product_height','H')).replace('.','_'); csv_fn=f"AutoCrate_BOM_{w}W_{l}L_{h}H.csv"
        except: csv_fn="AutoCrate_BOM.csv"
        st.download_button("📥 Download BOM as CSV", bom_df.to_csv(index=False).encode('utf-8'), csv_fn, 'text/csv', key='download_bom_csv_main')
    elif bom_df is not None: st.info("No components for BOM.")
    else: st.error("BOM data N/A.")

    # --- PDF Report Download Button ---
    if st.button("📄 Download PDF Report", key="download_pdf_report_main"):
        if st.session_state.get('bom_dataframe') is not None and \
           not st.session_state.bom_dataframe.empty and \
           st.session_state.get('ui_inputs_current') and \
           LOGIC_IMPORTED and hasattr(pdf_generator, 'create_crate_report'):
            
            report_figures = {}
            figure_keys_titles = {
                'fig_base_top': "Base Assembly - Top View (XY)",
                'fig_base_front': "Base Assembly - Front View (XZ)",
                'fig_base_side': "Base Assembly - Side View (YZ)",
                'fig_back_panel_front': "Front/Back Assembly - Front View", # Using back_panel for front/back assy
                'fig_back_panel_profile': "Front/Back Assembly - Profile View",
                'fig_side_panel_front': "Side Plate Assembly - Front View",
                'fig_side_panel_profile': "Side Plate Assembly - Profile View",
                'fig_top_panel_front': "Top Plate Assembly - Front View (XY)",
                'fig_top_panel_profile': "Top Plate Assembly - Profile View"
            }
            for fig_key, fig_title in figure_keys_titles.items():
                if st.session_state.get(fig_key) is not None:
                    report_figures[fig_title] = st.session_state.get(fig_key)
            
            with st.spinner("Generating PDF report... This may take a moment."):
                pdf_bytes = pdf_generator.create_crate_report(
                    st.session_state.bom_dataframe,
                    report_figures,
                    st.session_state.ui_inputs_current
                )
            pdf_fn = f"AutoCrate_Report_{str(ui_inputs_current.get('product_width','W')).replace('.','_')}W_{str(ui_inputs_current.get('product_length','L')).replace('.','_')}L_{str(ui_inputs_current.get('product_height','H')).replace('.','_')}H.pdf"
            st.download_button(label="📥 Download Report Now", data=pdf_bytes, file_name=pdf_fn, mime="application/pdf", key="final_pdf_download_button")
        else:
            st.warning("BOM data, UI inputs, or PDF generator module not available. Cannot generate report. Please 'Regenerate' first.")

    st.caption(f"AutoCrate Wizard v{APP_VERSION}")
log.info(f"Streamlit app v{APP_VERSION} exec finished.")