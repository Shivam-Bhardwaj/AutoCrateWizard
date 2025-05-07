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
# This MUST come after `import streamlit as st`
st.set_page_config(layout="wide", page_title="AutoCrate Wizard", page_icon="⚙️")

# --- Setup Logging ---
log = logging.getLogger(__package__ if __package__ else "wizard_app")
if not log.handlers:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log.info(f"Logger '{log.name}' configured.")


# --- Import Your Project Modules ---
try:
    from wizard_app import config
    from wizard_app import skid_logic
    from wizard_app import floorboard_logic
    from wizard_app import cap_logic
    from wizard_app import wall_logic
    from wizard_app import explanations
    from wizard_app import bom_utils # Import the new BOM utilities

    from wizard_app.ui_modules import sidebar
    from wizard_app.ui_modules import status
    from wizard_app.ui_modules import metrics
    from wizard_app.ui_modules import visualizations
    from wizard_app.ui_modules import details

    # Check availability (optional)
    floorboard_logic_available = hasattr(floorboard_logic, 'calculate_floorboard_layout')
    cap_logic_available = hasattr(cap_logic, 'calculate_cap_layout')
    wall_logic_available = hasattr(wall_logic, 'calculate_wall_panels')
    details_module_available = hasattr(details, 'display_details_tables')
    # Check if BOM utils imported successfully and have the necessary functions
    bom_utils_available = (
        'bom_utils' in sys.modules and
        hasattr(bom_utils, 'compile_bom_data') and
        hasattr(bom_utils, 'generate_bom_pdf_bytes')
    )
    # Also check if the PDF library itself is available within bom_utils
    if bom_utils_available and not hasattr(bom_utils, 'FPDF') or getattr(bom_utils, 'FPDF') is None:
         log.warning("bom_utils imported, but FPDF2 library seems unavailable within it.")
         # We can still proceed, but PDF generation will be disabled later
         pass # Allow app to run, PDF section will show warning

    log.info("Successfully imported all project modules.")

except ImportError as e:
    log.error(f"CRITICAL ERROR: Could not import one or more project modules: {e}", exc_info=True)
    # Try to show error in Streamlit UI if st is defined
    try:
        st.error(f"Application Initialization Error: Could not load critical components. Details: {e}")
        st.caption("Please check the application console logs. The application might be in an inconsistent state or an essential file might be missing/misplaced.")
    except NameError:
        # This happens if streamlit itself failed to import
        print(f"FATAL ERROR during import: {e}. Streamlit UI cannot be shown.")
    st.stop() # Halt further execution


# --- Main Application Title ---
st.title("⚙️ AutoCrate Wizard - Parametric Crate Layout System")
st.caption("Interactively calculates and visualizes industrial shipping crate layouts (Base, Floor, Walls, Top).")
st.divider()

# --- Caching Wrappers for Logic Functions ---
@st.cache_data
def cached_calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness):
    log.debug("CACHE MISS or RECALC: cached_calculate_skid_layout")
    return skid_logic.calculate_skid_layout(product_weight, product_width, clearance_side_product, panel_thickness, framing_cleat_thickness)

@st.cache_data
def cached_calculate_floorboard_layout(skid_results_tuple_or_dict, product_length, clearance_side_product, selected_nominal_sizes_tuple, allow_custom_narrow):
    skid_results_dict = dict(skid_results_tuple_or_dict) if isinstance(skid_results_tuple_or_dict, tuple) else skid_results_tuple_or_dict
    selected_nominal_sizes = list(selected_nominal_sizes_tuple)
    log.debug("CACHE MISS or RECALC: cached_calculate_floorboard_layout")
    if not floorboard_logic_available: return {"status": "NOT FOUND", "message": "floorboard_logic.py missing."}
    return floorboard_logic.calculate_floorboard_layout(skid_results_dict, product_length, clearance_side_product, selected_nominal_sizes, allow_custom_narrow)

