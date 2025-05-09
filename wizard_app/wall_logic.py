# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and back wall panels.
Includes splicing logic and intermediate cleat placement based on max spacing.
Version updated for v0.6.9 changes.
"""

import logging
import math
from typing import Dict, List, Any, Tuple

try:
    # Use absolute imports if running as part of the package
    from . import config
except ImportError:
    # Fallback to relative/direct import if run standalone or package structure differs
    import config 

log = logging.getLogger(__name__)

# Constants from config
PLYWOOD_STD_WIDTH = config.PLYWOOD_STD_WIDTH
PLYWOOD_STD_HEIGHT = config.PLYWOOD_STD_HEIGHT
# Use MAX_INTERMEDIATE_CLEAT_SPACING if defined, otherwise fallback
MAX_CLEAT_SPACING = getattr(config, 'MAX_INTERMEDIATE_CLEAT_SPACING', config.INTERMEDIATE_CLEAT_THRESHOLD)
FLOAT_TOL = config.FLOAT_TOLERANCE

def _calculate_intermediate_cleat_positions(
    span_dimension: float, # The dimension ACROSS which cleats are spaced (e.g., panel_width for vertical cleats)
    cleat_actual_width: float, # Width of the cleat lumber itself (e.g., 3.5")
    max_spacing: float, # Maximum allowed center-to-center spacing
    existing_cleat_centers_relative: List[float] # Sorted list of existing cleat center positions (edge/splice) relative to panel center along the span dimension
) -> List[float]:
    """
    Calculates the positions for intermediate cleats based on max spacing rules,
    fitting them between the outermost existing cleats.
    Returns a list of relative center positions for the new intermediate cleats.
    """
    intermediate_positions = []
    if not existing_cleat_centers_relative or len(existing_cleat_centers_relative) < 2:
        log.debug("Not enough existing cleats to place intermediates between.")
        return intermediate_positions

    # Span between the centerlines of the outermost existing cleats
    outermost_span_centers = abs(existing_cleat_centers_relative[-1] - existing_cleat_centers_relative[0])
    
    # The clear space available between the inner edges of the outermost cleats
    clear_span_for_intermediates = outermost_span_centers - cleat_actual_width

    log.debug(f"Calculating intermediates: Outermost span={outermost_span_centers:.2f}, CleatW={cleat_actual_width:.2f}, Clear span={clear_span_for_intermediates:.2f}, MaxSpace={max_spacing:.2f}")

    if clear_span_for_intermediates <= max_spacing + FLOAT_TOL:
        log.debug("Clear span is less than or equal to max spacing. No intermediate cleats needed.")
        return intermediate_positions

    # Calculate the number of spaces needed within the clear span
    num_spaces = math.ceil(clear_span_for_intermediates / max_spacing)
    num_intermediate_cleats = num_spaces - 1

    if num_intermediate_cleats < 1:
        log.debug(f"Calculated {num_spaces} spaces, needing {num_intermediate_cleats} cleats. None required.")
        return intermediate_positions
        
    # Calculate the actual spacing between cleats (including edges/splices and new intermediates)
    # Total items defining the spaces = 2 (outermost existing) + num_intermediate_cleats
    total_cleats_in_span = 2 + num_intermediate_cleats
    actual_spacing = outermost_span_centers / (total_cleats_in_span - 1)
    
    log.debug(f"Need {num_intermediate_cleats} intermediate cleats with actual spacing {actual_spacing:.2f}")

    # Calculate positions relative to the first outermost cleat's center
    first_outermost_pos = existing_cleat_centers_relative[0]
    for i in range(1, num_intermediate_cleats + 1):
        # Position = start_pos + i * actual_spacing
        pos = first_outermost_pos + i * actual_spacing
        intermediate_positions.append(round(pos, 4))
        
    log.debug(f"Calculated intermediate cleat relative positions: {intermediate_positions}")
    return intermediate_positions


def _calculate_single_panel_layout(
    panel_width: float, panel_height: float, plywood_thickness: float,
    cleat_thickness: float, cleat_actual_width: float, panel_type: str 
) -> Dict[str, Any]:
    """Calculates layout for a single wall panel, including splicing and intermediate cleats based on max spacing."""
    panel_layout = {
        "panel_width": round(panel_width, 4),
        "panel_height": round(panel_height, 4),
        "plywood_thickness": round(plywood_thickness, 4),
        "cleats": [],
        "plywood_pieces": [],
        "cleat_spec": {"thickness": cleat_thickness, "width": cleat_actual_width}
    }
    cleats = panel_layout["cleats"] 
    plywood_pieces = panel_layout["plywood_pieces"]

    log.debug(f"Calculating {panel_type} panel: W={panel_width:.2f}, H={panel_height:.2f}, PlywoodT={plywood_thickness:.2f} CleatSpec={cleat_thickness:.2f}x{cleat_actual_width:.2f}")

    # 1. Determine Plywood Pieces (coordinates relative to panel 0,0 bottom-left)
    needs_vertical_splice = panel_width > PLYWOOD_STD_WIDTH + FLOAT_TOL
    needs_horizontal_splice = panel_height > PLYWOOD_STD_HEIGHT + FLOAT_TOL

    if not needs_vertical_splice and not needs_horizontal_splice:
        plywood_pieces.append({"x0": 0, "y0": 0, "x1": panel_width, "y1": panel_height})
    elif needs_vertical_splice and not needs_horizontal_splice:
        plywood_pieces.append({"x0": 0, "y0": 0, "x1": PLYWOOD_STD_WIDTH, "y1": panel_height})
        plywood_pieces.append({"x0": PLYWOOD_STD_WIDTH, "y0": 0, "x1": panel_width, "y1": panel_height})
    elif not needs_vertical_splice and needs_horizontal_splice:
        plywood_pieces.append({"x0": 0, "y0": 0, "x1": panel_width, "y1": PLYWOOD_STD_HEIGHT})
        plywood_pieces.append({"x0": 0, "y0": PLYWOOD_STD_HEIGHT, "x1": panel_width, "y1": panel_height})
    else: # Both splices needed
        plywood_pieces.append({"x0": 0, "y0": 0, "x1": PLYWOOD_STD_WIDTH, "y1": PLYWOOD_STD_HEIGHT}) # Bottom-Left
        plywood_pieces.append({"x0": PLYWOOD_STD_WIDTH, "y0": 0, "x1": panel_width, "y1": PLYWOOD_STD_HEIGHT}) # Bottom-Right
        plywood_pieces.append({"x0": 0, "y0": PLYWOOD_STD_HEIGHT, "x1": PLYWOOD_STD_WIDTH, "y1": panel_height}) # Top-Left
        plywood_pieces.append({"x0": PLYWOOD_STD_WIDTH, "y0": PLYWOOD_STD_HEIGHT, "x1": panel_width, "y1": panel_height}) # Top-Right
    
    log.debug(f"Calculated {len(plywood_pieces)} plywood pieces.")

    # 2. Edge & Splice Cleats (positions relative to panel center)
    center_x_panel = panel_width / 2.0
    center_y_panel = panel_height / 2.0
    vertical_cleat_centers_rel = [] # Store relative X positions
    horizontal_cleat_centers_rel = [] # Store relative Y positions

    # --- Add Edge Cleats ---
    # Determine which orientation runs full length based on panel type
    vert_runs_full = (panel_type == 'back') # Vertical cleats run full height on back panels
    horiz_runs_full = (panel_type == 'side') # Horizontal cleats run full width on side panels

    # Vertical Edge Cleats (Left/Right)
    pos_x_left = -center_x_panel + cleat_actual_width / 2.0
    pos_x_right = center_x_panel - cleat_actual_width / 2.0
    v_edge_cleat_len = panel_height if vert_runs_full else panel_height - 2 * cleat_actual_width
    if v_edge_cleat_len > FLOAT_TOL:
        cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": round(v_edge_cleat_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": round(pos_x_left,4), "position_y": 0})
        cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": round(v_edge_cleat_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": round(pos_x_right,4), "position_y": 0})
        vertical_cleat_centers_rel.extend([pos_x_left, pos_x_right])
        log.debug(f"Added V edge cleats: Len={v_edge_cleat_len:.2f} at X_rel={pos_x_left:.2f}, {pos_x_right:.2f}")
    
    # Horizontal Edge Cleats (Top/Bottom)
    pos_y_bottom = -center_y_panel + cleat_actual_width / 2.0
    pos_y_top = center_y_panel - cleat_actual_width / 2.0
    h_edge_cleat_len = panel_width if horiz_runs_full else panel_width - 2 * cleat_actual_width
    if h_edge_cleat_len > FLOAT_TOL:
        cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": round(h_edge_cleat_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": round(pos_y_bottom,4)})
        cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": round(h_edge_cleat_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": round(pos_y_top,4)})
        horizontal_cleat_centers_rel.extend([pos_y_bottom, pos_y_top])
        log.debug(f"Added H edge cleats: Len={h_edge_cleat_len:.2f} at Y_rel={pos_y_bottom:.2f}, {pos_y_top:.2f}")

    # --- Add Splice Cleats ---
    if needs_vertical_splice:
        splice_cleat_x_abs = PLYWOOD_STD_WIDTH
        splice_cleat_x_rel = splice_cleat_x_abs - center_x_panel
        # Length depends on whether horizontal cleats interrupt it
        splice_v_len = panel_height if vert_runs_full else panel_height - 2 * cleat_actual_width
        if splice_v_len > FLOAT_TOL:
             cleats.append({"type": "splice_vertical", "orientation": "vertical", "length": round(splice_v_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": round(splice_cleat_x_rel, 4), "position_y": 0})
             vertical_cleat_centers_rel.append(splice_cleat_x_rel)
             log.debug(f"Added V splice cleat: Len={splice_v_len:.2f} at X_rel={splice_cleat_x_rel:.2f}")

    if needs_horizontal_splice:
        splice_cleat_y_abs = PLYWOOD_STD_HEIGHT
        splice_cleat_y_rel = splice_cleat_y_abs - center_y_panel
        # Length depends on whether vertical cleats interrupt it
        splice_h_len = panel_width if horiz_runs_full else panel_width - 2 * cleat_actual_width
        # TODO: Handle case where H splice crosses V splice - needs splitting. Keeping simple for now.
        if splice_h_len > FLOAT_TOL:
             cleats.append({"type": "splice_horizontal", "orientation": "horizontal", "length": round(splice_h_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": round(splice_cleat_y_rel, 4)})
             horizontal_cleat_centers_rel.append(splice_cleat_y_rel)
             log.debug(f"Added H splice cleat: Len={splice_h_len:.2f} at Y_rel={splice_cleat_y_rel:.2f}")
             
    # Sort existing cleat positions
    vertical_cleat_centers_rel.sort()
    horizontal_cleat_centers_rel.sort()

    # 3. Add Intermediate Cleats
    # Vertical Intermediates (spaced across width)
    intermediate_v_cleat_positions = _calculate_intermediate_cleat_positions(
        panel_width, cleat_actual_width, MAX_CLEAT_SPACING, vertical_cleat_centers_rel
    )
    if intermediate_v_cleat_positions:
        # Length depends on panel type (if horizontal edges interrupt)
        intermediate_v_len = panel_height if vert_runs_full else panel_height - 2 * cleat_actual_width
        if intermediate_v_len > FLOAT_TOL:
            for pos_x in intermediate_v_cleat_positions:
                 cleats.append({"type": "intermediate_vertical", "orientation": "vertical", "length": round(intermediate_v_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": pos_x, "position_y": 0})
            log.debug(f"Added {len(intermediate_v_cleat_positions)} V intermediate cleats.")
        else:
            log.warning("Skipped V intermediate cleats due to calculated length <= 0.")

    # Horizontal Intermediates (spaced across height)
    intermediate_h_cleat_positions = _calculate_intermediate_cleat_positions(
        panel_height, cleat_actual_width, MAX_CLEAT_SPACING, horizontal_cleat_centers_rel
    )
    if intermediate_h_cleat_positions:
        # Length depends on panel type (if vertical edges interrupt)
        # TODO: Needs refinement if vertical splices exist - intermediate might be split. Simple for now.
        intermediate_h_len = panel_width if horiz_runs_full else panel_width - 2 * cleat_actual_width
        if intermediate_h_len > FLOAT_TOL:
            for pos_y in intermediate_h_cleat_positions:
                 cleats.append({"type": "intermediate_horizontal", "orientation": "horizontal", "length": round(intermediate_h_len, 4), "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": pos_y})
            log.debug(f"Added {len(intermediate_h_cleat_positions)} H intermediate cleats.")
        else:
            log.warning("Skipped H intermediate cleats due to calculated length <= 0.")
            
    log.debug(f"Final cleat count for {panel_type} panel: {len(cleats)}")
    return panel_layout


def calculate_wall_panels(
    crate_overall_width: float, crate_overall_length: float, panel_height: float, panel_plywood_thickness: float,
    wall_cleat_actual_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS, 
    wall_cleat_actual_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH     
) -> Dict[str, Any]:
    """Calculates wall panels using updated logic including intermediate cleat spacing."""
    result = {
        "status": "INIT", "message": "Wall panel calculation not started.",
        "side_panels": [], "back_panels": [], # Changed from end_panels
        "panel_height_used": 0.0,
        "panel_plywood_thickness_used": 0.0,
        "wall_cleat_spec": {"thickness": wall_cleat_actual_thickness, "width": wall_cleat_actual_width}
    }
    log.info(f"Starting wall panel calculation: CrateW={crate_overall_width:.2f}, CrateL={crate_overall_length:.2f}, PanelH={panel_height:.2f}, PanelT={panel_plywood_thickness:.2f}, CleatActualTxW={wall_cleat_actual_thickness:.2f}x{wall_cleat_actual_width:.2f}")

    # --- Input Validation ---
    if not (crate_overall_width > FLOAT_TOL and crate_overall_length > FLOAT_TOL and panel_height > FLOAT_TOL):
        result["status"] = "ERROR"; result["message"] = "Crate dimensions (W, L) and panel height must be positive."
        log.error(result["message"]); return result
    plywood_thickness_to_use = panel_plywood_thickness
    if panel_plywood_thickness < config.WALL_PLYWOOD_THICKNESS_MIN - FLOAT_TOL:
        log.warning(f"Input panel plywood thickness {panel_plywood_thickness:.3f} < min {config.WALL_PLYWOOD_THICKNESS_MIN:.3f}. Using default {config.DEFAULT_WALL_PLYWOOD_THICKNESS:.3f}.")
        plywood_thickness_to_use = config.DEFAULT_WALL_PLYWOOD_THICKNESS
    if not (wall_cleat_actual_thickness > FLOAT_TOL and wall_cleat_actual_width > FLOAT_TOL):
        result["status"] = "ERROR"; result["message"] = "Wall cleat dimensions (thickness, width) must be positive."
        log.error(result["message"]); return result

    result["panel_height_used"] = round(panel_height, 4)
    result["panel_plywood_thickness_used"] = round(plywood_thickness_to_use, 4)

    # --- Calculate Panels ---
    try:
        log.debug("Calculating side panels...")
        side_panel_layout = _calculate_single_panel_layout(
            panel_width=crate_overall_length, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='side'
        )
        # Assuming two identical side panels
        result["side_panels"] = [side_panel_layout, side_panel_layout] 

        log.debug("Calculating back panels...")
        back_panel_layout = _calculate_single_panel_layout( # Changed from end
            panel_width=crate_overall_width, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='back' # Changed from end
        )
        # Assuming two identical back panels
        result["back_panels"] = [back_panel_layout, back_panel_layout] # Changed from end_panels

        # Basic check for successful calculation (at least edge cleats should exist if dims are valid)
        total_cleats_side = len(side_panel_layout.get("cleats", []))
        total_cleats_back = len(back_panel_layout.get("cleats", [])) 
        if total_cleats_side > 0 and total_cleats_back > 0 : 
            result["status"] = "OK"
            result["message"] = "Wall panel layouts calculated successfully (intermediate cleats based on spacing)."
        elif total_cleats_side == 0 and total_cleats_back == 0:
             result["status"] = "ERROR"; result["message"] = "Failed to calculate any wall panel cleats for both side and back panels."
        else: 
            result["status"] = "WARNING"
            result["message"] = "Wall panel layouts calculated, but one panel type may have no cleats."
            if total_cleats_side == 0: result["message"] += " Side panels have no cleats."
            if total_cleats_back == 0: result["message"] += " Back panels have no cleats."

    except Exception as e:
        log.error(f"Error during wall panel calculation: {e}", exc_info=True)
        result["status"] = "CRITICAL ERROR"
        result["message"] = f"An unexpected error occurred: {e}"

    log.info(f"Wall Panel Calculation Complete. Final Status: {result['status']}")
    return result