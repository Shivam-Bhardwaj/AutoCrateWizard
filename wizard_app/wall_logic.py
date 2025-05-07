# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and end wall panels.
Uses simplified cleat logic for initial implementation.
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

def _calculate_single_panel_layout(
    panel_width: float,
    panel_height: float,
    plywood_thickness: float,
    cleat_thickness: float,
    cleat_width: float,
    panel_type: str # 'side' or 'end'
) -> Dict[str, Any]:
    """
    Helper function to calculate layout for a single wall panel.
    Uses simplified intermediate cleat logic.
    """
    panel_layout = {
        "panel_width": round(panel_width, 4),
        "panel_height": round(panel_height, 4),
        "plywood_thickness": round(plywood_thickness, 4),
        "cleats": [],
        "cleat_spec": {"thickness": cleat_thickness, "width": cleat_width}
    }
    cleats = []

    log.debug(f"Calculating {panel_type} panel layout: W={panel_width:.2f}, H={panel_height:.2f}, Cleat={cleat_thickness:.2f}x{cleat_width:.2f}")

    # --- Edge Cleats ---
    if panel_type == 'side':
        # Horizontal edge cleats run full length (panel_width)
        # Top edge cleat
        cleats.append({
            "type": "edge_horizontal", "orientation": "horizontal",
            "length": panel_width, "thickness": cleat_thickness, "width": cleat_width,
            "position_x": 0, # Centered horizontally for reference
            "position_y": panel_height - cleat_width / 2 # Centered vertically at top edge
        })
        # Bottom edge cleat
        cleats.append({
            "type": "edge_horizontal", "orientation": "horizontal",
            "length": panel_width, "thickness": cleat_thickness, "width": cleat_width,
            "position_x": 0, # Centered horizontally for reference
            "position_y": cleat_width / 2 # Centered vertically at bottom edge
        })
        # Vertical edge cleats run between horizontal edge cleats
        vertical_cleat_length = panel_height - 2 * cleat_width
        if vertical_cleat_length > config.FLOAT_TOLERANCE:
            # Left edge cleat
            cleats.append({
                "type": "edge_vertical", "orientation": "vertical",
                "length": vertical_cleat_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": -panel_width / 2 + cleat_width / 2, # Centered horizontally at left edge
                "position_y": panel_height / 2 # Centered vertically for reference
            })
            # Right edge cleat
            cleats.append({
                "type": "edge_vertical", "orientation": "vertical",
                "length": vertical_cleat_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": panel_width / 2 - cleat_width / 2, # Centered horizontally at right edge
                "position_y": panel_height / 2 # Centered vertically for reference
            })
        else:
            log.warning(f"Panel height {panel_height:.2f} too small for vertical edge cleats between horizontal cleats of width {cleat_width:.2f}.")

    elif panel_type == 'end':
        # Vertical edge cleats run full height (panel_height)
        # Left edge cleat
        cleats.append({
            "type": "edge_vertical", "orientation": "vertical",
            "length": panel_height, "thickness": cleat_thickness, "width": cleat_width,
            "position_x": -panel_width / 2 + cleat_width / 2, # Centered horizontally at left edge
            "position_y": panel_height / 2 # Centered vertically for reference
        })
        # Right edge cleat
        cleats.append({
            "type": "edge_vertical", "orientation": "vertical",
            "length": panel_height, "thickness": cleat_thickness, "width": cleat_width,
            "position_x": panel_width / 2 - cleat_width / 2, # Centered horizontally at right edge
            "position_y": panel_height / 2 # Centered vertically for reference
        })
        # Horizontal edge cleats run between vertical edge cleats
        horizontal_cleat_length = panel_width - 2 * cleat_width
        if horizontal_cleat_length > config.FLOAT_TOLERANCE:
            # Top edge cleat
            cleats.append({
                "type": "edge_horizontal", "orientation": "horizontal",
                "length": horizontal_cleat_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": 0, # Centered horizontally for reference
                "position_y": panel_height - cleat_width / 2 # Centered vertically at top edge
            })
            # Bottom edge cleat
            cleats.append({
                "type": "edge_horizontal", "orientation": "horizontal",
                "length": horizontal_cleat_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": 0, # Centered horizontally for reference
                "position_y": cleat_width / 2 # Centered vertically at bottom edge
            })
        else:
            log.warning(f"Panel width {panel_width:.2f} too small for horizontal edge cleats between vertical cleats of width {cleat_width:.2f}.")

    # --- Simplified Intermediate Cleats ---
    # Add one centered vertical cleat if panel width is large
    if panel_width > config.INTERMEDIATE_CLEAT_THRESHOLD + config.FLOAT_TOLERANCE:
        intermediate_vertical_length = panel_height - (2 * cleat_width if panel_type == 'side' else 0) # Runs between horizontal edges if side panel
        if intermediate_vertical_length > config.FLOAT_TOLERANCE:
             cleats.append({
                "type": "intermediate_vertical", "orientation": "vertical",
                "length": intermediate_vertical_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": 0, # Centered horizontally
                "position_y": panel_height / 2 # Centered vertically
            })
             log.debug(f"Added intermediate vertical cleat for {panel_type} panel (Width > {config.INTERMEDIATE_CLEAT_THRESHOLD})")

    # Add one centered horizontal cleat if panel height is large
    if panel_height > config.INTERMEDIATE_CLEAT_THRESHOLD + config.FLOAT_TOLERANCE:
        intermediate_horizontal_length = panel_width - (2 * cleat_width if panel_type == 'end' else 0) # Runs between vertical edges if end panel
        if intermediate_horizontal_length > config.FLOAT_TOLERANCE:
            cleats.append({
                "type": "intermediate_horizontal", "orientation": "horizontal",
                "length": intermediate_horizontal_length, "thickness": cleat_thickness, "width": cleat_width,
                "position_x": 0, # Centered horizontally
                "position_y": panel_height / 2 # Centered vertically
            })
            log.debug(f"Added intermediate horizontal cleat for {panel_type} panel (Height > {config.INTERMEDIATE_CLEAT_THRESHOLD})")


    panel_layout["cleats"] = cleats
    return panel_layout

