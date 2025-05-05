# skid_logic.py
"""
Core logic for calculating skid layout for industrial shipping crates
based on specified shipping standards. (Revised logic for positioning)
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
    if product_weight < 0:
        result["status"] = "ERROR"; result["message"] = "Product weight cannot be negative."
        log.error(result["message"]); return result
    if product_width <= 0:
        result["status"] = "ERROR"; result["message"] = "Product width must be positive."
        log.error(result["message"]); return result
    if clearance_side < 0 or panel_thickness < 0 or cleat_thickness < 0:
         result["status"] = "ERROR"; result["message"] = "Dimensions (clearance, panel, cleat) cannot be negative."
         log.error(result["message"]); return result

    log.info(f"Calculating layout for Weight={product_weight:.2f} lbs, Product Width={product_width:.2f}\"")

    # --- Handle Overweight Case ---
    if product_weight > 20000:
        result["status"] = "OVER"
        result["message"] = f"Weight ({product_weight:.0f} lbs) exceeds 20,000 lbs limit."
        log.warning(result["message"]); return result

    # --- Determine Skid Type, Width, Height, and Max Spacing ---
    skid_type_nominal = None
    max_spacing = None
    skid_width = 0.0
    skid_height = 0.0

    # Determine skid type based on weight
    if 0 <= product_weight <= 500:
         skid_type_nominal = "3x4"; max_spacing = 30.0
    else: # Weight > 500 and <= 20000
        for max_w, type_nom, max_s in WEIGHT_RULES:
            if product_weight <= max_w:
                # Find the first bracket the weight falls into
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
    if skid_height < MIN_SKID_HEIGHT:
         result["status"] = "ERROR"; result["message"] = f"Skid height ({skid_height}\") < min required ({MIN_SKID_HEIGHT}\")."
         log.error(result["message"]); return result

    # --- Calculate Crate and Usable Width ---
    crate_width = product_width + 2 * (clearance_side + panel_thickness + cleat_thickness)
    usable_width = crate_width - 2 * (panel_thickness + cleat_thickness) # Space between inner faces of cleats
    result.update({"crate_width": crate_width, "usable_width": usable_width})
    log.info(f"Crate Width: {crate_width:.2f}\", Usable Width (between cleats): {usable_width:.2f}\"")

    # --- Determine Skid Count and Spacing (REVISED LOGIC) ---
    # Check if usable width is sufficient for even one skid
    if usable_width < skid_width:
        result["status"] = "ERROR"
        result["message"] = f"Usable width ({usable_width:.2f}\") is too narrow for skid width ({skid_width:.2f}\")."
        log.error(result["message"]); return result

    skid_count = 0
    spacing_actual = 0.0

    # Case 1: Only one skid fits or is needed.
    # If usable_width is less than the width of two skids, only one can be placed.
    if usable_width < (skid_width * 2):
        skid_count = 1
        spacing_actual = 0.0 # No spacing for a single skid
        log.info("Usable width allows only one skid.")
    # Case 2: Two or more skids might fit. Determine count by spacing.
    else:
        # **REVISED:** Calculate the span available for the centerlines.
        # This is the usable width minus the space taken by half a skid width at each end.
        centerline_span = usable_width - skid_width
        log.debug(f"Centerline span available: {centerline_span:.2f}\" (UsableW - SkidW)")

        # Start with minimum possible (2 skids) and check spacing against the centerline_span
        skid_count = 2
        while True:
            # Calculate the center-to-center spacing required for the current skid_count
            # across the available centerline_span.
            # Need (skid_count - 1) gaps.
            current_spacing_needed = centerline_span / (skid_count - 1)
            log.debug(f"Trying {skid_count} skids: Spacing needed = {centerline_span:.2f} / {skid_count - 1} = {current_spacing_needed:.2f}\"")


            if current_spacing_needed <= max_spacing:
                # This skid count works, the required spacing is within the limit.
                spacing_actual = current_spacing_needed
                log.info(f"Spacing {spacing_actual:.2f}\" <= Max {max_spacing:.2f}\". Using {skid_count} skids.")
                break # Found the minimum count that satisfies spacing
            else:
                # Required spacing is too large, need more skids to reduce spacing.
                log.debug(f"Spacing {current_spacing_needed:.2f}\" > Max {max_spacing:.2f}\". Trying {skid_count + 1} skids.")
                skid_count += 1
                # Safety break
                if skid_count > 100:
                    result["status"] = "ERROR"; result["message"] = "Exceeded skid count limit (100)."
                    log.error(result["message"]); return result

    result.update({"skid_count": skid_count, "spacing_actual": spacing_actual})
    log.info(f"Final Skid Count: {skid_count}, Actual Spacing: {spacing_actual:.2f}\"")


    # --- Calculate Skid Positions (REVISED LOGIC) ---
    # Positions are relative to the center of the usable_width (0).
    skid_positions = []
    if skid_count == 1:
        # Single skid is centered at 0
        skid_positions = [0.0]
    elif skid_count > 1:
        # **REVISED:** Calculate the starting position (center of the first skid).
        # The total span covered by centerlines is (skid_count - 1) * spacing_actual.
        # This span should be centered around 0.
        # The first skid's center is half the total centerline span to the left of center.
        centerline_span_actual = spacing_actual * (skid_count - 1)
        start_x = - centerline_span_actual / 2.0

        log.debug(f"Calculated actual centerline span: {centerline_span_actual:.4f}\"")
        log.debug(f"First skid center (start_x): {start_x:.4f}\"")

        for i in range(skid_count):
            position = start_x + i * spacing_actual
            skid_positions.append(round(position, 4)) # Round for cleaner output

    result["skid_positions"] = skid_positions
    log.info(f"Skid Positions (Centerlines): {['%.2f' % p for p in skid_positions]}")

    # --- Final Status Check & Return ---
    if skid_count > 0 and result["status"] not in ["ERROR", "OVER"]:
        result["status"] = "OK"; result["message"] = "Skid layout calculated successfully."
        log.info(result["message"])
    elif result["status"] == "INIT": # Fallback if status wasn't updated
        result["status"] = "ERROR"; result["message"] = "Calculation finished without a final status."
        log.error(result["message"])

    return result

# Example usage for standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    test_cases = [
        {"label": "Case 1: Mid-range (4600 lbs, 90\")", "params": (4600, 90, 2.0, 0.25, 0.75)}, # 4x6, W=5.5, MaxS=41. Usable=94. CenterSpan=88.5. Cnt=3, Sp=44.25>41. Cnt=4, Sp=29.5<=41. Count=4. Pos=[-44.25, -14.75, 14.75, 44.25]
        {"label": "Case 2: Light (400 lbs, 30\")", "params": (400, 30, 1.0, 0.25, 0.75)}, # 3x4, W=2.5, MaxS=30. Usable=32. CenterSpan=29.5. Cnt=2, Sp=29.5<=30. Count=2. Pos=[-14.75, 14.75]
        {"label": "Case 3: Heavy (15000 lbs, 110\")", "params": (15000, 110, 2.0, 0.5, 1.0)}, # 4x6, W=5.5, MaxS=24. Usable=114. CenterSpan=108.5. Cnt=5, Sp=27.1>24. Cnt=6, Sp=21.7<=24. Count=6. Pos=[-54.25, -32.55, -10.85, 10.85, 32.55, 54.25]
        {"label": "Case 4: Narrow (5000 lbs, 40\")", "params": (5000, 40, 1.0, 0.25, 0.75)}, # 4x6, W=5.5, MaxS=41. Usable=42. CenterSpan=36.5. Cnt=2, Sp=36.5<=41. Count=2. Pos=[-18.25, 18.25]
        {"label": "Case 5: Over Limit (21000 lbs)", "params": (21000, 90, 2.0, 0.25, 0.75)}, # OVER
        {"label": "Case 6: Width too small for skid (1000 lbs, 2\")", "params": (1000, 2, 0.5, 0.25, 0.75)}, # 4x4, W=3.5. Usable=3. Usable < SkidW. ERROR.
        {"label": "Case 7: Zero Weight (50\")", "params": (0, 50, 1.0, 0.25, 0.75)}, # 3x4, W=2.5, MaxS=30. Usable=52. CenterSpan=49.5. Cnt=2, Sp=49.5>30. Cnt=3, Sp=24.75<=30. Count=3. Pos=[-24.75, 0.0, 24.75]
        {"label": "Case 8a: Just enough usable for 2 skids (1000 lbs, 5.0\")", "params": (1000, 5.0, 1.0, 0.25, 0.75)}, # 4x4, W=3.5, MaxS=30. Usable=7.0. Usable >= 2*W. CenterSpan=3.5. Cnt=2, Sp=3.5<=30. Count=2. Pos=[-1.75, 1.75]
        {"label": "Case 8b: Slightly more than 8a (1000 lbs, 5.1\")", "params": (1000, 5.1, 1.0, 0.25, 0.75)}, # 4x4, W=3.5, MaxS=30. Usable=7.1. CenterSpan=3.6. Cnt=2, Sp=3.6<=30. Count=2. Pos=[-1.8, 1.8]
        {"label": "Case 9: Negative Weight", "params": (-100, 50, 1.0, 0.25, 0.75)}, # ERROR
        {"label": "Case 10: Zero Width", "params": (1000, 0, 1.0, 0.25, 0.75)}, # ERROR
        {"label": "Case 11: Negative Clearance", "params": (1000, 50, -1.0, 0.25, 0.75)}, # ERROR
        {"label": "Case 12: High Weight, Narrow Spacing (18000 lbs, 90\")", "params": (18000, 90, 2.0, 0.25, 0.75)}, # 4x6, W=5.5, MaxS=24. Usable=94. CenterSpan=88.5. Cnt=4, Sp=29.5>24. Cnt=5, Sp=22.125<=24. Count=5. Pos=[-44.25, -22.125, 0.0, 22.125, 44.25]
        {"label": "Case 13: Just wide enough for 1 skid (1000 lbs, 3.5\")", "params": (1000, 3.5, 0.0, 0.0, 0.0)}, # 4x4, W=3.5. Usable=3.5. Usable < 2*W. Count=1. Pos=[0.0]
    ]

    import json
    for test in test_cases:
        print(f"\n--- {test['label']} ---")
        layout = calculate_skid_layout(*test['params'])
        print(json.dumps(layout, indent=2))

        # Verification check for span
        if layout.get("status") == "OK" and layout.get("skid_count", 0) > 1:
            positions = layout["skid_positions"]
            skid_w = layout["skid_width"]
            first_outer = positions[0] - skid_w / 2
            last_outer = positions[-1] + skid_w / 2
            calc_span = last_outer - first_outer
            usable_w = layout["usable_width"]
            # Allow for tiny floating point differences
            if abs(calc_span - usable_w) > 0.001:
                 print(f"  [VERIFICATION FAILED] Calculated Span ({calc_span:.3f}) != Usable Width ({usable_w:.3f})")
            else:
                 print(f"  [VERIFICATION PASSED] Calculated Span ({calc_span:.3f}) == Usable Width ({usable_w:.3f})")
        elif layout.get("status") == "OK" and layout.get("skid_count", 0) == 1:
             positions = layout["skid_positions"]
             skid_w = layout["skid_width"]
             calc_span = skid_w # Span of one skid is its width
             usable_w = layout["usable_width"]
             print(f"  [VERIFICATION INFO] Single Skid Span ({calc_span:.3f}), Usable Width ({usable_w:.3f})")