@st.cache_data
def cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing):
    log.debug("CACHE MISS or RECALC: cached_calculate_cap_layout")
    if not cap_logic_available: return {"status": "NOT FOUND", "message": "cap_logic.py missing."}
    return cap_logic.calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_val, cap_cleat_thk, cap_cleat_w, max_spacing)

@st.cache_data
def cached_calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width):
    log.debug("CACHE MISS or RECALC: cached_calculate_wall_panels")
    if not wall_logic_available: return {"status": "NOT FOUND", "message": "wall_logic.py missing."}
    return wall_logic.calculate_wall_panels(crate_overall_width, crate_overall_length, panel_height, panel_thickness, wall_cleat_thickness, wall_cleat_width)


# --- Sidebar Inputs ---
ui_inputs = sidebar.display_sidebar()

# --- Core Logic Execution ---
# Unpack inputs from ui_inputs dictionary
product_weight = ui_inputs.get('product_weight')
product_width_input = ui_inputs.get('product_width')
product_length_input = ui_inputs.get('product_length')
product_actual_height = ui_inputs.get('product_height')
clearance_side_product = ui_inputs.get('clearance_side')
clearance_above_product_ui = ui_inputs.get('clearance_above')
panel_thickness_ui = ui_inputs.get('panel_thickness')
wall_cleat_thickness_ui = ui_inputs.get('wall_cleat_thickness')
wall_cleat_width_ui = ui_inputs.get('wall_cleat_width')
selected_nominal_sizes_tuple_for_cache = ui_inputs.get('selected_floor_nominals', tuple())
allow_custom_narrow = ui_inputs.get('allow_custom_narrow', False)
cap_cleat_actual_thk_ui = ui_inputs.get('cap_cleat_thickness')
cap_cleat_actual_width_ui = ui_inputs.get('cap_cleat_width')
max_top_cleat_spacing_ui = ui_inputs.get('max_top_cleat_spacing')

log.info(f"UI Inputs captured: {ui_inputs}")

# Initialize results dictionaries
skid_results = {"status": "NOT RUN", "message": "Skid calculation not initiated."}
floor_results = {"status": "NOT RUN", "message": "Floorboard calculation not initiated."}
wall_results = {"status": "NOT RUN", "message": "Wall panel calculation not initiated."}
top_panel_results = {"status": "NOT RUN", "message": "Top panel calculation not initiated."}
skid_status = "NOT RUN"

# Calculate Skid Layout
try:
    skid_results = cached_calculate_skid_layout(
        product_weight, product_width_input, clearance_side_product,
        panel_thickness_ui, wall_cleat_thickness_ui
    )
    skid_status = skid_results.get("status", "UNKNOWN")
    log.info(f"Skid calculation status: {skid_status} - Message: {skid_results.get('message', '')}")
except Exception as e:
    log.error(f"Skid calculation runtime error: {e}", exc_info=True)
    st.error(f"Skid calculation failed: {e}")
    skid_results = {"status": "CRITICAL ERROR", "message": f"Skid calculation failed due to runtime error: {e}"}
    skid_status = "CRITICAL ERROR"

skid_results_tuple_for_cache = tuple(sorted(skid_results.items())) if isinstance(skid_results, dict) else skid_results

# Calculate Derived Dimensions
crate_overall_width = skid_results.get('crate_width', 0.0)
crate_overall_length = product_length_input + 2 * (clearance_side_product + panel_thickness_ui + wall_cleat_thickness_ui)
skid_actual_height = skid_results.get('skid_height', 0.0)
crate_internal_clear_height = product_actual_height + clearance_above_product_ui
wall_panel_height_calc = crate_internal_clear_height
crate_overall_height_external = (
    skid_actual_height + panel_thickness_ui + wall_panel_height_calc +
    panel_thickness_ui + cap_cleat_actual_thk_ui
)
log.info(f"Calculated Overall Dimensions: Width={crate_overall_width:.2f}, Length={crate_overall_length:.2f}, Height={crate_overall_height_external:.2f}")
log.info(f"Calculated Wall Panel Clear Height for logic: {wall_panel_height_calc:.2f}")

