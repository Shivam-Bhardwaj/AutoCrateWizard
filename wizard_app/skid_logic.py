# skid_logic.py
"""
Core logic for calculating skid layout for industrial shipping crates
based on specified shipping standards. (Revised logic for positioning)

Version 0.1.0 - Initial implementation.
Version 0.2.0 - Added weight rules and skid types.
Version 0.3.0 - Revised skid count and spacing logic based on usable width.
Version 0.3.1 - Implemented revised skid positioning logic.
Version 0.3.2 - Added input validation checks.
Version 0.3.3 - Ensured skid_height check is against MIN_SKID_HEIGHT.
Version 0.3.4 - Added logging.
Version 0.3.5 - Refined error messages.
Version 0.3.6 - Added comments and clarity.
Version 0.3.7 - Ensured spacing_actual is 0 for skid_count = 1.
Version 0.3.8 - Added more test cases and verification checks.
Version 0.3.18 - Added FLOAT_TOLERANCE and used it in usable width vs skid width check and other comparisons.
Version 0.3.19 - No logic changes, version updated for consistency with app.py import fix. (No changes for v0.4.3)
"""

import math
import logging
from typing import Dict, List, Union, Tuple

# Configure logging
log = logging.getLogger(__name__) # Use module-specific logger

# Define nominal vs actual dimensions for clarity (based on standard lumber sizes)
SKID_DIMENSIONS = {
    "3x4": (2.5, 3.5), # Actual dimensions (Width, Height)
    "4x4": (3.5, 3.5),
    "4x6": (5.5, 3.5)  # Actual dimensions (placed flat - Width=5.5)
}

# Define skid parameters based on weight ranges
# Format: (max_weight, skid_type_nominal, max_spacing_center_to_center)
WEIGHT_RULES = [
    (500,   "3x4", 30.0),
    (4500,  "4x4", 30.0),
    (6000,  "4x6", 41.0),
    (12000, "4x6", 28.0),
    (20000, "4x6", 24.0),
]

# Minimum required skid height (based on standard lumber)
MIN_SKID_HEIGHT = 3.5

# Tolerance for floating-point comparisons
FLOAT_TOLERANCE: float = 1e-6

