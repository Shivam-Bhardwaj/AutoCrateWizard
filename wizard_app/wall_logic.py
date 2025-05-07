# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and back wall panels.
Includes basic splicing logic and simplified intermediate cleat placement
(adds max one central intermediate per large span > INTERMEDIATE_CLEAT_ADD_THRESHOLD).
"""

import logging
import math
from typing import Dict, List, Any

try:
    from . import config
except ImportError:
    import config # Fallback

log = logging.getLogger(__name__)

# Constants from config are preferred, but if defined locally, ensure they match or are intended.
# PLYWOOD_STD_WIDTH = config.PLYWOOD_STD_WIDTH (already in config)
# PLYWOOD_STD_HEIGHT = config.PLYWOOD_STD_HEIGHT (already in config)
INTERMEDIATE_CLEAT_ADD_THRESHOLD = config.INTERMEDIATE_CLEAT_THRESHOLD # Use from config

def _add_intermediate_cleats_simplified(
    cleats_list: List[Dict],
    span_dimension: float, # e.g. panel_width for vertical cleats, panel_height for horizontal
    run_dimension: float,  # e.g. panel_height for vertical cleats, panel_width for horizontal
    cleat_thickness: float,
    cleat_actual_width: float, # Actual width of the cleat lumber (e.g. 3.5")
    orientation: str, # "vertical" or "horizontal"
    existing_cleat_center_positions_relative: List[float], # Positions relative to panel center
    edge_cleat_allowance_on_run_dim: float # e.g., 2 * cleat_actual_width for side panel vertical cleats
):
    """
    Adds at most ONE central intermediate cleat if the largest span between existing
    edge/splice cleats is greater than INTERMEDIATE_CLEAT_ADD_THRESHOLD.
    Positions are relative to the center of the panel.
    """
    log.debug(f"Attempting to add simplified intermediate {orientation} cleats: SpanDim={span_dimension:.2f}, RunDim={run_dimension:.2f}, ExistingPos={existing_cleat_center_positions_relative}")

    if not existing_cleat_center_positions_relative or len(existing_cleat_center_positions_relative) < 2:
        # Need at least two cleats (e.g., edges) to define a span between them.
        # If only one edge cleat exists (e.g. very narrow panel), no intermediate.
        # If panel is wide enough for intermediate but no edge cleats defined (error), skip.
        log.debug(f"Not enough existing {orientation} cleats to define a span for intermediates.")
        return

    # Sort positions to find outermost cleats
    sorted_positions = sorted(existing_cleat_center_positions_relative)
    outermost_cleat1_pos = sorted_positions[0]
    outermost_cleat2_pos = sorted_positions[-1]

    # This is the span between the centerlines of the two outermost existing cleats
    span_between_outermost_cleat_centers = abs(outermost_cleat2_pos - outermost_cleat1_pos)

    # The space available for intermediate cleats is between the inner edges of these outermost cleats.
    # Inner edge of cleat1 = outermost_cleat1_pos + cleat_actual_width / 2
    # Inner edge of cleat2 = outermost_cleat2_pos - cleat_actual_width / 2
    # Span available = (outermost_cleat2_pos - cleat_actual_width/2) - (outermost_cleat1_pos + cleat_actual_width/2)
    #              = outermost_cleat2_pos - outermost_cleat1_pos - cleat_actual_width
    #              = span_between_outermost_cleat_centers - cleat_actual_width
    centerline_span_available_for_intermediate = span_between_outermost_cleat_centers - cleat_actual_width

    log.debug(f"  Outermost existing {orientation} cleats at rel_pos {outermost_cleat1_pos:.2f} and {outermost_cleat2_pos:.2f}.")
    log.debug(f"  Span between their centers: {span_between_outermost_cleat_centers:.2f}")
    log.debug(f"  Effective span available for intermediate cleats (between inner edges): {centerline_span_available_for_intermediate:.2f}")

    pos_axis = "position_x" if orientation == "vertical" else "position_y" # Axis along which cleat is positioned

    if centerline_span_available_for_intermediate > INTERMEDIATE_CLEAT_ADD_THRESHOLD + config.FLOAT_TOLERANCE:
        # Calculate length of this intermediate cleat
        intermediate_cleat_length = run_dimension - edge_cleat_allowance_on_run_dim
        if intermediate_cleat_length <= config.FLOAT_TOLERANCE:
            log.warning(f"    Cannot add intermediate {orientation} cleat, calculated length {intermediate_cleat_length:.2f} too small. (RunDim={run_dimension:.2f}, Allowance={edge_cleat_allowance_on_run_dim:.2f})")
            return

        # Add ONE central intermediate cleat. Its position is the midpoint of the two outermost cleats.
        # Which is also the center of the panel (0.0) if outermost cleats are symmetric.
        # For non-symmetric outermost (e.g. one edge, one splice), it's their midpoint.
        intermediate_cleat_pos_rel_panel_center = (outermost_cleat1_pos + outermost_cleat2_pos) / 2.0

        new_cleat = {
            "type": f"intermediate_{orientation}",
            "orientation": orientation,
            "length": round(intermediate_cleat_length, 4),
            "thickness": cleat_thickness,
            "width": cleat_actual_width, # This is the lumber width (e.g. 3.5")
            pos_axis: round(intermediate_cleat_pos_rel_panel_center, 4),
            # The other axis position (center of the cleat along its length) is 0 relative to panel center
            "position_y" if orientation == "vertical" else "position_x": 0.0
        }

        # Check if an intermediate or splice cleat is already very close to this position
        already_exists_at_pos = any(
            (c.get("type", "").startswith("intermediate") or c.get("type", "").startswith("splice")) and
            c.get("orientation") == orientation and
            math.isclose(c.get(pos_axis, float('nan')), new_cleat[pos_axis], abs_tol=cleat_actual_width / 2.0) # Check within half cleat width
            for c in cleats_list
        )

        if not already_exists_at_pos:
            cleats_list.append(new_cleat)
            log.debug(f"    Added ONE intermediate {orientation} cleat at rel_pos {pos_axis}={intermediate_cleat_pos_rel_panel_center:.2f}, Length={intermediate_cleat_length:.2f}")
        else:
            log.debug(f"    Skipping intermediate {orientation} cleat near {pos_axis}={intermediate_cleat_pos_rel_panel_center:.2f} due to existing cleat.")
    else:
        log.debug(f"  Span {centerline_span_available_for_intermediate:.2f} not > threshold {INTERMEDIATE_CLEAT_ADD_THRESHOLD:.2f}. No central intermediate {orientation} cleat added.")


def _calculate_single_panel_layout(
    panel_width: float, panel_height: float, plywood_thickness: float,
    cleat_thickness: float, cleat_actual_width: float, panel_type: str # panel_type is 'side' or 'back'
) -> Dict[str, Any]:
    """Helper function to calculate layout for a single wall panel, including splicing and simplified intermediate cleats."""
    panel_layout = {
        "panel_width": round(panel_width, 4),
        "panel_height": round(panel_height, 4),
        "plywood_thickness": round(plywood_thickness, 4),
        "cleats": [],
        "plywood_pieces": [],
        "cleat_spec": {"thickness": cleat_thickness, "width": cleat_actual_width} # Store actual width
    }
    cleats = panel_layout["cleats"] # Direct reference for modification
    plywood_pieces = panel_layout["plywood_pieces"]

    log.debug(f"Calculating {panel_type} panel layout: W={panel_width:.2f}, H={panel_height:.2f}, PlywoodT={plywood_thickness:.2f} CleatSpec={cleat_thickness:.2f}x{cleat_actual_width:.2f}")

    # Determine Plywood Pieces (coordinates relative to 0,0 of the panel)
    # Standard plywood sheet dimensions from config
    std_ply_w = config.PLYWOOD_STD_WIDTH
    std_ply_h = config.PLYWOOD_STD_HEIGHT

    # How many full standard sheets fit horizontally and vertically
    num_std_w = math.floor(panel_width / std_ply_w) if panel_width > std_ply_w + config.FLOAT_TOLERANCE else 0
    num_std_h = math.floor(panel_height / std_ply_h) if panel_height > std_ply_h + config.FLOAT_TOLERANCE else 0

    # Remaining dimensions
    rem_w = panel_width - num_std_w * std_ply_w
    rem_h = panel_height - num_std_h * std_ply_h

    current_y = 0.0
    for i_h in range(int(num_std_h) + (1 if rem_h > config.FLOAT_TOLERANCE else 0) ):
        h = std_ply_h if i_h < num_std_h else rem_h
        if h <= config.FLOAT_TOLERANCE: continue
        current_x = 0.0
        for i_w in range(int(num_std_w) + (1 if rem_w > config.FLOAT_TOLERANCE else 0) ):
            w = std_ply_w if i_w < num_std_w else rem_w
            if w <= config.FLOAT_TOLERANCE: continue
            plywood_pieces.append({"x0": round(current_x,4), "y0": round(current_y,4), "x1": round(current_x + w,4), "y1": round(current_y + h,4)})
            current_x += w
        current_y += h
    
    if not plywood_pieces: # Should always have at least one piece
         plywood_pieces.append({"x0": 0, "y0": 0, "x1": panel_width, "y1": panel_height})


    # Edge & Splice Cleats (positions are relative to panel center)
    # Panel center coordinates (used for converting relative positions to absolute later if needed by viz)
    center_x_panel = panel_width / 2.0
    center_y_panel = panel_height / 2.0

    vertical_cleat_center_positions_relative = [] # Store X-positions (relative to panel center)
    horizontal_cleat_center_positions_relative = [] # Store Y-positions (relative to panel center)

    # Edge Cleats: Configuration per spec (e.g. Fig 7-4 in 0251-70054)
    # Side Panel: Horizontal edge cleats run full panel_width. Vertical edge cleats run between them.
    # Back Panel: Vertical edge cleats run full panel_height. Horizontal edge cleats run between them.

    if panel_type == 'side':
        # Horizontal edge cleats (top & bottom)
        h_cleat_len = panel_width
        pos_y_bottom = -center_y_panel + cleat_actual_width / 2.0
        pos_y_top = center_y_panel - cleat_actual_width / 2.0
        cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": h_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": pos_y_bottom})
        cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": h_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": pos_y_top})
        horizontal_cleat_center_positions_relative.extend([pos_y_bottom, pos_y_top])

        # Vertical edge cleats (left & right), length adjusted for horizontal cleats
        v_cleat_len = panel_height - 2 * cleat_actual_width # Runs between horizontal edge cleats
        if v_cleat_len > config.FLOAT_TOLERANCE:
            pos_x_left = -center_x_panel + cleat_actual_width / 2.0
            pos_x_right = center_x_panel - cleat_actual_width / 2.0
            cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": v_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": pos_x_left, "position_y": 0})
            cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": v_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": pos_x_right, "position_y": 0})
            vertical_cleat_center_positions_relative.extend([pos_x_left, pos_x_right])

    elif panel_type == 'back': # Changed from 'end'
        # Vertical edge cleats (left & right)
        v_cleat_len = panel_height
        pos_x_left = -center_x_panel + cleat_actual_width / 2.0
        pos_x_right = center_x_panel - cleat_actual_width / 2.0
        cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": v_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": pos_x_left, "position_y": 0})
        cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": v_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": pos_x_right, "position_y": 0})
        vertical_cleat_center_positions_relative.extend([pos_x_left, pos_x_right])

        # Horizontal edge cleats (top & bottom), length adjusted for vertical cleats
        h_cleat_len = panel_width - 2 * cleat_actual_width # Runs between vertical edge cleats
        if h_cleat_len > config.FLOAT_TOLERANCE:
            pos_y_bottom = -center_y_panel + cleat_actual_width / 2.0
            pos_y_top = center_y_panel - cleat_actual_width / 2.0
            cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": h_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": pos_y_bottom})
            cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": h_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": pos_y_top})
            horizontal_cleat_center_positions_relative.extend([pos_y_bottom, pos_y_top])

    # Splice Cleats
    # Vertical splice cleats (if panel_width > std_ply_w)
    if panel_width > std_ply_w + config.FLOAT_TOLERANCE:
        num_vertical_splices = int(num_std_w) # Splice after each standard sheet width
        for i in range(1, num_vertical_splices + 1):
            splice_cleat_x_abs = i * std_ply_w
            splice_cleat_x_rel = splice_cleat_x_abs - center_x_panel # Position of splice line relative to panel center
            
            # Length of vertical splice cleat: full panel height, or adjusted if it meets horiz edge cleats
            len_adjust = 0
            if panel_type == 'side': len_adjust = 2 * cleat_actual_width # for side panels, vertical cleats are shorter
            splice_cleat_len = panel_height - len_adjust

            if splice_cleat_len > config.FLOAT_TOLERANCE:
                cleats.append({"type": "splice_vertical", "orientation": "vertical", "length": splice_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": splice_cleat_x_rel, "position_y": 0})
                vertical_cleat_center_positions_relative.append(splice_cleat_x_rel)
                log.debug(f"Added vertical splice cleat at x_rel={splice_cleat_x_rel:.2f}")

    # Horizontal splice cleats (if panel_height > std_ply_h)
    if panel_height > std_ply_h + config.FLOAT_TOLERANCE:
        num_horizontal_splices = int(num_std_h)
        for i in range(1, num_horizontal_splices + 1):
            splice_cleat_y_abs = i * std_ply_h
            splice_cleat_y_rel = splice_cleat_y_abs - center_y_panel # Position of splice line relative to panel center

            len_adjust = 0
            if panel_type == 'back': len_adjust = 2 * cleat_actual_width # for back panels, horizontal cleats are shorter
            splice_cleat_len = panel_width - len_adjust
            
            # Horizontal splice cleats might be split if they cross a vertical splice.
            # For simplicity, assume full length unless very complex splicing is needed.
            # The current _calculate_single_panel_layout's plywood logic is simpler.
            # We'll add one continuous splice cleat here.
            if splice_cleat_len > config.FLOAT_TOLERANCE:
                cleats.append({"type": "splice_horizontal", "orientation": "horizontal", "length": splice_cleat_len, "thickness": cleat_thickness, "width": cleat_actual_width, "position_x": 0, "position_y": splice_cleat_y_rel})
                horizontal_cleat_center_positions_relative.append(splice_cleat_y_rel)
                log.debug(f"Added horizontal splice cleat at y_rel={splice_cleat_y_rel:.2f}")


    # Add Intermediate Cleats (Simplified - max 1 per large span, per orientation)
    # Vertical intermediate cleats (based on panel_width)
    allowance_v = 2 * cleat_actual_width if panel_type == 'side' else 0
    _add_intermediate_cleats_simplified(cleats, panel_width, panel_height, cleat_thickness, cleat_actual_width, 'vertical', sorted(list(set(vertical_cleat_center_positions_relative))), allowance_v)

    # Horizontal intermediate cleats (based on panel_height)
    allowance_h = 2 * cleat_actual_width if panel_type == 'back' else 0
    _add_intermediate_cleats_simplified(cleats, panel_height, panel_width, cleat_thickness, cleat_actual_width, 'horizontal', sorted(list(set(horizontal_cleat_center_positions_relative))), allowance_h)

    return panel_layout


def calculate_wall_panels(
    crate_overall_width: float, crate_overall_length: float, panel_height: float, panel_plywood_thickness: float,
    wall_cleat_actual_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS, # Use actual dimensions
    wall_cleat_actual_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH     # Use actual dimensions
) -> Dict[str, Any]:
    """Calculates wall panels using Python logic including splicing and simplified intermediate cleat placement."""
    result = {
        "status": "INIT", "message": "Wall panel calculation not started.",
        "side_panels": [], "back_panels": [], # Changed from end_panels
        "panel_height_used": 0.0,
        "panel_plywood_thickness_used": 0.0,
        "wall_cleat_spec": {"thickness": wall_cleat_actual_thickness, "width": wall_cleat_actual_width}
    }
    log.info(f"Starting wall panel calculation: CrateW={crate_overall_width:.2f}, CrateL={crate_overall_length:.2f}, PanelH={panel_height:.2f}, PanelT={panel_plywood_thickness:.2f}, CleatActualTxW={wall_cleat_actual_thickness:.2f}x{wall_cleat_actual_width:.2f}")

    if not (crate_overall_width > config.FLOAT_TOLERANCE and \
            crate_overall_length > config.FLOAT_TOLERANCE and \
            panel_height > config.FLOAT_TOLERANCE):
        result["status"] = "ERROR"; result["message"] = "Crate dimensions (W, L) and panel height must be positive."
        log.error(result["message"]); return result

    plywood_thickness_to_use = panel_plywood_thickness
    if panel_plywood_thickness < config.WALL_PLYWOOD_THICKNESS_MIN - config.FLOAT_TOLERANCE:
        log.warning(f"Input panel plywood thickness {panel_plywood_thickness:.3f} < min {config.WALL_PLYWOOD_THICKNESS_MIN:.3f}. Using default {config.DEFAULT_WALL_PLYWOOD_THICKNESS:.3f}.")
        plywood_thickness_to_use = config.DEFAULT_WALL_PLYWOOD_THICKNESS
    
    if not (wall_cleat_actual_thickness > config.FLOAT_TOLERANCE and \
            wall_cleat_actual_width > config.FLOAT_TOLERANCE):
        result["status"] = "ERROR"; result["message"] = "Wall cleat dimensions (thickness, width) must be positive."
        log.error(result["message"]); return result

    result["panel_height_used"] = round(panel_height, 4)
    result["panel_plywood_thickness_used"] = round(plywood_thickness_to_use, 4)

    log.debug("Calculating side panels...")
    side_panel_layout = _calculate_single_panel_layout(
        panel_width=crate_overall_length, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
        cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='side'
    )
    result["side_panels"] = [side_panel_layout, side_panel_layout] # Assuming two identical side panels

    log.debug("Calculating back panels...") # Changed from end
    back_panel_layout = _calculate_single_panel_layout( # Changed from end
        panel_width=crate_overall_width, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
        cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='back' # Changed from end
    )
    result["back_panels"] = [back_panel_layout, back_panel_layout] # Changed from end_panels, assuming two identical

    total_cleats_side = len(side_panel_layout.get("cleats", []))
    total_cleats_back = len(back_panel_layout.get("cleats", [])) # Changed from end

    if total_cleats_side > 0 and total_cleats_back > 0 : # Ensure both panel types have some cleats
        result["status"] = "OK"
        result["message"] = "Wall panel layouts calculated successfully (simplified intermediate cleats)."
    elif total_cleats_side == 0 and total_cleats_back == 0:
         result["status"] = "ERROR"; result["message"] = "Failed to calculate any wall panel cleats for both side and back panels."
    else: # One panel type might have failed
        result["status"] = "WARNING"
        result["message"] = "Wall panel layouts calculated, but one panel type (side or back) may have no cleats."
        if total_cleats_side == 0: result["message"] += " Side panels have no cleats."
        if total_cleats_back == 0: result["message"] += " Back panels have no cleats."


    log.info(f"Wall Panel Calculation Complete. Final Status: {result['status']}")
    return result