# Calculate Floorboards
if floorboard_logic_available:
    if skid_status == "OK":
        if not selected_nominal_sizes_tuple_for_cache and not allow_custom_narrow: floor_results = {"status": "INPUT ERROR", "message": "No standard lumber selected AND custom narrow not allowed."}
        else:
            try: floor_results = cached_calculate_floorboard_layout(skid_results_tuple_for_cache, product_length_input, clearance_side_product, selected_nominal_sizes_tuple_for_cache, allow_custom_narrow); log.info(f"Floorboard status: {floor_results.get('status')} - Message: {floor_results.get('message', '')}")
            except Exception as e: log.error(f"Floorboard calc runtime error: {e}", exc_info=True); st.error(f"Floorboard calc error: {e}"); floor_results = {"status": "CRITICAL ERROR", "message": f"Floorboard calculation failed: {e}"}
    elif skid_status != "OK" : floor_results = {"status": "SKIPPED", "message": f"Skipped due to Skid status: {skid_status}."}
else: floor_results = {"status": "NOT FOUND", "message": "floorboard_logic.py missing or not available."}

# Calculate Top Panel
if cap_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE:
        try: top_panel_results = cached_calculate_cap_layout(crate_overall_width, crate_overall_length, panel_thickness_ui, cap_cleat_actual_thk_ui, cap_cleat_actual_width_ui, max_top_cleat_spacing_ui); log.info(f"Top Panel status: {top_panel_results.get('status')} - Message: {top_panel_results.get('message', '')}")
        except Exception as e: log.error(f"Top Panel calc runtime error: {e}", exc_info=True); st.error(f"Top Panel calc error: {e}"); top_panel_results = {"status": "CRITICAL ERROR", "message": f"Top Panel calculation failed: {e}"}
    elif skid_status != "OK": top_panel_results = {"status": "SKIPPED", "message": f"Skipped due to Skid status: {skid_status}."}
    else: top_panel_results = {"status": "SKIPPED", "message": "Skipped due to invalid crate dimensions for Top Panel."}
else: top_panel_results = {"status": "NOT FOUND", "message": "cap_logic.py missing or not available."}

# Calculate Wall Panels
if wall_logic_available:
    if skid_status == "OK" and crate_overall_width > config.FLOAT_TOLERANCE and crate_overall_length > config.FLOAT_TOLERANCE and wall_panel_height_calc > config.FLOAT_TOLERANCE:
        try: wall_results = cached_calculate_wall_panels(crate_overall_width, crate_overall_length, wall_panel_height_calc, panel_thickness_ui, wall_cleat_thickness_ui, wall_cleat_width_ui); log.info(f"Wall panel status: {wall_results.get('status')} - Message: {wall_results.get('message', '')}")
        except Exception as e: log.error(f"Wall panel calc runtime error: {e}", exc_info=True); st.error(f"Wall panel calc error: {e}"); wall_results = {"status": "CRITICAL ERROR", "message": f"Wall panel calculation failed: {e}"}
    elif skid_status != "OK": wall_results = {"status": "SKIPPED", "message": f"Skipped due to Skid status: {skid_status}."}
    else: wall_results = {"status": "SKIPPED", "message": "Skipped due to invalid crate dimensions for Wall Panels."}
else: wall_results = {"status": "NOT FOUND", "message": "wall_logic.py missing or not available."}


# --- Display Status ---
status.display_status(skid_results, floor_results, wall_results, top_panel_results)

