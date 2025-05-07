# wizard_app/app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid, Floorboard & Cap Layout System.
Modularized version with enhanced visualizations and BOM generation.
Reflects production naming conventions and view orientations.
"""

# 1. Standard library imports
import sys
import os
import logging
import math
from collections import Counter
import io # For BytesIO with download button

# 2. Third-party library imports
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 3. Your __main__ block for path adjustments
if __name__ == "__main__" and __package__ is None:
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_script_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    __package__ = "wizard_app"

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="AutoCrate Wizard", page_icon="⚙️")

# --- Setup Logging ---
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log.info(f"Logger '{log.name}' configured.")

# --- Import Your Project Modules ---
try:
    from wizard_app import config, skid_logic, floorboard_logic, cap_logic, wall_logic, explanations, bom_utils
    from wizard_app.ui_modules import sidebar, status, metrics, visualizations, details

    floorboard_logic_available = hasattr(floorboard_logic, 'calculate_floorboard_layout')
    cap_logic_available = hasattr(cap_logic, 'calculate_cap_layout')
    wall_logic_available = hasattr(wall_logic, 'calculate_wall_panels')
    details_module_available = hasattr(details, 'display_details_tables')
    bom_utils_available = ('bom_utils' in sys.modules and hasattr(bom_utils, 'compile_bom_data') and hasattr(bom_utils, 'generate_bom_pdf_bytes'))
    if bom_utils_available and not hasattr(bom_utils, 'FPDF') or getattr(bom_utils, 'FPDF') is None: log.warning("bom_utils imported, but FPDF2 library seems unavailable.")

    log.info("Successfully imported all project modules.")

except ImportError as e:
    log.error(f"CRITICAL ERROR: Could not import one or more project modules: {e}", exc_info=True)
    try: st.error(f"Application Initialization Error: Could not load critical components. Details: {e}"); st.caption("Check console logs.")
    except NameError: print(f"FATAL ERROR during import: {e}. Streamlit UI cannot be shown.")
    st.stop()

# --- Main Application Title ---
st.title("⚙️ AutoCrate Wizard - Parametric Crate Layout System")
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
    if not floorboard_logic_available: return {"status": "NOT FOUND", "message": "floorboard_logic.py missing."}
    return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)
@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.debug("CACHE MISS or RECALC: cached_calculate_cap_layout");
    if not cap_logic_available: return {"status": "NOT FOUND", "message": "cap_logic.py missing."}
    return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)
@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width):
    log.debug("CACHE MISS or RECALC: cached_calculate_wall_panels");
    if not wall_logic_available: return {"status": "NOT FOUND", "message": "wall_logic.py missing."}
    return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width)

# --- Sidebar Inputs ---
ui_inputs = sidebar.display_sidebar()

# --- Core Logic Execution ---
product_weight = ui_inputs.get('product_weight'); product_width_input = ui_inputs.get('product_width'); product_length_input = ui_inputs.get('product_length'); product_actual_height = ui_inputs.get('product_height')
clearance_side_product = ui_inputs.get('clearance_side'); clearance_above_product_ui = ui_inputs.get('clearance_above'); panel_thickness_ui = ui_inputs.get('panel_thickness')
wall_cleat_thickness_ui = ui_inputs.get('wall_cleat_thickness'); wall_cleat_width_ui = ui_inputs.get('wall_cleat_width')
selected_nominal_sizes_tuple_for_cache = ui_inputs.get('selected_floor_nominals', tuple()); allow_custom_narrow = ui_inputs.get('allow_custom_narrow', False)
cap_cleat_actual_thk_ui = ui_inputs.get('cap_cleat_thickness'); cap_cleat_actual_width_ui = ui_inputs.get('cap_cleat_width'); max_top_cleat_spacing_ui = ui_inputs.get('max_top_cleat_spacing')
log.info(f"UI Inputs captured: {ui_inputs}")

# Initialize results
skid_results, floor_results, wall_results, top_panel_results = {}, {}, {}, {}; skid_status = "NOT RUN"
skid_results = {"status": "NOT RUN", "message": "Init"}; floor_results = {"status": "NOT RUN", "message": "Init"}; wall_results = {"status": "NOT RUN", "message": "Init"}; top_panel_results = {"status": "NOT RUN", "message": "Init"}

# Calculations ( Skid -> Derived Dims -> Floor/Cap/Wall )
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
status.display_status(skid_results, floor_results, wall_results, top_panel_results)

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
metrics.display_metrics(skid_results, floor_results, wall_results, top_panel_results, overall_dims_for_display)

# --- Main Area Display (Schematics) ---
st.divider(); st.header("📐 Layout Schematics")

# Display Base Assembly Views (Top XY, Front XZ, Side YZ)
visualizations.display_base_assembly_views(skid_results, floor_results, wall_results, overall_dims_for_display, ui_inputs)

# Display Wall Panel Visualizations (Front XZ, Profile ZY/ZX)
st.divider(); st.subheader("Wall Panel Assembly Schematics")
if wall_logic_available and wall_results and wall_results.get("status") == "OK":
    side_panel_data = wall_results.get("side_panels", [{}])[0]
    back_panel_data = wall_results.get("back_panels", [{}])[0]
    visualizations.display_wall_assembly(side_panel_data, "Side Panel", ui_inputs, overall_dims_for_display)
    st.markdown("<br>", unsafe_allow_html=True)
    visualizations.display_wall_assembly(back_panel_data, "Back Panel", ui_inputs, overall_dims_for_display)
elif wall_results: st.info(f"Wall panel schematics cannot be displayed. Status: {wall_results.get('status', 'N/A')}, Message: {wall_results.get('message', 'No message')}")
else: st.info("Wall panel calculation pending or wall logic module not available.")

# Display Top Panel Visualizations (Front XY, Profile YZ/YX)
st.divider(); st.subheader("Top Panel Assembly Schematics")
if cap_logic_available and top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
    visualizations.display_top_panel_assembly(top_panel_results, ui_inputs, overall_dims_for_display)
elif top_panel_results: st.info(f"Top panel schematics cannot be displayed. Status: {top_panel_results.get('status', 'N/A')}, Message: {top_panel_results.get('message', 'No message')}")
else: st.info("Top panel calculation pending or cap logic module not available.")

# --- Details Tables ---
if details_module_available: details.display_details_tables(wall_results, floor_results, top_panel_results)
else: st.warning("Details display module not available.")

# --- BOM Section ---
st.divider(); st.subheader("📦 Bill of Materials (BOM)")
if bom_utils_available:
    pdf_lib_functional = hasattr(bom_utils, 'FPDF') and getattr(bom_utils, 'FPDF') is not None
    try:
        bom_dataframe = bom_utils.compile_bom_data(skid_results, floor_results, wall_results, top_panel_results, overall_dims_for_display)
        if bom_dataframe is not None and not bom_dataframe.empty:
            st.dataframe(
                bom_dataframe, hide_index=True, use_container_width=True,
                column_config={ # Format numeric columns for display
                    "Item No.": st.column_config.NumberColumn(format="%d"),
                    "Qty": st.column_config.NumberColumn(format="%d"),
                    # Other columns are likely strings based on bom_utils logic
                }
            )
            if pdf_lib_functional:
                pdf_bytes = bom_utils.generate_bom_pdf_bytes(bom_dataframe)
                if pdf_bytes:
                    st.download_button(label="Download BOM (PDF)", data=pdf_bytes, file_name="crate_bom.pdf", mime="application/pdf")
                else: st.warning("Could not generate PDF data for download (check console logs for FPDF errors).")
            else: st.warning("FPDF2 library not available, PDF download disabled.")
        elif bom_dataframe is not None: st.info("No components found for Bill of Materials based on current inputs/calculations.")
        else: st.error("BOM data compilation failed (compile_bom_data returned None).")
    except Exception as e:
        log.error(f"Error during BOM processing or PDF generation in app.py: {e}", exc_info=True)
        st.error(f"An error occurred while preparing the BOM: {e}")
else:
    st.warning("BOM generation utilities not available (check bom_utils.py and fpdf2 installation).")

log.info("Streamlit app script execution finished.")