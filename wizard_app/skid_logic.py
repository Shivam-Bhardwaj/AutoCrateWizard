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
Version 0.3.19 - No logic changes, version updated for consistency with app.py import fix.
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
    cleat_thickness: float
) -> Dict[str, Union[str, float, int, List[float], None]]:
    """
    Calculates skid layout based on product weight and dimensions per shipping standards.
    Uses revised logic to ensure skids fit within usable width edge-to-edge.

    Args:
        product_weight: Weight of the product in lbs. Must be non-negative.
        product_width: Width of the product in inches. Must be positive.
        clearance_side: Clearance space on each side of the product in inches. Must be non-negative.
        panel_thickness: Thickness of the crate side panels in inches. Must be non-negative.
        cleat_thickness: Thickness of the crate cleats in inches. Must be non-negative.

    Returns:
        A dictionary containing skid layout parameters or an error status.
        Keys: "skid_type", "skid_width", "skid_height", "skid_count",
              "spacing_actual", "max_spacing", "crate_width", "usable_width",
              "skid_positions", "status", "message"
    """
    result = {
        "skid_type": None, "skid_width": None, "skid_height": None,
        "skid_count": 0, "spacing_actual": 0.0, "max_spacing": None,
        "crate_width": 0.0, "usable_width": 0.0, "skid_positions": [],
        "status": "INIT", "message": "Calculation not started."
    }

    # --- Input Validation ---
    if product_weight < -FLOAT_TOLERANCE: # Use tolerance
        result["status"] = "ERROR"; result["message"] = "Product weight cannot be negative."
        log.error(result["message"]); return result
    if product_width <= FLOAT_TOLERANCE: # Use tolerance
        result["status"] = "ERROR"; result["message"] = "Product width must be positive."
        log.error(result["message"]); return result
    if clearance_side < -FLOAT_TOLERANCE or panel_thickness < -FLOAT_TOLERANCE or cleat_thickness < -FLOAT_TOLERANCE: # Use tolerance
         result["status"] = "ERROR"; result["message"] = "Dimensions (clearance, panel, cleat) cannot be negative."
         log.error(result["message"]); return result

    log.info(f"Calculating layout for Weight={product_weight:.2f} lbs, Product Width={product_width:.2f}\"")

    # --- Handle Overweight Case ---
    if product_weight > 20000 + FLOAT_TOLERANCE: # Use tolerance
        result["status"] = "OVER"
        result["message"] = f"Weight ({product_weight:.0f} lbs) exceeds 20,000 lbs limit."
        log.warning(result["message"]); return result

    # --- Determine Skid Type, Width, Height, and Max Spacing ---
    skid_type_nominal = None
    max_spacing = None
    skid_width = 0.0
    skid_height = 0.0

    # Determine skid type based on weight
    if 0.0 <= product_weight <= 500.0 + FLOAT_TOLERANCE: # Use tolerance
         skid_type_nominal = "3x4"; max_spacing = 30.0
    else: # Weight > 500 and <= 20000
        for max_w, type_nom, max_s in WEIGHT_RULES:
            if product_weight <= max_w + FLOAT_TOLERANCE: # Use tolerance
                if skid_type_nominal is None: # Assign if it's the first match > 500 lbs
                    skid_type_nominal = type_nom
                    max_spacing = max_s
                    break # Found the correct bracket

    if skid_type_nominal is None:
         result["status"] = "ERROR"; result["message"] = f"Could not determine skid type for weight {product_weight:.0f} lbs."
         log.error(result["message"]); return result

    # Get actual dimensions
    try:
        skid_width, skid_height = SKID_DIMENSIONS[skid_type_nominal]
    except KeyError:
        result["status"] = "ERROR"; result["message"] = f"Dimensions for skid type '{skid_type_nominal}' not found."
        log.error(result["message"]); return result

    result.update({"skid_type": skid_type_nominal, "skid_width": skid_width,
                   "skid_height": skid_height, "max_spacing": max_spacing})
    log.info(f"Selected Skid: {skid_type_nominal}, W={skid_width}\", H={skid_height}\", Max Spacing={max_spacing}\"")

    # --- Validate Skid Height Requirement ---
    if skid_height < MIN_SKID_HEIGHT - FLOAT_TOLERANCE: # Use tolerance
         result["status"] = "ERROR"; result["message"] = f"Skid height ({skid_height}\") < min required ({MIN_SKID_HEIGHT}\")."
         log.error(result["message"]); return result

    # --- Calculate Crate and Usable Width ---
    crate_width = product_width + 2 * (clearance_side + panel_thickness + cleat_thickness)
    usable_width = crate_width - 2 * (panel_thickness + cleat_thickness) # Space between inner faces of cleats
    result.update({"crate_width": crate_width, "usable_width": usable_width})
    log.info(f"Crate Width: {crate_width:.2f}\", Usable Width (between cleats): {usable_width:.2f}\"")

    # --- Determine Skid Count and Spacing (REVISED LOGIC) ---
    # Use tolerance when comparing usable_width and skid_width
    if usable_width < skid_width - FLOAT_TOLERANCE:
        result["status"] = "ERROR"
        result["message"] = f"Usable width ({usable_width:.2f}\") is too narrow for skid width ({skid_width:.2f}\")."
        log.error(result["message"]); return result

    skid_count = 0
    spacing_actual = 0.0

    # Case 1: Only one skid fits or is needed. Usable width is less than the space needed for two skids (SkidW + spacing + SkidW = 2*SkidW theoretically, but here simplified to < 2*SkidW).
    # More accurately, if usable_width is less than the *minimum* space needed for two skids edge-to-edge. The minimum space for two skids is SkidW + SkidW = 2*SkidW (touching).
    # The current logic `usable_width < (skid_width * 2)` implicitly assumes minimum space for 2 skids is just shy of 2*SkidW before spacing is considered. Let's refine this check slightly with tolerance.
    if usable_width < (skid_width * 2) - FLOAT_TOLERANCE:
        skid_count = 1
        spacing_actual = 0.0
        log.info("Usable width allows only one skid.")
    # Case 2: Two or more skids might fit. Determine count by spacing.
    else:
        # Centerline span is the space between the centerlines of the two outermost skids.
        # The space from the edge of the usable width to the centerline of the outermost skid is SkidW / 2.
        # So, centerline_span = UsableWidth - 2 * (SkidW / 2) = UsableWidth - SkidW
        centerline_span = usable_width - skid_width
        log.debug(f"Centerline span available: {centerline_span:.2f}\" (UsableW - SkidW)")

        # Start with 2 skids and check spacing
        skid_count = 2
        while True:
            # Ensure division by zero doesn't occur if skid_count somehow becomes 1 here
            if skid_count <= 1:
                 result["status"] = "ERROR"; result["message"] = "Internal error during skid count calculation (division by zero risk)."
                 log.error(result["message"]); return result
            current_spacing_needed = centerline_span / (skid_count - 1)
            log.debug(f"Trying {skid_count} skids: Spacing needed = {centerline_span:.2f} / {skid_count - 1} = {current_spacing_needed:.2f}\"")

            # Use tolerance for spacing comparison
            if current_spacing_needed <= max_spacing + FLOAT_TOLERANCE:
                spacing_actual = current_spacing_needed
                log.info(f"Spacing {spacing_actual:.2f}\" <= Max {max_spacing:.2f}\". Using {skid_count} skids.")
                break
            else:
                log.debug(f"Spacing {current_spacing_needed:.2f}\" > Max {max_spacing:.2f}\". Trying {skid_count + 1} skids.")
                skid_count += 1
                if skid_count > 100: # Safety break
                    result["status"] = "ERROR"; result["message"] = "Exceeded skid count limit (100)."
                    log.error(result["message"]); return result

    result.update({"skid_count": skid_count, "spacing_actual": spacing_actual})
    log.info(f"Final Skid Count: {skid_count}, Actual Spacing: {spacing_actual:.2f}\"")

    # --- Calculate Skid Positions (REVISED LOGIC) ---
    skid_positions = []
    if skid_count == 1:
        # Center the single skid within the usable width
        # Position is relative to the center of the usable width (which is 0)
        skid_positions = [0.0]
    elif skid_count > 1:
        # The total span covered by the centerlines is (skid_count - 1) * spacing_actual.
        # To center this span within the usable width (which is centered around 0),
        # the first centerline position is - (total span) / 2.
        centerline_span_actual = spacing_actual * (skid_count - 1)
        start_x = - centerline_span_actual / 2.0
        log.debug(f"Calculated actual centerline span: {centerline_span_actual:.4f}\"")
        log.debug(f"First skid center (start_x): {start_x:.4f}\"")
        for i in range(skid_count):
            position = start_x + i * spacing_actual
            skid_positions.append(round(position, 4)) # Rounding for cleaner output

    result["skid_positions"] = skid_positions
    log.info(f"Skid Positions (Centerlines): {['%.2f' % p for p in skid_positions]}")

    # --- Final Status Check & Return ---
    if skid_count > 0 and result["status"] not in ["ERROR", "OVER"]:
        result["status"] = "OK"; result["message"] = "Skid layout calculated successfully."
        log.info(result["message"])
    elif result["status"] == "INIT":
        result["status"] = "ERROR"; result["message"] = "Calculation finished without a final status."
        log.error(result["message"])

    # Add crate_length to results dictionary for floorboard logic if needed later
    # Calculate OUT_Crate_Length based on NX expression logic if consistent
    # OUT_Crate_Length = product_length + 2 * clearance_side + 2 * (panel_thickness + cleat_thickness)
    # result['crate_length'] = OUT_Crate_Length # Uncomment if floorboard logic needs this

    return result