# --- Prepare Overall Dimensions & Metrics for Display ---
overall_dims_for_display = {
    'width': crate_overall_width, 'length': crate_overall_length, 'height': crate_overall_height_external,
    'panel_thickness': panel_thickness_ui, 'product_height': product_actual_height,
    'clearance_top': clearance_above_product_ui, 'skid_height': skid_actual_height
}
overall_skid_span_metric = None
if skid_results.get("status") == "OK":
    # Use floorboard_logic helper if available, otherwise calculate manually
    if floorboard_logic_available and hasattr(floorboard_logic, 'calculate_overall_skid_span'):
        overall_skid_span_metric = floorboard_logic.calculate_overall_skid_span(skid_results)
    else: # Manual fallback
        skid_w_m, pos_m, skid_c_m = skid_results.get('skid_width'), skid_results.get('skid_positions', []), skid_results.get('skid_count')
        if skid_c_m == 1 and skid_w_m is not None: overall_skid_span_metric = skid_w_m
        elif skid_c_m is not None and skid_c_m > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_c_m: overall_skid_span_metric = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
overall_dims_for_display['overall_skid_span'] = overall_skid_span_metric

metrics.display_metrics(skid_results, floor_results, wall_results, top_panel_results, overall_dims_for_display)


# --- Main Area Display (Schematics) ---
st.divider(); st.header("📐 Layout Schematics")

# Display Skid Visualization (XZ View)
visualizations.display_skid_visualization(skid_results, overall_skid_span_metric, ui_inputs)

# Display Floorboard Visualization (XY View with context)
visualizations.display_floorboard_visualization(
    floor_results, skid_results, wall_results, overall_dims_for_display, ui_inputs
)

# Display Wall Panel Visualizations (Front XZ, Profile ZY)
st.divider(); st.subheader("Wall Panel Assembly Schematics")
if wall_logic_available and wall_results and wall_results.get("status") == "OK":
    side_panel_data = wall_results.get("side_panels", [{}])[0]
    back_panel_data = wall_results.get("back_panels", [{}])[0] # Use "back_panels" key
    visualizations.display_wall_assembly(side_panel_data, "Side Panel", ui_inputs, overall_dims_for_display)
    st.markdown("<br>", unsafe_allow_html=True)
    visualizations.display_wall_assembly(back_panel_data, "Back Panel", ui_inputs, overall_dims_for_display)
elif wall_results: st.info(f"Wall panel schematics cannot be displayed. Status: {wall_results.get('status', 'N/A')}, Message: {wall_results.get('message', 'No message')}")
else: st.info("Wall panel calculation pending or wall logic module not available.")

# Display Top Panel Visualizations (Front XY, Profile YZ)
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
    try:
        bom_dataframe = bom_utils.compile_bom_data(skid_results, floor_results, wall_results, top_panel_results, overall_dims_for_display)
        if bom_dataframe is not None and not bom_dataframe.empty:
            # Display DataFrame in Streamlit with specific column formatting
            st.dataframe(
                bom_dataframe, hide_index=True, use_container_width=True,
                column_config={ # Add formatting for columns that exist and are numeric
                    "Length (in)": st.column_config.NumberColumn(format="%.2f"),
                    "Width (in)": st.column_config.NumberColumn(format="%.2f"),
                    "Thickness (in)": st.column_config.NumberColumn(format="%.3f"),
                }
            )
            pdf_bytes = bom_utils.generate_bom_pdf_bytes(bom_dataframe)
            if pdf_bytes:
                st.download_button(label="Download BOM (PDF)", data=pdf_bytes, file_name="crate_bom.pdf", mime="application/pdf")
            else: st.warning("Could not generate PDF data for download (check console logs for FPDF errors).")
        elif bom_dataframe is not None: st.info("No components found for Bill of Materials based on current inputs/calculations.")
        else: st.error("BOM data compilation failed.")
    except Exception as e:
        log.error(f"Error during BOM processing or PDF generation in app.py: {e}", exc_info=True)
        st.error(f"An error occurred while preparing the BOM: {e}")
else:
    st.warning("BOM generation utilities not available (check bom_utils.py and fpdf2 installation).")


log.info("Streamlit app script execution finished.")