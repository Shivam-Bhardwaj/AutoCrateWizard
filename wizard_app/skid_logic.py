# wizard_app/skid_logic.py
"""
Core logic for calculating skid layout for industrial shipping crates
based on specified shipping standards. (Revised logic for positioning)
Imports constants from config.py
"""

import math
import logging
from typing import Dict, List, Union

# Import from config
from . import config

# Configure logging
log = logging.getLogger(__name__) # Use module-specific logger

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
    if product_weight < -config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product weight cannot be negative."
        log.error(result["message"]); return result
    if product_width <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product width must be positive."
        log.error(result["message"]); return result
    if clearance_side < -config.FLOAT_TOLERANCE or panel_thickness < -config.FLOAT_TOLERANCE or cleat_thickness < -config.FLOAT_TOLERANCE:
         result["status"] = "ERROR"; result["message"] = "Dimensions (clearance, panel, cleat) cannot be negative."
         log.error(result["message"]); return result

    log.info(f"Calculating skid layout for Weight={product_weight:.2f} lbs, Product Width={product_width:.2f}\"")

    # --- Handle Overweight Case ---
    if product_weight > config.WEIGHT_RULES[-1][0] + config.FLOAT_TOLERANCE: # Assumes WEIGHT_RULES is sorted by weight
        result["status"] = "OVER"
        result["message"] = f"Weight ({product_weight:.0f} lbs) exceeds {config.WEIGHT_RULES[-1][0]:.0f} lbs limit."
        log.warning(result["message"]); return result

    # --- Determine Skid Type, Width, Height, and Max Spacing ---
    skid_type_nominal = None
    max_spacing = None
    skid_width = 0.0
    skid_height = 0.0

    # Simplified rule selection - first rule that fits weight
    for max_w, type_nom, max_s in config.WEIGHT_RULES:
        if product_weight <= max_w + config.FLOAT_TOLERANCE:
            skid_type_nominal = type_nom
            max_spacing = max_s
            break

    if skid_type_nominal is None: # Should not happen if weight is within overall limits
         result["status"] = "ERROR"; result["message"] = f"Could not determine skid type for weight {product_weight:.0f} lbs."
         log.error(result["message"]); return result

    try:
        skid_width, skid_height = config.SKID_DIMENSIONS[skid_type_nominal]
    except KeyError:
        result["status"] = "ERROR"; result["message"] = f"Dimensions for skid type '{skid_type_nominal}' not found in config."
        log.error(result["message"]); return result

    result.update({"skid_type": skid_type_nominal, "skid_width": skid_width,
                   "skid_height": skid_height, "max_spacing": max_spacing})
    log.info(f"Selected Skid: {skid_type_nominal}, W={skid_width}\", H={skid_height}\", Max Spacing={max_spacing}\"")

    if skid_height < config.MIN_SKID_HEIGHT - config.FLOAT_TOLERANCE:
         result["status"] = "ERROR"; result["message"] = f"Skid height ({skid_height}\") < min required ({config.MIN_SKID_HEIGHT}\")."
         log.error(result["message"]); return result

    # --- Calculate Crate and Usable Width ---
    crate_width_calculated = product_width + 2 * (clearance_side + panel_thickness + cleat_thickness)
    usable_width_calculated = product_width + 2 * clearance_side # This is the space product sits in, skids are typically wider under this
    # Usable width for skid placement is typically the crate_width - 2*cleat_thickness (if skids are flush to inner panel)
    # However, the original logic based it on product_width + 2*clearance_side and then checked skids fit in that.
    # The problem states: "Usable width is the space between the innermost faces of the side wall cleats"
    # This would be: crate_width_calculated - 2 * (panel_thickness + cleat_thickness)
    # Let's stick to the description:
    usable_width_for_skids = crate_width_calculated - 2 * (panel_thickness + cleat_thickness)


    result.update({"crate_width": crate_width_calculated, "usable_width": usable_width_for_skids}) # Using usable_width_for_skids for skid placement
    log.info(f"Crate Width: {crate_width_calculated:.2f}\", Usable Width (between cleats for skids): {usable_width_for_skids:.2f}\"")

    # --- Determine Skid Count and Spacing ---
    if usable_width_for_skids < skid_width - config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"
        result["message"] = f"Usable width for skids ({usable_width_for_skids:.2f}\") is too narrow for skid width ({skid_width:.2f}\")."
        log.error(result["message"]); return result

    skid_count = 0
    spacing_actual = 0.0

    # Case 1: Only one skid fits or is needed due to narrow usable width
    if usable_width_for_skids < (skid_width * 2) - config.FLOAT_TOLERANCE:
        skid_count = 1
        spacing_actual = 0.0
        log.info("Usable width allows only one skid.")
    else:
        # Centerline span is the space between the centerlines of the two outermost skids.
        # Outermost skids are placed with their centers half their width from the edges of usable_width_for_skids
        centerline_span = usable_width_for_skids - skid_width
        log.debug(f"Centerline span available for skids: {centerline_span:.2f}\"")

        if centerline_span < config.FLOAT_TOLERANCE: # Effectively space for only two skids edge-to-edge if their centers are at ends of span
            skid_count = 2
            spacing_actual = centerline_span # which could be very small or zero if usable_width_for_skids == skid_width
            log.info(f"Centerline span ({centerline_span:.2f}) very small, placing 2 skids with spacing {spacing_actual:.2f}\"")
        else:
            # Calculate theoretical minimum number of skids
            # (N-1) * max_spacing >= centerline_span  => N-1 >= centerline_span / max_spacing
            # N >= (centerline_span / max_spacing) + 1
            num_skids_calculated = math.ceil( (centerline_span / max_spacing) + 1 )
            skid_count = max(2, int(num_skids_calculated))
            log.debug(f"Calculated initial skid count: {skid_count} (from theoretical min {num_skids_calculated})")

            if skid_count <=1 : # Should be caught by initial checks or logic above. Safety.
                result["status"] = "ERROR"; result["message"] = "Internal error: skid_count became <= 1 unexpectedly."
                log.error(result["message"]); return result

            spacing_actual = centerline_span / (skid_count - 1)

            # Iteratively add skids if calculated spacing is too large (this part is similar to original, ensures we meet max_spacing)
            # This refinement loop might be redundant if the direct ceil calculation is robust.
            # However, it was in the original logic, so let's keep a similar check.
            # The direct calculation *should* give the minimum number of skids such that spacing is <= max_spacing.
            # So, this loop *shouldn't* execute if max_spacing > 0.
            # If max_spacing is 0 or negative (validated earlier, but for safety), this loop would be infinite.
            # The initial calculation already finds the smallest number of skids to satisfy the spacing constraint.
            # The `while True` loop from original could be replaced by this direct calculation.

            if spacing_actual > max_spacing + config.FLOAT_TOLERANCE and max_spacing > config.FLOAT_TOLERANCE :
                 # This case suggests that even with the calculated minimum skids, the spacing is too large.
                 # This would only happen if centerline_span / (ceil((centerline_span / max_spacing) + 1) - 1) > max_spacing
                 # which implies an issue in reasoning or an edge case.
                 # Let's revert to the iterative method from the original if the direct calc needs more testing.
                 # For now, trust the direct calculation and log if this happens.
                 log.warning(f"Calculated spacing {spacing_actual:.2f} > max_spacing {max_spacing:.2f} with {skid_count} skids. Check logic if this occurs frequently.")
                 # To be safe, use the original iterative refinement if direct calc seems problematic:
                 # Start with 2 skids and increment.
                 skid_count = 2
                 while True:
                     if skid_count <= 1: # Should not happen
                         result["status"] = "ERROR"; result["message"] = "Internal error: skid_count became <= 1 in loop."; return result
                     current_spacing_needed = centerline_span / (skid_count - 1)
                     if current_spacing_needed <= max_spacing + config.FLOAT_TOLERANCE or skid_count > 100: # Safety break
                         spacing_actual = current_spacing_needed
                         break
                     skid_count +=1
                 if skid_count > 100:
                     result["status"] = "ERROR"; result["message"] = "Exceeded skid count limit (100)."; return result


    result.update({"skid_count": skid_count, "spacing_actual": spacing_actual if skid_count > 1 else 0.0})
    log.info(f"Final Skid Count: {skid_count}, Actual Spacing: {result['spacing_actual']:.2f}\"")

    # --- Calculate Skid Positions (relative to center of usable_width_for_skids) ---
    skid_positions = []
    if skid_count == 1:
        skid_positions = [0.0] # Centered in usable_width_for_skids
    elif skid_count > 1:
        # Total span covered by centerlines of skids is (skid_count - 1) * spacing_actual
        total_centerline_span_actual = spacing_actual * (skid_count - 1)
        # First skid is at -total_centerline_span_actual / 2
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