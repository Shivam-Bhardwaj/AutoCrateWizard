# skid_logic.py
"""
Core logic for calculating skid layout for industrial shipping crates
based on internal shipping standards.
"""

import math
import logging
from typing import Dict, List, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define nominal vs actual dimensions for clarity (based on standard lumber sizes)
# Format: "Nominal": (Actual_Width, Actual_Height)
# We assume skids are placed such that the larger dimension is height if different,
# unless specified otherwise (like 3x4 rotated).
SKID_DIMENSIONS = {
    "3x4": (2.5, 3.5),  # Rotated: Width = 2.5", Height = 3.5"
    "4x4": (3.5, 3.5),
    "4x6": (3.5, 5.5),  # Standard orientation for calculation: Width = 3.5", Height = 5.5"
                       # Per standard text, 4x6 seems used with width = 5.5" (placed flat?)
                       # Let's follow the pseudo-code's width interpretation for 4x6 -> 5.5" width.
                       # Re-defining based on pseudo-code for clarity:
    "4x6_calc": (5.5, 3.5) # Width = 5.5" (as used in pseudo-code), Height=3.5"
}

# Minimum required height per standard
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

    Args:
        product_weight: Weight of the product in lbs.
        product_width: Width of the product in inches.
        clearance_side: Clearance space on each side of the product in inches.
        panel_thickness: Thickness of the crate side panels in inches.
        cleat_thickness: Thickness of the crate cleats in inches.

    Returns:
        A dictionary containing skid layout parameters or an error status.
        Keys: "skid_type", "skid_width", "skid_height", "skid_count",
              "spacing_actual", "max_spacing", "crate_width", "usable_width",
              "skid_positions", "status", "message" (optional error details)
    """
    result = {
        "skid_type": None, "skid_width": None, "skid_height": None,
        "skid_count": None, "spacing_actual": 0.0, "max_spacing": None,
        "crate_width": None, "usable_width": None, "skid_positions": None,
        "status": "ERROR", "message": None
    }

    # --- Input Validation ---
    if product_weight < 0:
        result["message"] = "Weight cannot be negative."
        logging.error(result["message"])
        return result
    if product_width <= 0:
        result["message"] = "Product width must be positive."
        logging.error(result["message"])
        return result
    if clearance_side < 0 or panel_thickness < 0 or cleat_thickness < 0:
         result["message"] = "Dimensions (clearance, panel, cleat) cannot be negative."
         logging.error(result["message"])
         return result

    logging.info(f"Calculating layout for Weight={product_weight} lbs, Width={product_width}\"")

    # --- Determine Skid Type, Width, Height, and Max Spacing (Internal Standard, up to 20k lbs) ---
    if product_weight <= 0: # Treat 0 weight as needing minimal support
         skid_type_nominal = "3x4"
         skid_width = SKID_DIMENSIONS[skid_type_nominal][0]
         skid_height = SKID_DIMENSIONS[skid_type_nominal][1]
         max_spacing = 30.0
    elif 0 < product_weight <= 500:
        skid_type_nominal = "3x4" # Optional 4x4 allowed, defaulting to 3x4 rotated
        skid_width = SKID_DIMENSIONS[skid_type_nominal][0] # 2.5"
        skid_height = SKID_DIMENSIONS[skid_type_nominal][1] # 3.5"
        max_spacing = 30.0
    elif product_weight <= 4500:
        skid_type_nominal = "4x4"
        skid_width = SKID_DIMENSIONS[skid_type_nominal][0] # 3.5"
        skid_height = SKID_DIMENSIONS[skid_type_nominal][1] # 3.5"
        max_spacing = 30.0
    elif product_weight <= 20000:
        skid_type_nominal = "4x6" # Using 4x6 based on weight range
        # Using width=5.5" as per pseudo-code's interpretation for calculation
        skid_width = SKID_DIMENSIONS["4x6_calc"][0] # 5.5"
        skid_height = SKID_DIMENSIONS["4x6_calc"][1] # 3.5" (Meets min height)

        if product_weight <= 6000:
            max_spacing = 41.0
        elif product_weight <= 12000:
            max_spacing = 28.0
        else: # 12001 to 20000 lbs
            max_spacing = 24.0
    else: # product_weight > 20000
        result["status"] = "OVER"
        result["message"] = "Weight exceeds 20,000 lbs limit for this configuration."
        logging.warning(result["message"])
        return result

    result.update({
        "skid_type": skid_type_nominal,
        "skid_width": skid_width,
        "skid_height": skid_height,
        "max_spacing": max_spacing,
    })
    logging.info(f"Selected Skid: {skid_type_nominal}, Width: {skid_width}\", Height: {skid_height}\", Max Spacing: {max_spacing}\"")

    # --- Validate Skid Height Requirement ---
    if skid_height < MIN_SKID_HEIGHT:
         result["message"] = f"Calculated skid height ({skid_height}\") is less than minimum required ({MIN_SKID_HEIGHT}\"). Check SKID_DIMENSIONS."
         logging.error(result["message"])
         return result

    # --- Calculate Crate and Usable Width ---
    crate_width = product_width + 2 * (clearance_side + panel_thickness + cleat_thickness)
    usable_width = crate_width - 2 * (panel_thickness + cleat_thickness) # Space between inner faces of side cleats/panels
    result.update({
        "crate_width": crate_width,
        "usable_width": usable_width
    })
    logging.info(f"Crate Width: {crate_width:.2f}\", Usable Width: {usable_width:.2f}\"")

    # --- Determine Minimum Skid Count and Spacing ---
    if usable_width < skid_width:
        result["message"] = f"Crate usable width ({usable_width:.2f}\") is too narrow for the selected skid width ({skid_width:.2f}\")."
        logging.error(result["message"])
        return result

    if usable_width <= skid_width:
        skid_count = 1
        spacing_actual = 0.0
    elif usable_width < (2 * skid_width):
        skid_count = 1
        spacing_actual = 0.0
        logging.warning(f"Usable width ({usable_width:.2f}\") allows only one skid ({skid_width:.2f}\"). Centering single skid.")
    else:
        skid_count = 2
        spacing_actual = usable_width / (skid_count - 1)
        while spacing_actual > max_spacing and (skid_count -1) > 0 :
            skid_count += 1
            spacing_actual = usable_width / (skid_count - 1)
            logging.debug(f"Spacing {spacing_actual:.2f} > Max {max_spacing:.2f}. Increasing skid count to {skid_count}.")

    result.update({
        "skid_count": skid_count,
        "spacing_actual": spacing_actual if skid_count > 1 else 0.0
    })
    logging.info(f"Calculated Skid Count: {skid_count}, Actual Spacing: {result['spacing_actual']:.2f}\"")


    # --- Calculate Skid Positions (Centered within Usable Width) ---
    skid_positions = []
    if skid_count == 1:
        skid_positions = [0.0]
    elif skid_count > 1:
        start_x = - (spacing_actual * (skid_count - 1)) / 2.0
        for i in range(skid_count):
            position = start_x + i * spacing_actual
            skid_positions.append(position)

    result["skid_positions"] = skid_positions
    logging.info(f"Skid Positions (Centerlines): {['%.2f' % p for p in skid_positions]}")

    # --- Final Status Check & Return ---
    if skid_count > 1 and spacing_actual > max_spacing:
        result["status"] = "TOO WIDE"
        result["message"] = f"Calculated spacing ({spacing_actual:.2f}\") exceeds maximum allowed ({max_spacing:.2f}\"). Logic error?"
        logging.error(result["message"])
    elif skid_count > 0 :
        result["status"] = "OK"
        result["message"] = "Skid layout calculated successfully."
        logging.info(result["message"])
    else:
        result["status"] = "ERROR"
        result["message"] = "Failed to determine skid count or positions."
        logging.error(result["message"])

    # --- Acknowledge Additional Standards (Not calculated/validated here) ---
    logging.debug("Standard Compliance Notes:")
    logging.debug("- Skid Height: Requirement >= 3.5\". Met by selected types.")
    logging.debug("- Splicing: Prohibited. Assumed no splicing occurs.")
    logging.debug("- Warping: Limit <= 1/4\". Assumed material meets standard.")

    return result

# Example usage
if __name__ == "__main__":
    test_weight = 4600
    test_width = 90
    test_clearance = 2.0
    test_panel = 0.25
    test_cleat = 0.75
    layout = calculate_skid_layout(
        test_weight, test_width, test_clearance, test_panel, test_cleat
    )
    import json
    print(json.dumps(layout, indent=4))
