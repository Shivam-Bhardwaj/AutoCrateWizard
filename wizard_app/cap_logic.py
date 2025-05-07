# cap_logic.py
"""
Logic for calculating the crate's top cap assembly.

Determines dimensions, components, and layout of the cap based on
overall crate dimensions and construction constants.

The cap consists of a top panel (sheathing) and cleats (longitudinal and transverse)
mounted on top of this panel. Based on rules in 0251-70054.
"""

import logging
import math
from typing import Dict, List, Any, Tuple

# Configure logging
log = logging.getLogger(__name__)

# --- Constants ---
# Default actual dimensions based on 0251-70054, Sec 7.3 & Appendix D (e.g., 1x4)
DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS: float = 0.75  # Actual thickness for 1x lumber (height when laid flat)
DEFAULT_NOMINAL_CAP_CLEAT_WIDTH: float = 3.5    # Actual width for 1x4 lumber
FLOAT_TOLERANCE: float = 1e-6                   # Calculation tolerance

def _calculate_cleats_layout(
    dimension_for_spacing: float,           # Dimension across which cleats are spaced (e.g., crate_width)
    cleat_measure_for_spacing_calc: float,  # Cleat's dimension perpendicular to spacing direction (e.g., cleat_width)
    max_spacing_param: float,               # Max C-C spacing allowed
    cleat_length: float,                    # Length of the individual cleats (run along the other dimension)
    cleat_thickness: float                  # Thickness/height of the cleat lumber
) -> Dict[str, Any]:
    """
    Helper function to calculate number, spacing, and positions of cleats along one dimension.
    Uses logic similar to skid positioning: cleats centered within the dimension_for_spacing.
    First/last cleat centers are placed half their width in from the edges.
    """
    cleats_results = {
        "count": 0,
        "actual_spacing": 0.0,
        "positions": [], # Center positions relative to the center of dimension_for_spacing
        "cleat_length_each": cleat_length,
        "cleat_thickness_each": cleat_thickness, # Height when laid flat
        "cleat_width_each": cleat_measure_for_spacing_calc # Width across spacing direction
    }

    log.debug(f"Calculating cleat layout: Dim={dimension_for_spacing:.2f}, CleatW={cleat_measure_for_spacing_calc:.2f}, MaxSpace={max_spacing_param:.2f}")

    # --- Basic Validation ---
    if dimension_for_spacing < cleat_measure_for_spacing_calc - FLOAT_TOLERANCE:
        log.warning(f"Dimension {dimension_for_spacing:.2f} too small for cleat width {cleat_measure_for_spacing_calc:.2f}. Cannot place cleats.")
        return cleats_results # Count remains 0

    # --- Determine Cleat Count ---
    num_cleats = 0
    # Case 1: Only one cleat fits
    if dimension_for_spacing < (2 * cleat_measure_for_spacing_calc) - FLOAT_TOLERANCE:
         num_cleats = 1
         log.debug("Dimension allows for only one cleat.")
    # Case 2: Two or more cleats
    else:
        if max_spacing_param <= FLOAT_TOLERANCE:
             log.warning("Max cleat spacing is zero or negative. Defaulting to 2 edge cleats.")
             num_cleats = 2
        else:
            # Span between centerlines of the outermost cleats
            centerline_span = dimension_for_spacing - cleat_measure_for_spacing_calc
            if centerline_span < FLOAT_TOLERANCE: # Should not happen if dim >= 2*cleat_width, but safety check
                 log.warning(f"Centerline span ({centerline_span:.3f}) is near zero despite dim ({dimension_for_spacing:.2f}) >= 2*cleat_width ({cleat_measure_for_spacing_calc:.2f}). Placing 2 cleats.")
                 num_cleats = 2
            else:
                # Calculate theoretical count based on spacing
                # Number of spaces needed = ceil(centerline_span / max_spacing)
                num_spaces_needed = math.ceil(centerline_span / max_spacing_param)
                num_cleats_calculated = num_spaces_needed + 1
                num_cleats = max(2, num_cleats_calculated) # Always at least 2 if dim allows
                log.debug(f"Calculated centerline_span={centerline_span:.2f}, num_spaces={num_spaces_needed}, initial_count={num_cleats_calculated}")

    # --- Calculate Spacing and Positions ---
    actual_spacing = 0.0
    positions = []
    if num_cleats == 1:
        actual_spacing = 0.0
        positions = [0.0] # Centered
    elif num_cleats > 1:
        centerline_span_actual = dimension_for_spacing - cleat_measure_for_spacing_calc
        actual_spacing = centerline_span_actual / (num_cleats - 1)
        
        start_pos = -centerline_span_actual / 2.0
        positions = [round(start_pos + i * actual_spacing, 4) for i in range(num_cleats)]

    cleats_results["count"] = num_cleats
    cleats_results["actual_spacing"] = round(actual_spacing, 4) if num_cleats > 1 else 0.0
    cleats_results["positions"] = positions
    log.debug(f"Final Cleat Layout: Count={num_cleats}, Spacing={actual_spacing:.2f}, Positions={positions}")
    return cleats_results