def calculate_skid_layout(
    product_weight: float,
    product_width: float,
    clearance_side: float,
    panel_thickness: float,
    cleat_thickness: float # This is the framing cleat thickness for side/end walls
) -> Dict[str, Union[str, float, int, List[float], None]]:
    """
    Calculates skid layout based on product weight and dimensions per shipping standards.

    Args:
        product_weight: Weight of the product in lbs. Must be non-negative.
        product_width: Width of the product in inches. Must be positive.
        clearance_side: Clearance space on each side of the product in inches. Must be non-negative.
        panel_thickness: Thickness of the crate side panels in inches. Must be non-negative.
        cleat_thickness: Thickness of the crate side/end wall framing cleats in inches. Must be non-negative.

    Returns:
        A dictionary containing skid layout parameters or an error status.
    """
    result = {
        "skid_type": None, "skid_width": None, "skid_height": None,
        "skid_count": 0, "spacing_actual": 0.0, "max_spacing": None,
        "crate_width": 0.0, "usable_width": 0.0, "skid_positions": [],
        "status": "INIT", "message": "Calculation not started."
    }

    # --- Input Validation ---
    if product_weight < -FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product weight cannot be negative."
        log.error(result["message"]); return result
    if product_width <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product width must be positive."
        log.error(result["message"]); return result
    if clearance_side < -FLOAT_TOLERANCE or panel_thickness < -FLOAT_TOLERANCE or cleat_thickness < -FLOAT_TOLERANCE:
         result["status"] = "ERROR"; result["message"] = "Dimensions (clearance, panel, cleat) cannot be negative."
         log.error(result["message"]); return result

    log.info(f"Calculating skid layout for Weight={product_weight:.2f} lbs, Product Width={product_width:.2f}\"")

    # --- Handle Overweight Case ---
    if product_weight > 20000 + FLOAT_TOLERANCE:
        result["status"] = "OVER"
        result["message"] = f"Weight ({product_weight:.0f} lbs) exceeds 20,000 lbs limit."
        log.warning(result["message"]); return result

    # --- Determine Skid Type, Width, Height, and Max Spacing ---
    skid_type_nominal = None
    max_spacing = None
    skid_width = 0.0
    skid_height = 0.0

    if 0.0 <= product_weight <= 500.0 + FLOAT_TOLERANCE:
         skid_type_nominal = "3x4"; max_spacing = 30.0
    else:
        for max_w, type_nom, max_s in WEIGHT_RULES:
            if product_weight <= max_w + FLOAT_TOLERANCE:
                if skid_type_nominal is None:
                    skid_type_nominal = type_nom
                    max_spacing = max_s
                    break
    if skid_type_nominal is None: # Should not happen if weight <= 20000
         result["status"] = "ERROR"; result["message"] = f"Could not determine skid type for weight {product_weight:.0f} lbs."
         log.error(result["message"]); return result

    try:
        skid_width, skid_height = SKID_DIMENSIONS[skid_type_nominal]
    except KeyError:
        result["status"] = "ERROR"; result["message"] = f"Dimensions for skid type '{skid_type_nominal}' not found."
        log.error(result["message"]); return result

    result.update({"skid_type": skid_type_nominal, "skid_width": skid_width,
                   "skid_height": skid_height, "max_spacing": max_spacing})
    log.info(f"Selected Skid: {skid_type_nominal}, W={skid_width}\", H={skid_height}\", Max Spacing={max_spacing}\"")

    if skid_height < MIN_SKID_HEIGHT - FLOAT_TOLERANCE:
         result["status"] = "ERROR"; result["message"] = f"Skid height ({skid_height}\") < min required ({MIN_SKID_HEIGHT}\")."
         log.error(result["message"]); return result

    # --- Calculate Crate and Usable Width ---
    # Crate width is product + clearances + panels + cleats on BOTH sides
    crate_width_calculated = product_width + 2 * (clearance_side + panel_thickness + cleat_thickness)
    # Usable width is the space between the innermost faces of the side wall cleats
    usable_width_calculated = crate_width_calculated - 2 * (panel_thickness + cleat_thickness)
    result.update({"crate_width": crate_width_calculated, "usable_width": usable_width_calculated})
    log.info(f"Crate Width: {crate_width_calculated:.2f}\", Usable Width (between cleats): {usable_width_calculated:.2f}\"")

    # --- Determine Skid Count and Spacing ---
    if usable_width_calculated < skid_width - FLOAT_TOLERANCE:
        result["status"] = "ERROR"
        result["message"] = f"Usable width ({usable_width_calculated:.2f}\") is too narrow for skid width ({skid_width:.2f}\")."
        log.error(result["message"]); return result

    skid_count = 0
    spacing_actual = 0.0

    if usable_width_calculated < (skid_width * 2) - FLOAT_TOLERANCE: # Not enough for two skids edge to edge
        skid_count = 1
        spacing_actual = 0.0
        log.info("Usable width allows only one skid.")
    else:
        # Centerline span is the space between the centerlines of the two outermost skids.
        centerline_span = usable_width_calculated - skid_width # Space available for distributing centers
        log.debug(f"Centerline span available for skids: {centerline_span:.2f}\"")

        skid_count = 2 # Start with minimum of 2 skids
        while True:
            if skid_count <= 1: # Should not happen if logic above is correct
                 result["status"] = "ERROR"; result["message"] = "Internal error: skid_count became <= 1."
                 log.error(result["message"]); return result
            current_spacing_needed = centerline_span / (skid_count - 1)
            log.debug(f"Trying {skid_count} skids: Spacing needed = {current_spacing_needed:.2f}\"")

            if current_spacing_needed <= max_spacing + FLOAT_TOLERANCE:
                spacing_actual = current_spacing_needed
                log.info(f"Spacing {spacing_actual:.2f}\" <= Max {max_spacing:.2f}\". Using {skid_count} skids.")
                break
            else:
                skid_count += 1
                if skid_count > 100: # Safety break
                    result["status"] = "ERROR"; result["message"] = "Exceeded skid count limit (100)."
                    log.error(result["message"]); return result

    result.update({"skid_count": skid_count, "spacing_actual": spacing_actual})
    log.info(f"Final Skid Count: {skid_count}, Actual Spacing: {spacing_actual:.2f}\"")

    # --- Calculate Skid Positions (relative to center of usable_width_calculated) ---
    skid_positions = []
    if skid_count == 1:
        skid_positions = [0.0] # Centered
    elif skid_count > 1:
        total_centerline_span_actual = spacing_actual * (skid_count - 1)
        start_x = -total_centerline_span_actual / 2.0
        log.debug(f"Calculated actual centerline span for positions: {total_centerline_span_actual:.4f}\"")
        log.debug(f"First skid center (start_x): {start_x:.4f}\"")
        for i in range(skid_count):
            position = start_x + i * spacing_actual
            skid_positions.append(round(position, 4))

    result["skid_positions"] = skid_positions
    log.info(f"Skid Positions (Centerlines relative to usable width center): {['%.2f' % p for p in skid_positions]}")

    if skid_count > 0 and result["status"] not in ["ERROR", "OVER"]:
        result["status"] = "OK"; result["message"] = "Skid layout calculated successfully."
        log.info(result["message"])
    elif result["status"] == "INIT": # Should be overwritten
        result["status"] = "ERROR"; result["message"] = "Calculation finished without a final status."
        log.error(result["message"])
    return result