# --- Example Usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    test_cases = [
        {"label": "Case 1: Mid-range (4600 lbs, 90\")", "params": (4600, 90, 2.0, 0.25, 0.75)},
        {"label": "Case 12: High Weight, Narrow Spacing (18000 lbs, 90\")", "params": (18000, 90, 2.0, 0.25, 0.75)},
        {"label": "Case 4: Narrow (5000 lbs, 40\")", "params": (5000, 40, 1.0, 0.25, 0.75)},
        {"label": "Case 8a: Just enough usable for 2 skids (1000 lbs, 7.0\")", "params": (1000, 7.0, 1.0, 0.25, 0.75)}, # Usable=7+3-2=8, SkidW=3.5 -> Cspan=4.5 -> 2 skids, space=4.5
        {"label": "Case 8b: Single skid case (1000 lbs, 6.0\")", "params": (1000, 6.0, 1.0, 0.25, 0.75)}, # Usable=6+3-2=7, SkidW=3.5 -> Usable=7, 2*SkidW=7 -> Usable < 2*SkidW - tol -> 1 skid (Corrected check)
        {"label": "Case 6: Width too small for skid (1000 lbs, 2\")", "params": (1000, 2, 0.5, 0.25, 0.75)}, # Usable = 2 + 2*(0.5+0.25+0.75) - 2*(0.25+0.75) = 2 + 3 - 2 = 3. SkidW=3.5 -> Error. Correct.
        {"label": "Case 5: Over Limit (21000 lbs)", "params": (21000, 90, 2.0, 0.25, 0.75)},
        {"label": "Case 9: Negative Weight", "params": (-100, 50, 1.0, 0.25, 0.75)},
        {"label": "Case 10: Zero Product Width", "params": (1000, 0, 1.0, 0.25, 0.75)},
        {"label": "Case 11: Min product width allowing one skid (1000 lbs, 3.5\")", "params": (1000, 3.5, 0.0, 0.0, 0.0)}, # Usable = 3.5, SkidW=3.5 -> Usable < 2*SkidW - tol -> 1 skid
    ]
    import json
    for test in test_cases:
        print(f"\n--- {test['label']} ---")
        layout = calculate_skid_layout(*test['params'])
        print(json.dumps(layout, indent=2))
        # Verification check for multi-skid cases
        if layout.get("status") == "OK" and layout.get("skid_count", 0) > 1:
            positions = layout["skid_positions"]; skid_w = layout["skid_width"]; usable_w = layout["usable_width"]
            first_outer = positions[0] - skid_w / 2; last_outer = positions[-1] + skid_w / 2
            calc_span = last_outer - first_outer
            # Use a tolerance for floating point comparison
            if not math.isclose(calc_span, usable_w, abs_tol=FLOAT_TOLERANCE * 10): print(f"  [VERIFICATION FAILED] Overall Span ({calc_span:.3f}\") != Usable Width ({usable_w:.3f}\")")
            else: print(f"  [VERIFICATION PASSED] Overall Span ({calc_span:.3f}\") == Usable Width ({usable_w:.3f}\")")
        # Verification check for single-skid cases
        elif layout.get("status") == "OK" and layout.get("skid_count", 0) == 1:
             skid_w = layout["skid_width"]; usable_w = layout["usable_width"]
             positions = layout.get("skid_positions", [])
             pos_ok = False
             if len(positions) == 1 and abs(positions[0] - 0.0) < FLOAT_TOLERANCE: pos_ok = True # Check position is close to 0
             if skid_w > usable_w + FLOAT_TOLERANCE: print(f"  [VERIFICATION FAILED] Single Skid Width ({skid_w:.3f}\") > Usable Width ({usable_w:.3f}\")")
             elif not pos_ok: print(f"  [VERIFICATION FAILED] Single Skid Position ({positions[0] if positions else 'N/A':.3f}\") != 0.0")
             else: print(f"  [VERIFICATION PASSED] Single Skid Width ({skid_w:.3f}\") <= Usable Width ({usable_w:.3f}\"), Position=0.0")