def calculate_cap_layout(
    crate_overall_width: float,
    crate_overall_length: float,
    cap_panel_sheathing_thickness: float,
    cap_cleat_nominal_thickness: float = DEFAULT_NOMINAL_CAP_CLEAT_THICKNESS,
    cap_cleat_nominal_width: float = DEFAULT_NOMINAL_CAP_CLEAT_WIDTH,
    max_top_cleat_spacing: float = 24.0
) -> Dict[str, Any]:
    """
    Calculates the layout for the crate's top cap assembly.

    Args:
        crate_overall_width: Overall external width of the crate (dimension for longitudinal cleat spacing).
        crate_overall_length: Overall external length of the crate (dimension for transverse cleat spacing).
        cap_panel_sheathing_thickness: Thickness of the cap's top panel sheathing (e.g., 0.75").
        cap_cleat_nominal_thickness: Actual thickness of the cleat lumber (e.g., 0.75" for 1x). Height when laid flat.
        cap_cleat_nominal_width: Actual width of the cleat lumber (e.g., 3.5" for 1x4).
        max_top_cleat_spacing: Maximum allowed center-to-center spacing for top cleats.

    Returns:
        A dictionary containing the cap layout details.
    """
    result = {
        "status": "INIT", "message": "Cap calculation not started.",
        "cap_panel_width": 0.0, "cap_panel_length": 0.0, "cap_panel_thickness": 0.0,
        "longitudinal_cleats": {}, # Cleats running along crate_overall_length, spaced across width
        "transverse_cleats": {},   # Cleats running along crate_overall_width, spaced across length
        "max_allowed_cleat_spacing_used": max_top_cleat_spacing,
        "cap_cleat_spec": {"thickness": cap_cleat_nominal_thickness, "width": cap_cleat_nominal_width}
    }
    log.info(f"Starting cap layout: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, PanelT={cap_panel_sheathing_thickness:.2f}, CleatTxW={cap_cleat_nominal_thickness:.2f}x{cap_cleat_nominal_width:.2f}, MaxSpace={max_top_cleat_spacing:.2f}")

    # --- Input Validation ---
    if crate_overall_width <= FLOAT_TOLERANCE or crate_overall_length <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Crate width/length must be positive."
        log.error(result["message"]); return result
    if cap_panel_sheathing_thickness <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Panel thickness must be positive."
        log.error(result["message"]); return result
    if cap_cleat_nominal_thickness <= FLOAT_TOLERANCE or cap_cleat_nominal_width <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Cleat dimensions must be positive."
        log.error(result["message"]); return result
    # Check max spacing only if it would be needed
    is_spacing_needed = (crate_overall_width >= (2 * cap_cleat_nominal_width) - FLOAT_TOLERANCE or
                         crate_overall_length >= (2 * cap_cleat_nominal_width) - FLOAT_TOLERANCE)
    if max_top_cleat_spacing <= FLOAT_TOLERANCE and is_spacing_needed:
        result["status"] = "ERROR"; result["message"] = "Max top cleat spacing must be positive."
        log.error(result["message"]); return result

    result["cap_panel_width"] = round(crate_overall_width, 4)
    result["cap_panel_length"] = round(crate_overall_length, 4)
    result["cap_panel_thickness"] = round(cap_panel_sheathing_thickness, 4)

    # --- Longitudinal Cleats (run along L, spaced across W) ---
    # Cleat Width (cap_cleat_nominal_width) determines spacing across crate_overall_width.
    # Cleat Thickness (cap_cleat_nominal_thickness) is their height dimension.
    log.debug("Calculating longitudinal cleats...")
    longitudinal_cleats = _calculate_cleats_layout(
        dimension_for_spacing=crate_overall_width,
        cleat_measure_for_spacing_calc=cap_cleat_nominal_width,
        max_spacing_param=max_top_cleat_spacing,
        cleat_length=crate_overall_length,
        cleat_thickness=cap_cleat_nominal_thickness
    )
    result["longitudinal_cleats"] = longitudinal_cleats

    # --- Transverse Cleats (run along W, spaced across L) ---
    # Cleat Width (cap_cleat_nominal_width) determines spacing across crate_overall_length.
    log.debug("Calculating transverse cleats...")
    transverse_cleats = _calculate_cleats_layout(
        dimension_for_spacing=crate_overall_length,
        cleat_measure_for_spacing_calc=cap_cleat_nominal_width,
        max_spacing_param=max_top_cleat_spacing,
        cleat_length=crate_overall_width,
        cleat_thickness=cap_cleat_nominal_thickness
    )
    # Rule: Always have at least two transverse cleats (ends) if length allows
    if transverse_cleats["count"] < 2 and crate_overall_length >= (2 * cap_cleat_nominal_width) - FLOAT_TOLERANCE:
        log.warning(f"Transverse cleat count was {transverse_cleats['count']} for length {crate_overall_length:.2f}. Forcing minimum 2 for ends.")
        centerline_span_actual = crate_overall_length - cap_cleat_nominal_width
        start_pos = -centerline_span_actual / 2.0
        end_pos = centerline_span_actual / 2.0
        transverse_cleats["count"] = 2
        transverse_cleats["actual_spacing"] = centerline_span_actual # Spacing between the two
        transverse_cleats["positions"] = [round(start_pos, 4), round(end_pos, 4)]
        
    elif transverse_cleats["count"] < 2 and crate_overall_length >= cap_cleat_nominal_width - FLOAT_TOLERANCE :
        log.warning(f"Transverse cleat count was {transverse_cleats['count']} for length {crate_overall_length:.2f}. Forcing minimum 1 as length is small.")
        # If length only fits one, ensure count is 1
        if transverse_cleats["count"] == 0:
            transverse_cleats["count"] = 1
            transverse_cleats["actual_spacing"] = 0.0
            transverse_cleats["positions"] = [0.0] # Centered

    result["transverse_cleats"] = transverse_cleats

    # --- Final Status ---
    if longitudinal_cleats["count"] > 0 or transverse_cleats["count"] > 0:
        result["status"] = "OK"
        result["message"] = "Cap layout calculated successfully."
        if longitudinal_cleats["count"] == 0:
             result["message"] += " (Note: No longitudinal cleats placed due to small width)."
             result["status"] = "WARNING" # Make it a warning if only one direction has cleats
        if transverse_cleats["count"] == 0:
             result["message"] += " (Note: No transverse cleats placed due to small length)."
             result["status"] = "WARNING"

    else: # Neither direction got cleats
        result["status"] = "ERROR"
        result["message"] = "Failed to place any cap cleats (crate dimensions likely too small)."

    log.info(f"Cap Layout Calculation Complete. Final Status: {result['status']}")
    return result

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    test_cases = [
        {"name": "Standard Case", "width": 48, "length": 96, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Small Square Cap", "width": 20, "length": 20, "panel_thk": 0.5, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 12},
        {"name": "Narrow Cap", "width": 10, "length": 60, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Short Cap", "width": 60, "length": 10, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Single Cleat Width Cap", "width": 3.5, "length": 40, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Single Cleat Length Cap", "width": 40, "length": 3.5, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Too Small Cap", "width": 2, "length": 2, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 24},
        {"name": "Zero Max Spacing Error Case", "width": 48, "length": 96, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 0},
        {"name": "Wide spacing only fits 2", "width": 50, "length": 50, "panel_thk": 0.75, "cleat_thk": 0.75, "cleat_w": 3.5, "max_space": 60},

    ]
    import json
    for test in test_cases:
        print(f"\n--- Test: {test['name']} ---")
        cap_data = calculate_cap_layout(
            crate_overall_width=test["width"],
            crate_overall_length=test["length"],
            cap_panel_sheathing_thickness=test["panel_thk"],
            cap_cleat_nominal_thickness=test["cleat_thk"],
            cap_cleat_nominal_width=test["cleat_w"],
            max_top_cleat_spacing=test["max_space"]
        )
        print(json.dumps(cap_data, indent=2))