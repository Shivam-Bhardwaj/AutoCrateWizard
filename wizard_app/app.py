# wizard_app/app.py
# REV: R_Revert_v3 - Task 1 Modifications
"""
Streamlit application for the AutoCrate Wizard - Parametric Crate Layout System.
Version 0.8.12 (Reverted input labels to plain text, centralized NX style helper)
MODIFIED FOR TASK 1: Robust UI - "Regenerate Crate" Button & Static Output
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
APP_VERSION_FALLBACK = "0.8.12" # Placeholder, actual version from config
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log.info(f"Logger '{log.name}' configured with basicConfig.")

# --- Import Project Modules ---
APP_INITIALIZATION_SUCCESS = True
CONFIG_IMPORTED = False
LOGIC_IMPORTED = False
UI_MODULES_IMPORTED = False
config = None # Initialize config to None
APP_VERSION = APP_VERSION_FALLBACK

# Define NX style for labels - THIS IS THE CRITICAL CSS STRING
NX_LABEL_STYLE_CSS = "color:green; font-weight:bold; font-family: 'Courier New', Courier, monospace;"

def get_nx_label_html(label_text):
    """Helper to create the HTML string for an NX-styled label."""
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
        CONFIG_IMPORTED = False
        APP_INITIALIZATION_SUCCESS = False

try:
    from . import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
    LOGIC_IMPORTED = True
    log.info("Imported logic modules (relative)")
except ImportError:
    log.warning("Relative logic import failed, trying direct...")
    try:
        import skid_logic, floorboard_logic, cap_logic, wall_logic, explanations
        LOGIC_IMPORTED = True
        log.info("Imported logic modules (direct)")
    except ImportError as e:
        log.error(f"CRITICAL: logic modules import failed: {e}", exc_info=True)
        LOGIC_IMPORTED = False
        APP_INITIALIZATION_SUCCESS = False

try:
    from .ui_modules import status, metrics, visualizations, details
    UI_MODULES_IMPORTED = True
    log.info("Imported specific ui_modules (status, metrics, visualizations, details)")
except ImportError:
    log.warning("Relative specific ui_modules import failed, trying direct...")
    try:
        from ui_modules import status, metrics, visualizations, details
        UI_MODULES_IMPORTED = True
        log.info("Imported specific ui_modules (direct)")
    except ImportError as e:
        log.error(f"CRITICAL: specific ui_modules import failed: {e}", exc_info=True)
        APP_INITIALIZATION_SUCCESS = False


st.set_page_config(layout="wide", page_title=f"AutoCrate Wizard v{APP_VERSION}", page_icon="⚙️")

# --- Module Availability Checks ---
floorboard_logic_available = LOGIC_IMPORTED and hasattr(floorboard_logic, 'calculate_floorboard_layout')
cap_logic_available = LOGIC_IMPORTED and hasattr(cap_logic, 'calculate_cap_layout')
wall_logic_available = LOGIC_IMPORTED and hasattr(wall_logic, 'calculate_wall_panels')
details_module_available = UI_MODULES_IMPORTED and hasattr(details, 'display_details_tables')
visualizations_available = UI_MODULES_IMPORTED and hasattr(visualizations, 'generate_base_assembly_figures')
status_module_available = UI_MODULES_IMPORTED and hasattr(status, 'display_status')
metrics_module_available = UI_MODULES_IMPORTED and hasattr(metrics, 'display_metrics')


if not APP_INITIALIZATION_SUCCESS or not CONFIG_IMPORTED or not LOGIC_IMPORTED or not UI_MODULES_IMPORTED:
    st.error(f"Application v{APP_VERSION} failed to initialize due to critical import errors. Check console logs.")
    st.stop()

# --- Caching Wrappers ---
@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness):
    log.debug("CACHE MISS/RECALC: cached_calculate_skid_layout")
    if LOGIC_IMPORTED and hasattr(skid_logic, 'calculate_skid_layout'):
        return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)
    log.error("Skid logic not available for cached_calculate_skid_layout")
    return {"status": "ERROR", "message": "Skid logic module not available."}

@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple_or_dict, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow):
    skid_results_dict = dict(skid_results_tuple_or_dict) if isinstance(skid_results_tuple_or_dict, tuple) else skid_results_tuple_or_dict
    selected_nominal_sizes = list(selected_nominal_sizes_tuple)
    log.debug("CACHE MISS/RECALC: cached_calculate_floorboard_layout")
    if floorboard_logic_available:
        return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)
    log.error("Floorboard logic not available for cached_calculate_floorboard_layout")
    return {"status":"NOT FOUND", "message":"Floorboard logic module not available."}

@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.debug("CACHE MISS/RECALC: cached_calculate_cap_layout")
    if cap_logic_available:
        return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)
    log.error("Cap logic not available for cached_calculate_cap_layout")
    return {"status":"NOT FOUND", "message":"Cap logic module not available."}

@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width):
    log.debug("CACHE MISS/RECALC: cached_calculate_wall_panels")
    if wall_logic_available:
        return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width)
    log.error("Wall logic not available for cached_calculate_wall_panels")
    return {"status":"NOT FOUND", "message":"Wall logic module not available."}

# --- Input Helper Functions ---
def set_visuals_stale():
    """Callback to mark visuals as stale."""
    st.session_state.visuals_are_stale = True
    log.debug("Visuals marked stale due to input change.")

def manage_input_state(widget_key, session_value_key, default_value):
    if session_value_key not in st.session_state:
        st.session_state[session_value_key] = default_value
    # Update session_value_key from widget_key if widget has changed
    if widget_key in st.session_state and st.session_state[widget_key] != st.session_state[session_value_key]:
        st.session_state[session_value_key] = st.session_state[widget_key]
        # set_visuals_stale() # This will be handled by on_change in the widget itself
    return st.session_state[session_value_key]

def input_slider_combo(label_text, min_val, max_val, default_val_from_ss, step, format_str="%.1f", help_text="", key_prefix=""):
    sanitized_label_for_key = label_text.replace(' (in)', '').replace(' (lbs)', '').replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('.', '').lower()

    session_key_value = f"{key_prefix}_value_ss_{sanitized_label_for_key}"
    widget_slider_key = f"{key_prefix}_widget_slider_{sanitized_label_for_key}"
    widget_num_key = f"{key_prefix}_widget_num_{sanitized_label_for_key}"

    if session_key_value not in st.session_state:
        st.session_state[session_key_value] = default_val_from_ss

    current_val_from_state = st.session_state[session_key_value]
    if not (min_val <= current_val_from_state <= max_val): # Ensure current value is within bounds
        current_val_from_state = max(min_val, min(max_val, default_val_from_ss))
        st.session_state[session_key_value] = current_val_from_state

    slider_col, num_col = st.columns([0.75, 0.25])

    with slider_col:
        new_slider_widget_val = st.slider(
            label_text,
            min_val, max_val, value=current_val_from_state, step=step,
            format=format_str, help=help_text, key=widget_slider_key,
            on_change=set_visuals_stale # MODIFICATION: Use on_change callback
        )
        # If slider interaction changes the value, update our primary session state key
        if new_slider_widget_val != st.session_state[session_key_value]:
            st.session_state[session_key_value] = new_slider_widget_val
            # No st.rerun() here. The on_change callback handles marking stale.

    with num_col:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        new_num_widget_val = st.number_input(
            "num_for_" + sanitized_label_for_key,
            min_value=min_val, max_value=max_val, value=st.session_state[session_key_value], # Read from primary session state
            step=step, format=format_str, label_visibility="collapsed", key=widget_num_key,
            help=help_text,
            on_change=set_visuals_stale # MODIFICATION: Use on_change callback
        )
        # If number input changes the value, update our primary session state key
        if new_num_widget_val != st.session_state[session_key_value]:
            st.session_state[session_key_value] = new_num_widget_val
            # No st.rerun() here. The on_change callback handles marking stale.

    return st.session_state[session_key_value]

# --- App Title ---
st.title(f"⚙️ AutoCrate Wizard v{APP_VERSION}")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts.")

# --- Initialize Session State ---
if 'first_data_run_complete' not in st.session_state: st.session_state.first_data_run_complete = False
if 'regenerate_data_clicked' not in st.session_state: st.session_state.regenerate_data_clicked = False
if 'visuals_are_stale' not in st.session_state: st.session_state.visuals_are_stale = True
if 'visuals_generated_at_least_once' not in st.session_state: st.session_state.visuals_generated_at_least_once = False
if 'visuals_toggle_state' not in st.session_state: st.session_state.visuals_toggle_state = True
for key in ['skid_results', 'floor_results', 'wall_results', 'top_panel_results', 'overall_dims_for_display', 'bom_dataframe', 'ui_inputs_current']:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame() if key == 'bom_dataframe' else ({} if key == 'ui_inputs_current' else None)
for fig_key in ['fig_base_top', 'fig_base_front', 'fig_base_side', 'fig_side_panel_front', 'fig_side_panel_profile', 'fig_back_panel_front', 'fig_back_panel_profile', 'fig_top_panel_front', 'fig_top_panel_profile']:
    if fig_key not in st.session_state: st.session_state[fig_key] = None

default_inputs_init = {
    'prod_weight_ss': 1500.0,
    'prod_w_main_value_ss_ctrl_prod_width_in': 90.0,
    'prod_l_main_value_ss_ctrl_prod_length_in': 90.0,
    'prod_h_main_value_ss_ctrl_prod_height_in': 48.0,
    'clearance_side_ss': 2.0,
    'clearance_above_ss': config.DEFAULT_CLEARANCE_ABOVE_PRODUCT if config else 1.5,
    'panel_thick_ss': config.DEFAULT_PANEL_THICKNESS_UI if config else 0.25,
    'wall_cleat_thick_ss': config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75,
    'wall_cleat_width_ss': config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5,
    'floor_lumber_ss': config.DEFAULT_UI_LUMBER_SELECTION_APP if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"],
    'cap_cleat_thick_ss': config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75,
    'cap_cleat_width_ss': config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5,
    'max_top_cleat_space_ss': 24.0,
}
for key, val in default_inputs_init.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- TOP DASHBOARD SECTION (Inputs & Summary) ---
with st.container():
    st.subheader("Input Parameters")

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        # For st.number_input directly using manage_input_state, we pass the callback to st.number_input
        manage_input_state('prod_weight_widget_main', 'prod_weight_ss', st.session_state.prod_weight_ss)
        st.number_input("CTRL_Prod_Weight (lbs)", value=st.session_state.prod_weight_ss,
                        min_value=1.0, max_value=20000.0, step=10.0, format="%.1f",
                        key='prod_weight_widget_main', help="Product Weight",
                        on_change=set_visuals_stale) # MODIFICATION
    with r1c2:
        input_slider_combo("CTRL_Prod_Width (in)", 1.0, 125.0,
                            st.session_state.prod_w_main_value_ss_ctrl_prod_width_in,
                            0.5, "%.1f", "Product Width", key_prefix='prod_w_main')
    with r1c3:
        input_slider_combo("CTRL_Prod_Length (in)", 1.0, 125.0,
                             st.session_state.prod_l_main_value_ss_ctrl_prod_length_in,
                             0.5, "%.1f", "Product Length", key_prefix='prod_l_main')
    with r1c4:
        input_slider_combo("CTRL_Prod_Height (in)", 1.0, 120.0,
                             st.session_state.prod_h_main_value_ss_ctrl_prod_height_in,
                             0.5, "%.1f", "Product Height", key_prefix='prod_h_main')

    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5)
    with r2c1:
        manage_input_state('clearance_side_widget_main', 'clearance_side_ss', st.session_state.clearance_side_ss)
        st.number_input("CTRL_Clearance_Side (in)", value=st.session_state.clearance_side_ss,
                        min_value=0.0, step=0.1, format="%.2f", key='clearance_side_widget_main', help="Side Clearance",
                        on_change=set_visuals_stale) # MODIFICATION
    with r2c2:
        manage_input_state('clearance_above_widget_main', 'clearance_above_ss',  st.session_state.clearance_above_ss)
        st.number_input("CTRL_Clearance_Top (in)", value=st.session_state.clearance_above_ss,
                        min_value=0.0, step=0.1, format="%.2f", key='clearance_above_widget_main', help="Top Clearance",
                        on_change=set_visuals_stale) # MODIFICATION
    with r2c3:
        manage_input_state('panel_thick_widget_main', 'panel_thick_ss', st.session_state.panel_thick_ss)
        st.number_input("CTRL_Panel_Thickness (in)", value=st.session_state.panel_thick_ss,
                        min_value=0.01, step=0.01, format="%.2f", key='panel_thick_widget_main', help="Panel Thickness",
                        on_change=set_visuals_stale) # MODIFICATION
    with r2c4:
        manage_input_state('wall_cleat_thick_widget_main', 'wall_cleat_thick_ss', st.session_state.wall_cleat_thick_ss)
        st.number_input("CTRL_Wall_Cleat_Thk (in)", value=st.session_state.wall_cleat_thick_ss,
                        min_value=0.01, step=0.01, format="%.2f", key='wall_cleat_thick_widget_main', help="Wall Cleat Thickness",
                        on_change=set_visuals_stale) # MODIFICATION
    with r2c5:
        manage_input_state('wall_cleat_width_widget_main', 'wall_cleat_width_ss', st.session_state.wall_cleat_width_ss)
        st.number_input("CTRL_Wall_Cleat_Wdh (in)", value=st.session_state.wall_cleat_width_ss,
                        min_value=0.1, step=0.1, format="%.1f", key='wall_cleat_width_widget_main', help="Wall Cleat Width",
                        on_change=set_visuals_stale) # MODIFICATION

    r3c1, r3c2, r3c3 = st.columns([2.5, 2.5, 1])
    with r3c1:
        st.caption("CTRL_Floor_Lumber_Options")
        all_lumber_opts = config.ALL_LUMBER_OPTIONS_UI if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"]
        manage_input_state('floor_lumber_widget_main', 'floor_lumber_ss', st.session_state.floor_lumber_ss)
        st.multiselect("Floor Lumber Options",
                        options=all_lumber_opts,
                        default=st.session_state.floor_lumber_ss,
                        key='floor_lumber_widget_main', help="Available Floorboard Lumber",
                        on_change=set_visuals_stale) # MODIFICATION
    with r3c2:
        st.caption("CTRL_Cap_Cleat_Options")
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            manage_input_state('cap_cleat_thick_widget_main', 'cap_cleat_thick_ss', st.session_state.cap_cleat_thick_ss)
            st.number_input("CapThk (in)", value=st.session_state.cap_cleat_thick_ss,
                            min_value=0.1, step=0.01, format="%.2f", key='cap_cleat_thick_widget_main', help="Top Cleat Thickness",
                            on_change=set_visuals_stale) # MODIFICATION
        with tc2:
            manage_input_state('cap_cleat_width_widget_main', 'cap_cleat_width_ss', st.session_state.cap_cleat_width_ss)
            st.number_input("CapWdh (in)", value=st.session_state.cap_cleat_width_ss,
                            min_value=0.1, step=0.1, format="%.1f", key='cap_cleat_width_widget_main', help="Top Cleat Width",
                            on_change=set_visuals_stale) # MODIFICATION
        with tc3:
            manage_input_state('max_top_cleat_space_widget_main', 'max_top_cleat_space_ss', st.session_state.max_top_cleat_space_ss)
            st.number_input("CapSpace (in)", value=st.session_state.max_top_cleat_space_ss,
                            min_value=1.0, step=1.0, format="%.1f", key='max_top_cleat_space_widget_main', help="Max Top Cleat Spacing",
                            on_change=set_visuals_stale) # MODIFICATION
    with r3c3:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Regenerate", type="primary", key="main_regenerate_button_compact", use_container_width=True):
            st.session_state.regenerate_data_clicked = True
            # A rerun is triggered by Streamlit when a button is clicked.
            # The regenerate_data_clicked flag will be handled in the data calculation logic.

    st.markdown("---")
    st.subheader("Calculation Summary")
    if st.session_state.first_data_run_complete:
        if status_module_available:
            status.display_status(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results)
        else:
            st.warning("Status display module not available.")

        if metrics_module_available and st.session_state.overall_dims_for_display:
            metrics.display_metrics(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
        elif not metrics_module_available:
            st.warning("Metrics display module not available.")
    else:
        st.info("Welcome! Adjust parameters above and click '🔄 Regenerate' to begin.")

# --- Collect current inputs from session state ---
custom_narrow_text_final = config.CUSTOM_NARROW_OPTION_TEXT_UI if config else "Use Custom Narrow Board (Fill < 5.5\")"
ui_inputs_current = {
    'product_weight': st.session_state.get('prod_weight_ss'),
    'product_width': st.session_state.get('prod_w_main_value_ss_ctrl_prod_width_in'),
    'product_length': st.session_state.get('prod_l_main_value_ss_ctrl_prod_length_in'),
    'product_height': st.session_state.get('prod_h_main_value_ss_ctrl_prod_height_in'),
    'clearance_side': st.session_state.get('clearance_side_ss'),
    'clearance_above': st.session_state.get('clearance_above_ss'),
    'panel_thickness': st.session_state.get('panel_thick_ss'),
    'wall_cleat_thickness': st.session_state.get('wall_cleat_thick_ss'),
    'wall_cleat_width': st.session_state.get('wall_cleat_width_ss'),
    'selected_floor_nominals': tuple(sorted([opt for opt in st.session_state.get('floor_lumber_ss', []) if opt != custom_narrow_text_final])),
    'allow_custom_narrow': custom_narrow_text_final in st.session_state.get('floor_lumber_ss', []),
    'cap_cleat_thickness': st.session_state.get('cap_cleat_thick_ss'),
    'cap_cleat_width': st.session_state.get('cap_cleat_width_ss'),
    'max_top_cleat_spacing': st.session_state.get('max_top_cleat_space_ss'),
}
st.session_state.ui_inputs_current = ui_inputs_current

# --- Data Calculation Logic ---
run_data_calculations = False
if st.session_state.get('regenerate_data_clicked', False): # MODIFICATION: Primary trigger
    run_data_calculations = True
    st.session_state.regenerate_data_clicked = False # Reset flag
    st.session_state.visuals_are_stale = True # Ensure visuals regenerate
    log.info("Regenerate button clicked. Forcing data and visual recalculation.")
elif not st.session_state.first_data_run_complete: # MODIFICATION: Also run on first load
    run_data_calculations = True
    st.session_state.visuals_are_stale = True # Ensure visuals generate on first load
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
    if _skid_results != st.session_state.skid_results:
        st.session_state.skid_results = _skid_results; data_actually_changed_in_this_run = True; log.info("Skid results changed.")

    skid_status = _skid_results.get("status", "UNKNOWN") if _skid_results else "ERROR"
    _crate_overall_width = _skid_results.get('crate_width', 0.0) if _skid_results else 0.0
    _crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
    _wall_panel_height_calc = product_actual_height + clearance_above_product_ui

    _floor_results = st.session_state.floor_results
    if floorboard_logic_available:
        if skid_status == "OK" and _skid_results:
             skid_input_for_floor = tuple(sorted(_skid_results.items()))
             _temp_floor_results = cached_calculate_floorboard_layout(skid_input_for_floor, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow)
             if _temp_floor_results != _floor_results: _floor_results = _temp_floor_results; data_actually_changed_in_this_run = True; log.info("Floor results changed.")
        elif _floor_results is None or _floor_results.get("status") != "SKIPPED": _floor_results = {"status": "SKIPPED", "message": f"Skid: {skid_status}."}; data_actually_changed_in_this_run = True
    st.session_state.floor_results = _floor_results

    _wall_results = st.session_state.wall_results
    if wall_logic_available and config:
        if skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE and _wall_panel_height_calc > config.FLOAT_TOLERANCE:
            _temp_wall_results = cached_calculate_wall_panels(_crate_overall_width, _crate_overall_length, _wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui)
            if _temp_wall_results != _wall_results: _wall_results = _temp_wall_results; data_actually_changed_in_this_run = True; log.info("Wall results changed.")
        elif _wall_results is None or _wall_results.get("status") != "SKIPPED": _wall_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed_in_this_run = True
    st.session_state.wall_results = _wall_results

    _top_panel_results = st.session_state.top_panel_results
    if cap_logic_available and config:
        if skid_status == "OK" and _crate_overall_width > config.FLOAT_TOLERANCE and _crate_overall_length > config.FLOAT_TOLERANCE:
            _temp_top_results = cached_calculate_cap_layout(_crate_overall_width, _crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui)
            if _temp_top_results != _top_panel_results: _top_panel_results = _temp_top_results; data_actually_changed_in_this_run = True; log.info("Top Panel results changed.")
        elif _top_panel_results is None or _top_panel_results.get("status") != "SKIPPED": _top_panel_results = {"status": "SKIPPED", "message": f"Skid: {skid_status} or invalid dims."}; data_actually_changed_in_this_run = True
    st.session_state.top_panel_results = _top_panel_results

    _skid_actual_height = _skid_results.get('skid_height', 0.0) if _skid_results else 0.0
    _crate_overall_height_external = (_skid_actual_height + panel_thickness_ui + _wall_panel_height_calc + panel_thickness_ui + cap_cleat_actual_thk_ui)
    _overall_dims_new = { 'width': _crate_overall_width, 'length': _crate_overall_length, 'height': _crate_overall_height_external, 'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height, 'clearance_top': clearance_above_product_ui, 'skid_height': _skid_actual_height, 'overall_skid_span': None }
    if skid_status == "OK" and floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span') and _skid_results:
        _overall_dims_new['overall_skid_span'] = floorboard_logic.calculate_overall_skid_span(_skid_results)
    if _overall_dims_new != st.session_state.overall_dims_for_display:
        st.session_state.overall_dims_for_display = _overall_dims_new; data_actually_changed_in_this_run = True; log.info("Overall dimensions changed.")

    if data_actually_changed_in_this_run or st.session_state.bom_dataframe is None or \
       (isinstance(st.session_state.bom_dataframe, pd.DataFrame) and st.session_state.bom_dataframe.empty and \
        (st.session_state.skid_results or st.session_state.floor_results or st.session_state.wall_results or st.session_state.top_panel_results)):
        log.info("Recompiling BOM data...")
        def compile_bom_data_local(skid_res, floor_res, wall_res, top_res, overall_dims_bom):
            if config is None: log.error("Config not loaded, cannot compile BOM."); return pd.DataFrame()
            bom_list = []; item_counter = 1
            def add_bom_item(qty, part_no_placeholder, description):
                nonlocal item_counter
                if qty is not None and qty > 0:
                    bom_list.append({"Item No.": item_counter, "Qty": int(qty), "Part No.": part_no_placeholder, "Description": description}); item_counter += 1
            if skid_res and skid_res.get("status") == "OK":
                skid_count=skid_res.get('skid_count',0); skid_len_val=overall_dims_bom.get('length'); skid_w=skid_res.get('skid_width'); skid_h=skid_res.get('skid_height'); skid_type=skid_res.get('skid_type','')
                if skid_len_val and skid_w and skid_h and skid_count > 0: desc=f"SKID, LUMBER, {skid_type}, {skid_len_val:.2f}L x {skid_w:.2f}W x {skid_h:.2f}H"; add_bom_item(skid_count,"TBD_SKID_PN",desc)
            if floor_res and floor_res.get("status") in ["OK", "WARNING"]:
                boards=floor_res.get("floorboards",[]); board_len_val=floor_res.get("floorboard_length_across_skids"); board_thickness = getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', 1.5)
                board_groups=defaultdict(int);
                if boards:
                    for board in boards: key=(board.get("nominal"), round(board.get("actual_width",0),3)); board_groups[key]+=1
                if board_len_val and board_groups:
                    for (nominal,actual_width), quantity in board_groups.items():
                        spec=nominal if nominal!="Custom" else f"Custom {actual_width:.2f}\" W"; desc=f"FLOORBOARD, LUMBER, {spec}, {board_len_val:.2f}L x {actual_width:.2f}W x {board_thickness:.3f}T"; add_bom_item(quantity,"TBD_FLOOR_PN",desc)
            if wall_res and wall_res.get("status") == "OK":
                 ply_thick_val=wall_res.get("panel_plywood_thickness_used"); ply_spec=f"{ply_thick_val:.3f}\" PLY" if ply_thick_val else "PLYWOOD"; cleat_ref="CLEATED"
                 if wall_res.get("side_panels") and wall_res["side_panels"][0]:
                     side_panel_data = wall_res["side_panels"][0]; side_w_bom,side_h_bom=side_panel_data.get("panel_width"),side_panel_data.get("panel_height")
                     if side_w_bom and side_h_bom: desc=f"SIDE PANEL ASSY, {ply_spec}, {cleat_ref} ({side_w_bom:.2f}L x {side_h_bom:.2f}H)"; add_bom_item(2,"TBD_SIDE_PN",desc)
                 if wall_res.get("back_panels") and wall_res["back_panels"][0]:
                     back_panel_data = wall_res["back_panels"][0]; back_w_bom,back_h_bom=back_panel_data.get("panel_width"),back_panel_data.get("panel_height")
                     if back_w_bom and back_h_bom: desc=f"BACK PANEL ASSY, {ply_spec}, {cleat_ref} ({back_w_bom:.2f}W x {back_h_bom:.2f}H)"; add_bom_item(2,"TBD_BACK_PN",desc)
            if top_res and top_res.get("status") in ["OK", "WARNING"]:
                 cap_w_bom=top_res.get("cap_panel_width"); cap_l_bom=top_res.get("cap_panel_length"); cap_ply_thick_val=top_res.get("cap_panel_thickness"); ply_spec=f"{cap_ply_thick_val:.3f}\" PLY" if cap_ply_thick_val else "PLYWOOD"; cleat_ref="CLEATED"
                 if cap_w_bom and cap_l_bom: desc=f"TOP PANEL ASSY, {ply_spec}, {cleat_ref} ({cap_l_bom:.2f}L x {cap_w_bom:.2f}W)"; add_bom_item(1,"TBD_TOP_PN",desc)
            final_columns = ["Item No.", "Qty", "Part No.", "Description"]; bom_df = pd.DataFrame(bom_list, columns=final_columns)
            if bom_list: bom_df["Item No."] = bom_df["Item No."].astype(int); bom_df["Qty"] = bom_df["Qty"].astype(int)
            else: bom_df = pd.DataFrame(columns=final_columns).astype({"Item No.": int, "Qty": int, "Part No.": str, "Description": str})
            return bom_df
        st.session_state.bom_dataframe = compile_bom_data_local(st.session_state.skid_results, st.session_state.floor_results, st.session_state.wall_results, st.session_state.top_panel_results, st.session_state.overall_dims_for_display)
        st.session_state.visuals_are_stale = True # Mark visuals stale if BOM changed

    if data_actually_changed_in_this_run: # If any core data changed, visuals must be stale
        st.session_state.visuals_are_stale = True
        st.session_state.visuals_generated_at_least_once = False # This ensures they WILL regenerate if toggle is on
        log.info("Core data changed, visuals marked stale and needing regeneration.")

    st.session_state.first_data_run_complete = True


# --- MAIN CONTENT AREA (Scrollable, starts after the dashboard) ---
st.divider()
st.header("Layout Schematics & Details")

show_visuals_toggle = st.toggle(
    "Show/Update Visuals",
    value=st.session_state.visuals_toggle_state,
    key="visuals_toggle_widget_main",
    help="Toggle ON to generate/update and view schematics. Toggle OFF to hide and clear them."
)
if show_visuals_toggle != st.session_state.visuals_toggle_state:
    st.session_state.visuals_toggle_state = show_visuals_toggle
    log.info(f"Visuals toggle changed to: {show_visuals_toggle}")
    if not show_visuals_toggle: # If toggled OFF
         for fig_k in st.session_state.keys(): # Clear all figure states
            if fig_k.startswith('fig_'): st.session_state[fig_k] = None
         st.session_state.visuals_generated_at_least_once = False
         # visuals_are_stale remains True or becomes True, which is fine.
         st.rerun() # Rerun to reflect the change in display (hide visuals)

if show_visuals_toggle:
    if not st.session_state.first_data_run_complete:
        st.info("Calculate data first by adjusting parameters above and clicking '🔄 Regenerate'.")
    else:
        # Determine if visuals need generation:
        # - If they are marked stale (due to input change or data recalc)
        # - OR if they haven't been generated at least once since toggle was last turned on.
        needs_generation = (st.session_state.visuals_are_stale or not st.session_state.visuals_generated_at_least_once)

        if needs_generation:
            log.info(f"Visuals toggle is ON and visuals need generation/update. Stale: {st.session_state.visuals_are_stale}, Not generated once: {not st.session_state.visuals_generated_at_least_once}")
            with st.spinner("Generating visualization figures..."):
                _skid_res = st.session_state.skid_results; _floor_res = st.session_state.floor_results
                _wall_res = st.session_state.wall_results; _top_res = st.session_state.top_panel_results
                _overall_dims = st.session_state.overall_dims_for_display; _ui_inputs = st.session_state.ui_inputs_current

                can_generate_base = _skid_res and _skid_res.get('status') == 'OK' and \
                                    _floor_res and _floor_res.get('status') in ['OK', 'WARNING'] and \
                                    _overall_dims
                log.info(f"Base generation check: skid_ok={_skid_res.get('status') if _skid_res else 'None'}, floor_ok={_floor_res.get('status') if _floor_res else 'None'}, overall_dims_present={bool(_overall_dims)}")

                can_generate_walls = _wall_res and _wall_res.get('status') == 'OK' and _overall_dims
                can_generate_top = _top_res and _top_res.get('status') in ['OK', 'WARNING'] and _overall_dims

                # Clear previous figures from session state before regenerating
                for fig_k in st.session_state.keys():
                     if fig_k.startswith('fig_'): st.session_state[fig_k] = None

                if visualizations_available:
                    if can_generate_base:
                         try:
                             st.session_state.fig_base_top, st.session_state.fig_base_front, st.session_state.fig_base_side = visualizations.generate_base_assembly_figures(_skid_res, _floor_res, _wall_res, _overall_dims, _ui_inputs)
                             log.info(f"Base figures generated. fig_base_top: {bool(st.session_state.fig_base_top)}")
                         except Exception as e: log.error(f"Error generating base figures: {e}", exc_info=True)
                    else:
                        log.warning("Skipping base figure generation due to unmet conditions.")

                    if can_generate_walls:
                         try:
                             if _wall_res.get("side_panels") and _wall_res["side_panels"][0]: st.session_state.fig_side_panel_front, st.session_state.fig_side_panel_profile = visualizations.generate_wall_panel_figures(_wall_res["side_panels"][0], "Side Panel", _ui_inputs, _overall_dims)
                             if _wall_res.get("back_panels") and _wall_res["back_panels"][0]: st.session_state.fig_back_panel_front, st.session_state.fig_back_panel_profile = visualizations.generate_wall_panel_figures(_wall_res["back_panels"][0], "Back Panel", _ui_inputs, _overall_dims)
                             log.info("Wall figures generated.")
                         except Exception as e: log.error(f"Error generating wall figures: {e}", exc_info=True)
                    else: log.warning("Skipping wall figure generation.")

                    if can_generate_top:
                         try: st.session_state.fig_top_panel_front, st.session_state.fig_top_panel_profile = visualizations.generate_top_panel_figures(_top_res, _ui_inputs, _overall_dims); log.info("Top panel figures generated.")
                         except Exception as e: log.error(f"Error generating top panel figures: {e}", exc_info=True)
                    else: log.warning("Skipping top panel figure generation.")

            st.session_state.visuals_are_stale = False # Reset stale flag
            st.session_state.visuals_generated_at_least_once = True # Mark as generated
            log.info("Visual generation attempt complete."); st.rerun() # Rerun to display new figures

        # This block executes if visuals are supposed to be shown, are not stale, and have been generated once.
        if st.session_state.visuals_generated_at_least_once and not st.session_state.visuals_are_stale:
            log.debug("Displaying figures from session state.")
            st.subheader("⚙️ BASE ASSEMBLY")
            _skid_res_exp = st.session_state.skid_results; _floor_res_exp = st.session_state.floor_results; _ui_inputs_exp = st.session_state.ui_inputs_current
            if _skid_res_exp and _ui_inputs_exp and LOGIC_IMPORTED and hasattr(explanations, 'get_skid_explanation'):
                with st.expander("Logic Explanation (Skid/Base)", expanded=False): st.markdown(explanations.get_skid_explanation(skid_results=_skid_res_exp, ui_inputs=_ui_inputs_exp))
            if _floor_res_exp and _ui_inputs_exp and LOGIC_IMPORTED and hasattr(explanations, 'get_floorboard_explanation'):
                with st.expander("Logic Explanation (Floorboard)", expanded=False): st.markdown(explanations.get_floorboard_explanation(floor_results=_floor_res_exp, ui_inputs=_ui_inputs_exp))

            col_base1, col_base2, col_base3 = st.columns(3)
            with col_base1:
                st.caption("Top View (XY Plane)")
                fig = st.session_state.get('fig_base_top')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Base Top View: Not Available or No Data")
            with col_base2:
                st.caption("Front View (XZ Plane)")
                fig = st.session_state.get('fig_base_front')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Base Front View: Not Available or No Data")
            with col_base3:
                st.caption("Side View (YZ Plane)")
                fig = st.session_state.get('fig_base_side')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Base Side View: Not Available or No Data")

            st.divider(); st.subheader("🧱 Wall Panel Assemblies")
            _wall_res_exp = st.session_state.wall_results; _overall_dims_exp = st.session_state.overall_dims_for_display
            st.markdown("#### SIDE PANEL ASSEMBLY (Runs along Crate Length)")
            if _wall_res_exp and _overall_dims_exp and _wall_res_exp.get("side_panels") and _wall_res_exp["side_panels"][0] and LOGIC_IMPORTED and hasattr(explanations, 'get_wall_panel_explanation'):
                 with st.expander("Logic Explanation (Side Panel)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(panel_data=_wall_res_exp["side_panels"][0], panel_type_label="Side Panel", overall_dims=_overall_dims_exp))
            col_wall_side1, col_wall_side2 = st.columns(2)
            with col_wall_side1:
                st.caption("Front View (XZ Plane)")
                fig = st.session_state.get('fig_side_panel_front')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Side Panel Front View: Not Available or No Data")
            with col_wall_side2:
                st.caption("Profile View (ZY Plane)")
                fig = st.session_state.get('fig_side_panel_profile')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Side Panel Profile View: Not Available or No Data")

            st.markdown("<br>", unsafe_allow_html=True); st.markdown("#### BACK PANEL ASSEMBLY (Runs along Crate Width)")
            if _wall_res_exp and _overall_dims_exp and _wall_res_exp.get("back_panels") and _wall_res_exp["back_panels"][0] and LOGIC_IMPORTED and hasattr(explanations, 'get_wall_panel_explanation'):
                 with st.expander("Logic Explanation (Back Panel)", expanded=False): st.markdown(explanations.get_wall_panel_explanation(panel_data=_wall_res_exp["back_panels"][0], panel_type_label="Back Panel", overall_dims=_overall_dims_exp))
            col_wall_back1, col_wall_back2 = st.columns(2)
            with col_wall_back1:
                st.caption("Front View (XZ Plane)")
                fig = st.session_state.get('fig_back_panel_front')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Back Panel Front View: Not Available or No Data")
            with col_wall_back2:
                st.caption("Profile View (ZY Plane)")
                fig = st.session_state.get('fig_back_panel_profile')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Back Panel Profile View: Not Available or No Data")

            st.divider(); st.subheader("🧢 Top Panel Assembly")
            _top_res_exp = st.session_state.top_panel_results
            if _top_res_exp and _overall_dims_exp and LOGIC_IMPORTED and hasattr(explanations, 'get_top_panel_explanation') and _ui_inputs_exp :
                with st.expander("Logic Explanation (Top Panel)", expanded=False): st.markdown(explanations.get_top_panel_explanation(top_panel_results=_top_res_exp, ui_inputs=_ui_inputs_exp))
            col_top1, col_top2 = st.columns(2)
            with col_top1:
                st.caption("Front View (XY Plane)")
                fig = st.session_state.get('fig_top_panel_front')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Top Panel Front View: Not Available or No Data")
            with col_top2:
                st.caption("Profile View (YZ Plane)")
                fig = st.session_state.get('fig_top_panel_profile')
                if fig and hasattr(fig, 'data') and fig.data:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.caption("Top Panel Profile View: Not Available or No Data")

        elif not st.session_state.visuals_generated_at_least_once and st.session_state.first_data_run_complete :
             st.info("Visuals are set to display but have not been generated yet. Click '🔄 Regenerate' or they will appear on the next successful data calculation if data changes.")
        elif st.session_state.visuals_are_stale and st.session_state.first_data_run_complete:
             st.warning("Input parameters have changed. Click '🔄 Regenerate' to update calculations and visuals.")


# --- Display Details and BOM ---
if st.session_state.first_data_run_complete:
    if details_module_available:
        details.display_details_tables(st.session_state.wall_results, st.session_state.floor_results, st.session_state.top_panel_results)

    st.divider(); st.subheader("📦 Bill of Materials (BOM)")
    bom_df_display = st.session_state.get("bom_dataframe")
    ui_inputs_for_filename = st.session_state.get('ui_inputs_current', {})

    if bom_df_display is not None and not bom_df_display.empty:
        st.dataframe(bom_df_display, hide_index=True, use_container_width=True, column_config={"Item No.": st.column_config.NumberColumn(format="%d"), "Qty": st.column_config.NumberColumn(format="%d")})
        try:
            prod_w_str = str(ui_inputs_for_filename.get('product_width', 'W')).replace('.', '_'); prod_l_str = str(ui_inputs_for_filename.get('product_length', 'L')).replace('.', '_'); prod_h_str = str(ui_inputs_for_filename.get('product_height', 'H')).replace('.', '_')
            csv_filename = f"AutoCrate_BOM_{prod_w_str}W_{prod_l_str}L_{prod_h_str}H.csv"
        except Exception: csv_filename = "AutoCrate_BOM.csv"
        csv_export_data = bom_df_display.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Download BOM as CSV", data=csv_export_data, file_name=csv_filename, mime='text/csv', key='download_bom_csv_button_main')
    elif bom_df_display is not None: st.info("No components generated for Bill of Materials.")
    else: st.error("Bill of Materials data is not available or compilation failed.")

    st.caption(f"AutoCrate Wizard v{APP_VERSION} - For inquiries, contact project maintainer.")

log.info(f"Streamlit app v{APP_VERSION} script execution finished.")