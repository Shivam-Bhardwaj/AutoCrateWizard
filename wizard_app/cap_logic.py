# wizard_app/cap_logic.py
"""
Logic for calculating the crate's top cap assembly.
Imports constants from config.py
"""

import logging
import math
from typing import Dict, List, Any

# Import from config
# Use absolute import assuming execution context is set up correctly
try:
    from . import config
except ImportError:
    # Fallback for potential direct script execution or testing
    import config

log = logging.getLogger(__name__)


def _calculate_cleats_layout(
    dimension_for_spacing: float,
    cleat_measure_for_spacing_calc: float,
    max_spacing_param: float,
    cleat_length: float,
    cleat_thickness: float
) -> Dict[str, Any]:
    """
    Helper function to calculate number, spacing, and positions of cleats along one dimension.
    """
    cleats_results = {
        "count": 0,
        "actual_spacing": 0.0,
        "positions": [],
        "cleat_length_each": cleat_length,
        "cleat_thickness_each": cleat_thickness,
        "cleat_width_each": cleat_measure_for_spacing_calc
    }

    log.debug(f"Calculating cleat layout: Dim={dimension_for_spacing:.2f}, CleatW={cleat_measure_for_spacing_calc:.2f}, MaxSpace={max_spacing_param:.2f}")

    if dimension_for_spacing < cleat_measure_for_spacing_calc - config.FLOAT_TOLERANCE:
        log.warning(f"Dimension {dimension_for_spacing:.2f} too small for cleat width {cleat_measure_for_spacing_calc:.2f}. Cannot place cleats.")
        return cleats_results

    num_cleats = 0
    if dimension_for_spacing < (2 * cleat_measure_for_spacing_calc) - config.FLOAT_TOLERANCE:
         num_cleats = 1
         log.debug("Dimension allows for only one cleat.")
    else:
        if max_spacing_param <= config.FLOAT_TOLERANCE:
             log.warning("Max cleat spacing is zero or negative. Defaulting to 2 edge cleats.")
             num_cleats = 2
        else:
            centerline_span = dimension_for_spacing - cleat_measure_for_spacing_calc
            if centerline_span < config.FLOAT_TOLERANCE:
                 log.warning(f"Centerline span ({centerline_span:.3f}) is near zero. Placing 2 cleats.")
                 num_cleats = 2
            else:
                num_spaces_needed = math.ceil(centerline_span / max_spacing_param)
                num_cleats_calculated = num_spaces_needed + 1
                num_cleats = max(2, num_cleats_calculated)
                log.debug(f"Calculated centerline_span={centerline_span:.2f}, num_spaces={num_spaces_needed}, initial_count={num_cleats_calculated}")

    actual_spacing = 0.0
    positions = []
    if num_cleats == 1:
        actual_spacing = 0.0
        positions = [0.0]
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
    # Corrected default values to use the constants from config.py
    cap_cleat_nominal_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS,
    cap_cleat_nominal_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH,
    max_top_cleat_spacing: float = 24.0
) -> Dict[str, Any]:
    """
    Calculates the layout for the crate's top cap assembly.
    """
    result = {
        "status": "INIT", "message": "Cap calculation not started.",
        "cap_panel_width": 0.0, "cap_panel_length": 0.0, "cap_panel_thickness": 0.0,
        "longitudinal_cleats": {},
        "transverse_cleats": {},
        "max_allowed_cleat_spacing_used": max_top_cleat_spacing,
        "cap_cleat_spec": {"thickness": cap_cleat_nominal_thickness, "width": cap_cleat_nominal_width}
    }
    log.info(f"Starting cap layout: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, PanelT={cap_panel_sheathing_thickness:.2f}, CleatTxW={cap_cleat_nominal_thickness:.2f}x{cap_cleat_nominal_width:.2f}, MaxSpace={max_top_cleat_spacing:.2f}")

    if crate_overall_width <= config.FLOAT_TOLERANCE or crate_overall_length <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Crate width/length must be positive."
        log.error(result["message"]); return result
    if cap_panel_sheathing_thickness <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Panel thickness must be positive."
        log.error(result["message"]); return result
    if cap_cleat_nominal_thickness <= config.FLOAT_TOLERANCE or cap_cleat_nominal_width <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Cleat dimensions must be positive."
        log.error(result["message"]); return result

    is_spacing_needed = (crate_overall_width >= (2 * cap_cleat_nominal_width) - config.FLOAT_TOLERANCE or
                         crate_overall_length >= (2 * cap_cleat_nominal_width) - config.FLOAT_TOLERANCE)
    if max_top_cleat_spacing <= config.FLOAT_TOLERANCE and is_spacing_needed:
        result["status"] = "ERROR"; result["message"] = "Max top cleat spacing must be positive."
        log.error(result["message"]); return result

    result["cap_panel_width"] = round(crate_overall_width, 4)
    result["cap_panel_length"] = round(crate_overall_length, 4)
    result["cap_panel_thickness"] = round(cap_panel_sheathing_thickness, 4)

    log.debug("Calculating longitudinal cleats...")
    longitudinal_cleats = _calculate_cleats_layout(
        dimension_for_spacing=crate_overall_width,
        cleat_measure_for_spacing_calc=cap_cleat_nominal_width,
        max_spacing_param=max_top_cleat_spacing,
        cleat_length=crate_overall_length,
        cleat_thickness=cap_cleat_nominal_thickness
    )
    result["longitudinal_cleats"] = longitudinal_cleats

    log.debug("Calculating transverse cleats...")
    transverse_cleats = _calculate_cleats_layout(
        dimension_for_spacing=crate_overall_length,
        cleat_measure_for_spacing_calc=cap_cleat_nominal_width,
        max_spacing_param=max_top_cleat_spacing,
        cleat_length=crate_overall_width,
        cleat_thickness=cap_cleat_nominal_thickness
    )
    if transverse_cleats["count"] < 2 and crate_overall_length >= (2 * cap_cleat_nominal_width) - config.FLOAT_TOLERANCE:
        log.warning(f"Transverse cleat count was {transverse_cleats['count']} for length {crate_overall_length:.2f}. Forcing minimum 2 for ends.")
        centerline_span_actual = crate_overall_length - cap_cleat_nominal_width
        start_pos = -centerline_span_actual / 2.0
        end_pos = centerline_span_actual / 2.0
        transverse_cleats["count"] = 2
        transverse_cleats["actual_spacing"] = centerline_span_actual
        transverse_cleats["positions"] = [round(start_pos, 4), round(end_pos, 4)]
    elif transverse_cleats["count"] < 2 and crate_overall_length >= cap_cleat_nominal_width - config.FLOAT_TOLERANCE :
        log.warning(f"Transverse cleat count was {transverse_cleats['count']} for length {crate_overall_length:.2f}. Forcing minimum 1 as length is small.")
        if transverse_cleats["count"] == 0:
            transverse_cleats["count"] = 1
            transverse_cleats["actual_spacing"] = 0.0
            transverse_cleats["positions"] = [0.0]
    result["transverse_cleats"] = transverse_cleats

    if longitudinal_cleats["count"] > 0 or transverse_cleats["count"] > 0:
        result["status"] = "OK"
        result["message"] = "Cap layout calculated successfully."
        if longitudinal_cleats["count"] == 0:
             result["message"] += " (Note: No longitudinal cleats placed due to small width)."
             result["status"] = "WARNING"
        if transverse_cleats["count"] == 0:
             result["message"] += " (Note: No transverse cleats placed due to small length)."
             result["status"] = "WARNING"
    else:
        result["status"] = "ERROR"
        result["message"] = "Failed to place any cap cleats (crate dimensions likely too small)."

    log.info(f"Cap Layout Calculation Complete. Final Status: {result['status']}")
    return result
