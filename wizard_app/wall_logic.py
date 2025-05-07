# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and end wall panels.
Includes basic splicing logic and simplified intermediate cleat placement
(adds max one central intermediate per large span > 48").
Version 0.5.4 / Target State
"""

import logging
import math
from typing import Dict, List, Any

try:
    from . import config
except ImportError:
    import config # Fallback

log = logging.getLogger(__name__)

PLYWOOD_STD_WIDTH = 48.0
PLYWOOD_STD_HEIGHT = 96.0
# Threshold to add ONE central intermediate cleat
INTERMEDIATE_CLEAT_ADD_THRESHOLD = 48.0 # Add one if span > this

def _add_intermediate_cleats_simplified(
    cleats_list: List[Dict],
    span_dimension: float,
    run_dimension: float,
    cleat_thickness: float,
    cleat_width: float,
    orientation: str,
    existing_cleat_positions_rel: List[float],
    edge_cleat_allowance: float
):
    """Adds at most ONE central intermediate cleat within large spans."""
    log.debug(f"Adding simplified intermediate {orientation} cleats: SpanDim={span_dimension:.2f}, ExistingPos={existing_cleat_positions_rel}")
    if not existing_cleat_positions_rel or len(existing_cleat_positions_rel) < 2:
        log.warning(f"Cannot add intermediate {orientation} cleats without at least two existing edge/splice cleats.")
        return

    sorted_positions = sorted(existing_cleat_positions_rel)
    num_existing = len(sorted_positions)
    pos_axis = "position_x" if orientation == "vertical" else "position_y"
    len_axis = "length"

    # Check only the largest span (between outermost existing cleats) for adding ONE central cleat
    pos1 = sorted_positions[0]
    pos2 = sorted_positions[-1]
    span_between = abs(pos2 - pos1)
    centerline_span_available = span_between - cleat_width # Space between inner edges

    log.debug(f"  Outermost span between existing {orientation} cleats at {pos1:.2f} and {pos2:.2f}: Centerline Span = {centerline_span_available:.2f}")

    # Add ONE central intermediate cleat if the overall span is large enough
    if centerline_span_available > INTERMEDIATE_CLEAT_ADD_THRESHOLD + config.FLOAT_TOLERANCE:
        intermediate_cleat_length = run_dimension - edge_cleat_allowance
        if intermediate_cleat_length <= config.FLOAT_TOLERANCE:
            log.warning(f"    Cannot add intermediate {orientation} cleat, run_dimension {run_dimension:.2f} too small for edge allowance {edge_cleat_allowance:.2f}")
            return # Exit if cleat length is invalid

        # Calculate position relative to center of the *panel*
        # The center of the span between the outermost cleats is the panel center (0.0)
        cleat_pos_rel_panel_center = 0.0

        new_cleat = {
            "type": f"intermediate_{orientation}",
            "orientation": orientation,
            len_axis: round(intermediate_cleat_length, 4),
            "thickness": cleat_thickness,
            "width": cleat_width,
            pos_axis: round(cleat_pos_rel_panel_center, 4),
            # The other axis position is 0 (relative to center)
            "position_y" if orientation == "vertical" else "position_x": 0.0
        }
        # Check if an intermediate cleat is already very close to the center (e.g., a splice cleat)
        already_exists = any(
            c.get("type", "").startswith("intermediate") and
            c.get("orientation") == orientation and
            math.isclose(c.get(pos_axis, float('nan')), new_cleat[pos_axis], abs_tol=0.1)
            for c in cleats_list
        )
        # Also check if a splice cleat is near the center
        is_splice_near_center = any(
             c.get("type", "").startswith("splice") and
             c.get("orientation") == orientation and
             math.isclose(c.get(pos_axis, float('nan')), new_cleat[pos_axis], abs_tol=cleat_width) # Check within one cleat width
             for c in cleats_list
        )

        if not already_exists and not is_splice_near_center:
            cleats_list.append(new_cleat)
            log.debug(f"    Added ONE central intermediate {orientation} cleat at {pos_axis}={cleat_pos_rel_panel_center:.2f}")
        else:
             log.debug(f"    Skipping central intermediate {orientation} cleat near {pos_axis}={cleat_pos_rel_panel_center:.2f} due to existing cleat.")


def _calculate_single_panel_layout(
    panel_width: float, panel_height: float, plywood_thickness: float,
    cleat_thickness: float, cleat_width: float, panel_type: str
) -> Dict[str, Any]:
    """Helper function to calculate layout for a single wall panel, including splicing and simplified intermediate cleats."""
    panel_layout = {"panel_width": round(panel_width, 4), "panel_height": round(panel_height, 4), "plywood_thickness": round(plywood_thickness, 4), "cleats": [], "plywood_pieces": [], "cleat_spec": {"thickness": cleat_thickness, "width": cleat_width}}
    cleats = []; plywood_pieces = []
    log.debug(f"Calculating {panel_type} panel layout: W={panel_width:.2f}, H={panel_height:.2f}, Cleat={cleat_thickness:.2f}x{cleat_width:.2f}")
    splice_vertical = panel_width > config.PLYWOOD_STD_WIDTH + config.FLOAT_TOLERANCE; splice_horizontal = panel_height > config.PLYWOOD_STD_HEIGHT + config.FLOAT_TOLERANCE

    # Determine Plywood Pieces
    if splice_vertical and splice_horizontal: log.debug("Panel requires both vertical and horizontal splicing."); w1 = config.PLYWOOD_STD_WIDTH; w2 = panel_width - w1; h1 = config.PLYWOOD_STD_HEIGHT; h2 = panel_height - h1; plywood_pieces.append({"x0": 0, "y0": 0, "x1": w1, "y1": h1}); plywood_pieces.append({"x0": w1, "y0": 0, "x1": panel_width, "y1": h1}); plywood_pieces.append({"x0": 0, "y0": h1, "x1": w1, "y1": panel_height}); plywood_pieces.append({"x0": w1, "y0": h1, "x1": panel_width, "y1": panel_height})
    elif splice_vertical: log.debug("Panel requires vertical splicing."); w1 = config.PLYWOOD_STD_WIDTH; w2 = panel_width - w1; plywood_pieces.append({"x0": 0, "y0": 0, "x1": w1, "y1": panel_height}); plywood_pieces.append({"x0": w1, "y0": 0, "x1": panel_width, "y1": panel_height})
    elif splice_horizontal: log.debug("Panel requires horizontal splicing."); h1 = config.PLYWOOD_STD_HEIGHT; h2 = panel_height - h1; plywood_pieces.append({"x0": 0, "y0": 0, "x1": panel_width, "y1": h1}); plywood_pieces.append({"x0": 0, "y0": h1, "x1": panel_width, "y1": panel_height})
    else: log.debug("Panel fits within standard plywood sheet."); plywood_pieces.append({"x0": 0, "y0": 0, "x1": panel_width, "y1": panel_height})
    panel_layout["plywood_pieces"] = plywood_pieces

    # Edge & Splice Cleats
    center_x = panel_width / 2.0; center_y = panel_height / 2.0; vertical_cleat_positions_rel = []; horizontal_cleat_positions_rel = []
    if panel_type == 'side':
        h_bottom_pos = -center_y + cleat_width / 2; h_top_pos = center_y - cleat_width / 2; cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": panel_width, "thickness": cleat_thickness, "width": cleat_width, "position_x": 0, "position_y": h_bottom_pos}); cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": panel_width, "thickness": cleat_thickness, "width": cleat_width, "position_x": 0, "position_y": h_top_pos}); horizontal_cleat_positions_rel.extend([h_bottom_pos, h_top_pos])
        vertical_cleat_length = panel_height - 2 * cleat_width
        if vertical_cleat_length > config.FLOAT_TOLERANCE: v_left_pos = -center_x + cleat_width / 2; v_right_pos = center_x - cleat_width / 2; cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": vertical_cleat_length, "thickness": cleat_thickness, "width": cleat_width, "position_x": v_left_pos, "position_y": 0}); cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": vertical_cleat_length, "thickness": cleat_thickness, "width": cleat_width, "position_x": v_right_pos, "position_y": 0}); vertical_cleat_positions_rel.extend([v_left_pos, v_right_pos])
    elif panel_type == 'end':
        v_left_pos = -center_x + cleat_width / 2; v_right_pos = center_x - cleat_width / 2; cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": panel_height, "thickness": cleat_thickness, "width": cleat_width, "position_x": v_left_pos, "position_y": 0}); cleats.append({"type": "edge_vertical", "orientation": "vertical", "length": panel_height, "thickness": cleat_thickness, "width": cleat_width, "position_x": v_right_pos, "position_y": 0}); vertical_cleat_positions_rel.extend([v_left_pos, v_right_pos])
        horizontal_cleat_length = panel_width - 2 * cleat_width
        if horizontal_cleat_length > config.FLOAT_TOLERANCE: h_bottom_pos = -center_y + cleat_width / 2; h_top_pos = center_y - cleat_width / 2; cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": horizontal_cleat_length, "thickness": cleat_thickness, "width": cleat_width, "position_x": 0, "position_y": h_bottom_pos}); cleats.append({"type": "edge_horizontal", "orientation": "horizontal", "length": horizontal_cleat_length, "thickness": cleat_thickness, "width": cleat_width, "position_x": 0, "position_y": h_top_pos}); horizontal_cleat_positions_rel.extend([h_bottom_pos, h_top_pos])
    if splice_vertical:
        splice_cleat_x_rel = config.PLYWOOD_STD_WIDTH - center_x; splice_cleat_len = panel_height - (2 * cleat_width if panel_type == 'side' else 0)
        if splice_cleat_len > config.FLOAT_TOLERANCE: cleats.append({"type": "splice_vertical", "orientation": "vertical", "length": splice_cleat_len, "thickness": cleat_thickness, "width": cleat_width, "position_x": splice_cleat_x_rel, "position_y": 0}); vertical_cleat_positions_rel.append(splice_cleat_x_rel); log.debug(f"Added vertical splice cleat at x={splice_cleat_x_rel:.2f} (relative)")
    if splice_horizontal:
        splice_cleat_y_rel = config.PLYWOOD_STD_HEIGHT - center_y; splice_cleat_len = panel_width - (2 * cleat_width if panel_type == 'end' else 0)
        if splice_vertical: len1 = config.PLYWOOD_STD_WIDTH; len2 = panel_width - config.PLYWOOD_STD_WIDTH; x1 = (config.PLYWOOD_STD_WIDTH / 2.0) - center_x; x2 = config.PLYWOOD_STD_WIDTH + len2 / 2.0 - center_x;
        if len1 > config.FLOAT_TOLERANCE: cleats.append({"type": "splice_horizontal", "orientation": "horizontal", "length": len1, "thickness": cleat_thickness, "width": cleat_width, "position_x": x1, "position_y": splice_cleat_y_rel})
        if len2 > config.FLOAT_TOLERANCE: cleats.append({"type": "splice_horizontal", "orientation": "horizontal", "length": len2, "thickness": cleat_thickness, "width": cleat_width, "position_x": x2, "position_y": splice_cleat_y_rel})
        elif splice_cleat_len > config.FLOAT_TOLERANCE: cleats.append({"type": "splice_horizontal", "orientation": "horizontal", "length": splice_cleat_len, "thickness": cleat_thickness, "width": cleat_width, "position_x": 0, "position_y": splice_cleat_y_rel})
        horizontal_cleat_positions_rel.append(splice_cleat_y_rel); log.debug(f"Added horizontal splice cleat(s) at y={splice_cleat_y_rel:.2f} (relative)")

    # Add Intermediate Cleats (Simplified - max 1 per large span)
    _add_intermediate_cleats_simplified(cleats, panel_width, panel_height, cleat_thickness, cleat_width, 'vertical', vertical_cleat_positions_rel, (2 * cleat_width if panel_type == 'side' else 0))
    _add_intermediate_cleats_simplified(cleats, panel_height, panel_width, cleat_thickness, cleat_width, 'horizontal', horizontal_cleat_positions_rel, (2 * cleat_width if panel_type == 'end' else 0))

    panel_layout["cleats"] = cleats
    return panel_layout

# Main function remains the same
def calculate_wall_panels(
    crate_overall_width: float, crate_overall_length: float, panel_height: float, panel_thickness: float,
    wall_cleat_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS, wall_cleat_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH
) -> Dict[str, Any]:
    """Calculates wall panels using Python logic including splicing and simplified intermediate cleat placement."""
    result = {"status": "INIT", "message": "Wall panel calculation not started.", "side_panels": [], "end_panels": [], "panel_height_used": 0.0, "panel_plywood_thickness_used": 0.0, "wall_cleat_spec": {"thickness": wall_cleat_thickness, "width": wall_cleat_width}}
    log.info(f"Starting wall panel calculation: W={crate_overall_width:.2f}, L={crate_overall_length:.2f}, PanelH={panel_height:.2f}, PanelT={panel_thickness:.2f}, Cleat={wall_cleat_thickness:.2f}x{wall_cleat_width:.2f}")
    if crate_overall_width <= config.FLOAT_TOLERANCE or crate_overall_length <= config.FLOAT_TOLERANCE or panel_height <= config.FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Crate dimensions and panel height must be positive."; log.error(result["message"]); return result
    if panel_thickness < config.WALL_PLYWOOD_THICKNESS_MIN - config.FLOAT_TOLERANCE: log.warning(f"Input panel thickness {panel_thickness:.3f} < min {config.WALL_PLYWOOD_THICKNESS_MIN:.3f}. Using default {config.DEFAULT_WALL_PLYWOOD_THICKNESS:.3f}."); plywood_thickness_to_use = config.DEFAULT_WALL_PLYWOOD_THICKNESS
    else: plywood_thickness_to_use = panel_thickness
    if wall_cleat_thickness <= config.FLOAT_TOLERANCE or wall_cleat_width <= config.FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Wall cleat dimensions must be positive."; log.error(result["message"]); return result
    result["panel_height_used"] = round(panel_height, 4); result["panel_plywood_thickness_used"] = round(plywood_thickness_to_use, 4)
    log.debug("Calculating side panels..."); side_panel_layout = _calculate_single_panel_layout(panel_width=crate_overall_length, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use, cleat_thickness=wall_cleat_thickness, cleat_width=wall_cleat_width, panel_type='side'); result["side_panels"] = [side_panel_layout, side_panel_layout]
    log.debug("Calculating end panels..."); end_panel_layout = _calculate_single_panel_layout(panel_width=crate_overall_width, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use, cleat_thickness=wall_cleat_thickness, cleat_width=wall_cleat_width, panel_type='end'); result["end_panels"] = [end_panel_layout, end_panel_layout]
    total_cleats = len(side_panel_layout.get("cleats", [])) * 2 + len(end_panel_layout.get("cleats", [])) * 2
    if total_cleats > 0: result["status"] = "OK"; result["message"] = "Wall panel layouts calculated successfully (simplified intermediate cleats)."
    else: result["status"] = "ERROR"; result["message"] = "Failed to calculate any wall panel cleats."
    log.info(f"Wall Panel Calculation Complete. Final Status: {result['status']}")
    return result