def calculate_wall_panels(
    crate_overall_width: float,
    crate_overall_length: float,
    panel_height: float, # Calculated height for side/end panels
    panel_thickness: float, # Plywood thickness
    wall_cleat_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS,
    wall_cleat_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH,
) -> Dict[str, Any]:
    """
    Calculates the layout for the crate's side and end wall panels.
    Assumes cleated plywood construction.
    """
    result = {
        "status": "INIT", "message": "Wall panel calculation not started.",
        "side_panels": [], # Should contain layout for 2 side panels
        "end_panels": [],  # Should contain layout for 2 end panels
        "panel_height_used": 0.0,
        "panel_plywood_thickness_used": 0.0,
        "wall_cleat_spec": {"thickness": wall_cleat_thickness, "width": wall_cleat_width}
    }
    log.info(f"Starting wall panel calculation: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, PanelH={panel_height:.2f}, PanelT={panel_thickness:.2f}, Cleat={wall_cleat_thickness:.2f}x{wall_cleat_width:.2f}")

    # --- Input Validation ---
    if crate_overall_width <= config.FLOAT_TOLERANCE or crate_overall_length <= config.FLOAT_TOLERANCE or panel_height <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Crate dimensions and panel height must be positive."
        log.error(result["message"]); return result
    if panel_thickness < config.WALL_PLYWOOD_THICKNESS_MIN - config.FLOAT_TOLERANCE:
        log.warning(f"Input panel thickness {panel_thickness:.3f} is less than minimum {config.WALL_PLYWOOD_THICKNESS_MIN:.3f}. Using default {config.DEFAULT_WALL_PLYWOOD_THICKNESS:.3f}.")
        plywood_thickness_to_use = config.DEFAULT_WALL_PLYWOOD_THICKNESS
    else:
        plywood_thickness_to_use = panel_thickness

    if wall_cleat_thickness <= config.FLOAT_TOLERANCE or wall_cleat_width <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Wall cleat dimensions must be positive."
        log.error(result["message"]); return result

    result["panel_height_used"] = round(panel_height, 4)
    result["panel_plywood_thickness_used"] = round(plywood_thickness_to_use, 4)

    # --- Calculate Side Panels (Length = crate_overall_length) ---
    # Assuming 2 identical side panels
    log.debug("Calculating side panels...")
    side_panel_layout = _calculate_single_panel_layout(
        panel_width=crate_overall_length, # Side panel width is crate length
        panel_height=panel_height,
        plywood_thickness=plywood_thickness_to_use,
        cleat_thickness=wall_cleat_thickness,
        cleat_width=wall_cleat_width,
        panel_type='side'
    )
    result["side_panels"] = [side_panel_layout, side_panel_layout] # Add two copies

    # --- Calculate End Panels (Width = crate_overall_width) ---
    # Assuming 2 identical end panels
    log.debug("Calculating end panels...")
    end_panel_layout = _calculate_single_panel_layout(
        panel_width=crate_overall_width, # End panel width is crate width
        panel_height=panel_height,
        plywood_thickness=plywood_thickness_to_use,
        cleat_thickness=wall_cleat_thickness,
        cleat_width=wall_cleat_width,
        panel_type='end'
    )
    result["end_panels"] = [end_panel_layout, end_panel_layout] # Add two copies

    # --- Final Status ---
    total_cleats = len(side_panel_layout.get("cleats", [])) * 2 + len(end_panel_layout.get("cleats", [])) * 2
    if total_cleats > 0:
        result["status"] = "OK"
        result["message"] = "Wall panel layouts calculated successfully (simplified cleats)."
    else:
        result["status"] = "ERROR"
        result["message"] = "Failed to calculate any wall panel cleats."

    log.info(f"Wall Panel Calculation Complete. Final Status: {result['status']}")
    return result
