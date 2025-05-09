# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and back wall panels.
Includes splicing logic and intermediate cleat placement based on max spacing.
Version updated for v0.6.9 changes.
MODIFIED: Attempting more granular cleat segmentation. Needs THOROUGH TESTING.
"""

import logging
import math
from typing import Dict, List, Any, Tuple, Set

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
MAX_CLEAT_SPACING = getattr(config, 'MAX_INTERMEDIATE_CLEAT_SPACING', config.INTERMEDIATE_CLEAT_THRESHOLD)
FLOAT_TOL = config.FLOAT_TOLERANCE

# --- Internal Helper for Segmentation (New) ---
def _get_cleat_segments(
    cleat_orientation: str, # "horizontal" or "vertical"
    cleat_fixed_coord_rel: float, # Relative Y for horizontal, Relative X for vertical
    panel_dim_along_cleat: float, # panel_width for horizontal, panel_height for vertical
    panel_center_along_cleat: float, # center_x_panel for horizontal, center_y_panel for vertical
    obstructing_cleat_lines_rel: List[float], # List of RELATIVE centerlines of perpendicular cleats
    obstructing_cleat_width: float,
    cleat_thickness_self: float, # Thickness of the cleat being segmented
    cleat_width_self: float # Width of the cleat being segmented (its dimension perpendicular to its length)
) -> List[Dict[str, Any]]:
    """
    Calculates segments for a single cleat line, considering perpendicular obstructions.
    Returns a list of dictionaries, each representing a cleat segment.
    """
    segments = []
    # Define the span of this cleat line (relative to panel center)
    span_start_rel = -panel_dim_along_cleat / 2.0
    span_end_rel = panel_dim_along_cleat / 2.0

    # Create cut points: panel edges and edges of obstructing cleats
    # All points are relative to the panel center ALONG THE CLEAT'S LENGTH
    cut_points_rel = {span_start_rel, span_end_rel}
    for obs_center_rel in obstructing_cleat_lines_rel:
        cut_points_rel.add(obs_center_rel - obstructing_cleat_width / 2.0)
        cut_points_rel.add(obs_center_rel + obstructing_cleat_width / 2.0)
    
    sorted_cuts_rel = sorted(list(pt for pt in cut_points_rel if span_start_rel - FLOAT_TOL <= pt <= span_end_rel + FLOAT_TOL))
    
    # Deduplicate points that are too close
    unique_sorted_cuts_rel = []
    if sorted_cuts_rel:
        unique_sorted_cuts_rel.append(sorted_cuts_rel[0])
        for i in range(1, len(sorted_cuts_rel)):
            if abs(sorted_cuts_rel[i] - unique_sorted_cuts_rel[-1]) > FLOAT_TOL:
                unique_sorted_cuts_rel.append(sorted_cuts_rel[i])

    for i in range(len(unique_sorted_cuts_rel) - 1):
        seg_start_rel = unique_sorted_cuts_rel[i]
        seg_end_rel = unique_sorted_cuts_rel[i+1]
        seg_len = seg_end_rel - seg_start_rel

        if seg_len > FLOAT_TOL:
            seg_mid_point_rel = (seg_start_rel + seg_end_rel) / 2.0
            
            # Check if this segment's midpoint falls INSIDE an obstructing cleat
            is_gap_segment = False
            for obs_center_rel in obstructing_cleat_lines_rel:
                if (obs_center_rel - obstructing_cleat_width / 2.0 - FLOAT_TOL <= seg_mid_point_rel <=
                    obs_center_rel + obstructing_cleat_width / 2.0 + FLOAT_TOL):
                    is_gap_segment = True
                    break
            
            if not is_gap_segment:
                segment_data = {
                    "length": round(seg_len, 4),
                    "thickness": cleat_thickness_self,
                    "width": cleat_width_self 
                }
                if cleat_orientation == "horizontal":
                    segment_data["position_x"] = round(seg_mid_point_rel, 4) # Center X of segment
                    segment_data["position_y"] = round(cleat_fixed_coord_rel, 4) # Fixed Y of H cleat
                else: # vertical
                    segment_data["position_x"] = round(cleat_fixed_coord_rel, 4) # Fixed X of V cleat
                    segment_data["position_y"] = round(seg_mid_point_rel, 4) # Center Y of segment
                segments.append(segment_data)
    return segments

def _calculate_intermediate_cleat_positions(
    span_dimension: float, 
    cleat_actual_width: float, 
    max_spacing: float, 
    existing_cleat_centers_relative: List[float] 
) -> List[float]:
    # (Existing _calculate_intermediate_cleat_positions function - keep as is for now)
    # ... (function content from the original file) ...
    # (Ensure this function remains or copy its content here)
    # For brevity, assuming it's present. If not, it needs to be copied from your original file.
    # It's used to find centerlines, then these centerlines will be segmented.
    intermediate_positions = []
    if not existing_cleat_centers_relative or len(existing_cleat_centers_relative) < 2:
        log.debug("Not enough existing cleats to place intermediates between.")
        return intermediate_positions

    outermost_span_centers = abs(existing_cleat_centers_relative[-1] - existing_cleat_centers_relative[0])
    clear_span_for_intermediates = outermost_span_centers - cleat_actual_width

    log.debug(f"Calculating intermediates: Outermost span={outermost_span_centers:.2f}, CleatW={cleat_actual_width:.2f}, Clear span={clear_span_for_intermediates:.2f}, MaxSpace={max_spacing:.2f}")

    if clear_span_for_intermediates <= max_spacing + FLOAT_TOL:
        log.debug("Clear span is less than or equal to max spacing. No intermediate cleats needed.")
        return intermediate_positions

    num_spaces = math.ceil(clear_span_for_intermediates / max_spacing)
    num_intermediate_cleats = num_spaces - 1

    if num_intermediate_cleats < 1:
        log.debug(f"Calculated {num_spaces} spaces, needing {num_intermediate_cleats} cleats. None required.")
        return intermediate_positions
        
    total_cleats_in_span = 2 + num_intermediate_cleats
    actual_spacing = outermost_span_centers / (total_cleats_in_span - 1)
    
    log.debug(f"Need {num_intermediate_cleats} intermediate cleats with actual spacing {actual_spacing:.2f}")

    first_outermost_pos = existing_cleat_centers_relative[0]
    for i in range(1, num_intermediate_cleats + 1):
        pos = first_outermost_pos + i * actual_spacing
        intermediate_positions.append(round(pos, 4))
        
    log.debug(f"Calculated intermediate cleat relative positions: {intermediate_positions}")
    return intermediate_positions


def _calculate_single_panel_layout(
    panel_width: float, panel_height: float, plywood_thickness: float,
    cleat_thickness: float, cleat_actual_width: float, panel_type: str 
) -> Dict[str, Any]:
    """
    Calculates layout for a single wall panel.
    MODIFIED: Attempts granular cleat segmentation. NEEDS THOROUGH TESTING AND REFINEMENT.
    """
    panel_layout = {
        "panel_width": round(panel_width, 4),
        "panel_height": round(panel_height, 4),
        "plywood_thickness": round(plywood_thickness, 4),
        "cleats": [], # Will store segmented cleat data
        "plywood_pieces": [],
        "cleat_spec": {"thickness": cleat_thickness, "width": cleat_actual_width}
    }
    cleats_output_list = panel_layout["cleats"] 
    plywood_pieces = panel_layout["plywood_pieces"]

    log.debug(f"Calculating {panel_type} panel: W={panel_width:.2f}, H={panel_height:.2f}, PlywoodT={plywood_thickness:.2f} CleatSpec={cleat_thickness:.2f}x{cleat_actual_width:.2f}")

    # 1. Determine Plywood Pieces (coordinates relative to panel 0,0 bottom-left)
    # (Existing plywood piece logic - assumed correct and remains the same)
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
    else: 
        plywood_pieces.append({"x0": 0, "y0": 0, "x1": PLYWOOD_STD_WIDTH, "y1": PLYWOOD_STD_HEIGHT}) 
        plywood_pieces.append({"x0": PLYWOOD_STD_WIDTH, "y0": 0, "x1": panel_width, "y1": PLYWOOD_STD_HEIGHT}) 
        plywood_pieces.append({"x0": 0, "y0": PLYWOOD_STD_HEIGHT, "x1": PLYWOOD_STD_WIDTH, "y1": panel_height}) 
        plywood_pieces.append({"x0": PLYWOOD_STD_WIDTH, "y0": PLYWOOD_STD_HEIGHT, "x1": panel_width, "y1": panel_height})
    log.debug(f"Calculated {len(plywood_pieces)} plywood pieces.")

    # 2. Define Primary Obstruction Cleat Centerlines (Relative to Panel Center)
    center_x_panel = panel_width / 2.0
    center_y_panel = panel_height / 2.0

    # These lists will store the RELATIVE centerlines of primary cleats
    # that can obstruct other cleats running perpendicularly.
    vertical_primary_cleat_centers_x_rel: List[float] = []
    horizontal_primary_cleat_centers_y_rel: List[float] = []

    # Add edge cleat centerlines to obstruction lists
    # Vertical Edge Cleats (Left/Right)
    v_edge_left_x = -center_x_panel + cleat_actual_width / 2.0
    v_edge_right_x = center_x_panel - cleat_actual_width / 2.0
    if panel_width > cleat_actual_width - FLOAT_TOL: # Only if panel is wide enough for them
        vertical_primary_cleat_centers_x_rel.extend([v_edge_left_x, v_edge_right_x])

    # Horizontal Edge Cleats (Top/Bottom)
    h_edge_bottom_y = -center_y_panel + cleat_actual_width / 2.0
    h_edge_top_y = center_y_panel - cleat_actual_width / 2.0
    if panel_height > cleat_actual_width - FLOAT_TOL: # Only if panel is tall enough
        horizontal_primary_cleat_centers_y_rel.extend([h_edge_bottom_y, h_edge_top_y])
    
    # Add splice cleat centerlines to obstruction lists (if they exist)
    if needs_vertical_splice:
        v_splice_x = PLYWOOD_STD_WIDTH - center_x_panel
        vertical_primary_cleat_centers_x_rel.append(v_splice_x)
    if needs_horizontal_splice:
        h_splice_y = PLYWOOD_STD_HEIGHT - center_y_panel
        horizontal_primary_cleat_centers_y_rel.append(h_splice_y)

    vertical_primary_cleat_centers_x_rel = sorted(list(set(vertical_primary_cleat_centers_x_rel)))
    horizontal_primary_cleat_centers_y_rel = sorted(list(set(horizontal_primary_cleat_centers_y_rel)))
    
    log.debug(f"Vertical primary obstruction X centers (rel): {vertical_primary_cleat_centers_x_rel}")
    log.debug(f"Horizontal primary obstruction Y centers (rel): {horizontal_primary_cleat_centers_y_rel}")

    # 3. Generate Segmented Cleats
    # --- Horizontal Edge Cleats (Top/Bottom) ---
    if panel_height > cleat_actual_width - FLOAT_TOL: # If panel is tall enough for H edges
        for y_rel in [h_edge_bottom_y, h_edge_top_y]:
            segments = _get_cleat_segments(
                cleat_orientation="horizontal", cleat_fixed_coord_rel=y_rel,
                panel_dim_along_cleat=panel_width, panel_center_along_cleat=center_x_panel,
                obstructing_cleat_lines_rel=vertical_primary_cleat_centers_x_rel,
                obstructing_cleat_width=cleat_actual_width,
                cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
            )
            for seg in segments:
                cleats_output_list.append({**seg, "type": "edge_horizontal_segment", "orientation": "horizontal"})
            log.debug(f"Added {len(segments)} segments for H edge cleat at Y_rel={y_rel:.2f}")

    # --- Vertical Edge Cleats (Left/Right) ---
    if panel_width > cleat_actual_width - FLOAT_TOL: # If panel is wide enough for V edges
        for x_rel in [v_edge_left_x, v_edge_right_x]:
            segments = _get_cleat_segments(
                cleat_orientation="vertical", cleat_fixed_coord_rel=x_rel,
                panel_dim_along_cleat=panel_height, panel_center_along_cleat=center_y_panel,
                obstructing_cleat_lines_rel=horizontal_primary_cleat_centers_y_rel,
                obstructing_cleat_width=cleat_actual_width,
                cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
            )
            for seg in segments:
                cleats_output_list.append({**seg, "type": "edge_vertical_segment", "orientation": "vertical"})
            log.debug(f"Added {len(segments)} segments for V edge cleat at X_rel={x_rel:.2f}")
            
    # --- Horizontal Splice Cleat (if needed) ---
    if needs_horizontal_splice:
        h_splice_y_rel = PLYWOOD_STD_HEIGHT - center_y_panel
        segments = _get_cleat_segments(
            cleat_orientation="horizontal", cleat_fixed_coord_rel=h_splice_y_rel,
            panel_dim_along_cleat=panel_width, panel_center_along_cleat=center_x_panel,
            obstructing_cleat_lines_rel=vertical_primary_cleat_centers_x_rel,
            obstructing_cleat_width=cleat_actual_width,
            cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
        )
        for seg in segments:
            cleats_output_list.append({**seg, "type": "splice_horizontal_segment", "orientation": "horizontal"})
        log.debug(f"Added {len(segments)} segments for H splice cleat at Y_rel={h_splice_y_rel:.2f}")

    # --- Vertical Splice Cleat (if needed) ---
    if needs_vertical_splice:
        v_splice_x_rel = PLYWOOD_STD_WIDTH - center_x_panel
        segments = _get_cleat_segments(
            cleat_orientation="vertical", cleat_fixed_coord_rel=v_splice_x_rel,
            panel_dim_along_cleat=panel_height, panel_center_along_cleat=center_y_panel,
            obstructing_cleat_lines_rel=horizontal_primary_cleat_centers_y_rel,
            obstructing_cleat_width=cleat_actual_width,
            cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
        )
        for seg in segments:
            cleats_output_list.append({**seg, "type": "splice_vertical_segment", "orientation": "vertical"})
        log.debug(f"Added {len(segments)} segments for V splice cleat at X_rel={v_splice_x_rel:.2f}")

    # 4. Add Intermediate Cleats
    # IMPORTANT: This section needs careful review. Intermediate cleats also need to be segmented.
    # The existing _calculate_intermediate_cleat_positions provides centerlines.
    # These centerlines then need to be processed by _get_cleat_segments.
    
    # Vertical Intermediates (spaced across width)
    # Use primary cleat centerlines for determining intermediate positions.
    # The `vertical_primary_cleat_centers_x_rel` should contain the main edge/splice lines.
    if len(vertical_primary_cleat_centers_x_rel) >=2: # Need at least two primary lines to space between
        intermediate_v_cleat_centerlines_x_rel = _calculate_intermediate_cleat_positions(
            panel_width, cleat_actual_width, MAX_CLEAT_SPACING, vertical_primary_cleat_centers_x_rel
        )
        for int_v_x_rel in intermediate_v_cleat_centerlines_x_rel:
            segments = _get_cleat_segments(
                cleat_orientation="vertical", cleat_fixed_coord_rel=int_v_x_rel,
                panel_dim_along_cleat=panel_height, panel_center_along_cleat=center_y_panel,
                obstructing_cleat_lines_rel=horizontal_primary_cleat_centers_y_rel, # Obstructed by H primary cleats
                obstructing_cleat_width=cleat_actual_width,
                cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
            )
            for seg in segments:
                cleats_output_list.append({**seg, "type": "intermediate_vertical_segment", "orientation": "vertical"})
            log.debug(f"Added {len(segments)} segments for Intermediate V cleat at X_rel={int_v_x_rel:.2f}")
    else:
        log.debug("Skipping vertical intermediate cleats: Not enough primary vertical cleat lines to space between.")

    # Horizontal Intermediates (spaced across height)
    if len(horizontal_primary_cleat_centers_y_rel) >= 2:
        intermediate_h_cleat_centerlines_y_rel = _calculate_intermediate_cleat_positions(
            panel_height, cleat_actual_width, MAX_CLEAT_SPACING, horizontal_primary_cleat_centers_y_rel
        )
        for int_h_y_rel in intermediate_h_cleat_centerlines_y_rel:
            segments = _get_cleat_segments(
                cleat_orientation="horizontal", cleat_fixed_coord_rel=int_h_y_rel,
                panel_dim_along_cleat=panel_width, panel_center_along_cleat=center_x_panel,
                obstructing_cleat_lines_rel=vertical_primary_cleat_centers_x_rel, # Obstructed by V primary cleats
                obstructing_cleat_width=cleat_actual_width,
                cleat_thickness_self=cleat_thickness, cleat_width_self=cleat_actual_width
            )
            for seg in segments:
                cleats_output_list.append({**seg, "type": "intermediate_horizontal_segment", "orientation": "horizontal"})
            log.debug(f"Added {len(segments)} segments for Intermediate H cleat at Y_rel={int_h_y_rel:.2f}")
    else:
        log.debug("Skipping horizontal intermediate cleats: Not enough primary horizontal cleat lines to space between.")

    log.info(f"Final cleat segment count for {panel_type} panel: {len(cleats_output_list)}")
    # DISCLAIMER: The visualization and details table might need updates to correctly
    # interpret and display these segmented cleats. The definition of "cleat type"
    # in details tables also needs to reflect these segments.
    return panel_layout


def calculate_wall_panels(
    crate_overall_width: float, crate_overall_length: float, panel_height: float, panel_plywood_thickness: float,
    wall_cleat_actual_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS, 
    wall_cleat_actual_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH     
) -> Dict[str, Any]:
    """Calculates wall panels using updated logic including intermediate cleat spacing."""
    result = {
        "status": "INIT", "message": "Wall panel calculation not started.",
        "side_panels": [], "back_panels": [], 
        "panel_height_used": 0.0,
        "panel_plywood_thickness_used": 0.0,
        "wall_cleat_spec": {"thickness": wall_cleat_actual_thickness, "width": wall_cleat_actual_width}
    }
    log.info(f"Starting wall panel calculation: CrateW={crate_overall_width:.2f}, CrateL={crate_overall_length:.2f}, PanelH={panel_height:.2f}, PanelT={panel_plywood_thickness:.2f}, CleatActualTxW={wall_cleat_actual_thickness:.2f}x{wall_cleat_actual_width:.2f}")

    # --- Input Validation ---
    # (Existing validation logic - assumed correct and remains the same)
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
        # NOTE: The panel_type='side' or 'back' distinction was used in the original _calculate_single_panel_layout
        # to determine which edge cleats run full length. With the new segmentation logic, this specific
        # distinction inside _get_cleat_segments might be less critical if all cleats are built from segments
        # defined by the panel boundaries and perpendicular obstructions.
        # However, the overall panel dimensions (width vs length) are still key.
        side_panel_layout = _calculate_single_panel_layout(
            panel_width=crate_overall_length, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='side'
        )
        result["side_panels"] = [side_panel_layout, side_panel_layout] 

        log.debug("Calculating back panels...")
        back_panel_layout = _calculate_single_panel_layout( 
            panel_width=crate_overall_width, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width, panel_type='back'
        )
        result["back_panels"] = [back_panel_layout, back_panel_layout] 

        total_cleats_side = len(side_panel_layout.get("cleats", []))
        total_cleats_back = len(back_panel_layout.get("cleats", [])) 
        if total_cleats_side > 0 and total_cleats_back > 0 : 
            result["status"] = "OK"
            result["message"] = "Wall panel layouts calculated (segmented cleats)."
        elif total_cleats_side == 0 and total_cleats_back == 0 and (crate_overall_width > FLOAT_TOL or crate_overall_length > FLOAT_TOL):
             result["status"] = "WARNING"; result["message"] = "Wall panel calculation resulted in no cleats for both panel types. Dimensions might be too small for any cleats under new segmented logic."
        elif total_cleats_side == 0 and crate_overall_length > FLOAT_TOL :
            result["status"] = "WARNING"; result["message"] = "Side panels have no cleats (segments). Dimensions might be too small."
        elif total_cleats_back == 0 and crate_overall_width > FLOAT_TOL:
            result["status"] = "WARNING"; result["message"] = "Back panels have no cleats (segments). Dimensions might be too small."
        else: # Default to OK if some cleats are there or dimensions are zero.
            result["status"] = "OK"
            result["message"] = "Wall panel layouts calculated (segmented cleats). Check counts if panels are very small."


    except Exception as e:
        log.error(f"Error during wall panel calculation: {e}", exc_info=True)
        result["status"] = "CRITICAL ERROR"
        result["message"] = f"An unexpected error occurred during segmented wall panel calculation: {e}"

    log.info(f"Wall Panel Calculation (Segmented) Complete. Final Status: {result['status']}")
    return result