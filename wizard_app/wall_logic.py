# wizard_app/wall_logic.py
"""
Logic for calculating the crate's side and back wall panels.
Includes splicing logic, intermediate cleat placement, and decal/Klimp placement.
MODIFIED: Added Klimp placement logic for End Panels (Front/Back).
"""

import logging
import math
from typing import Dict, List, Any, Tuple, Set, Optional

try:
    from . import config
except ImportError:
    import config

log = logging.getLogger(__name__)

PLYWOOD_STD_WIDTH = config.PLYWOOD_STD_WIDTH
PLYWOOD_STD_HEIGHT = config.PLYWOOD_STD_HEIGHT
MAX_CLEAT_SPACING = getattr(config, 'MAX_INTERMEDIATE_CLEAT_SPACING', config.INTERMEDIATE_CLEAT_THRESHOLD)
FLOAT_TOL = config.FLOAT_TOLERANCE
DECAL_RULES = getattr(config, 'DECAL_RULES', {})
DEFAULT_DECAL_BACKGROUND_COLOR = getattr(config, 'DEFAULT_DECAL_BACKGROUND_COLOR', 'rgba(255,255,224,0.5)')
DEFAULT_DECAL_TEXT_COLOR = getattr(config, 'DEFAULT_DECAL_TEXT_COLOR', 'black')
DEFAULT_DECAL_FONT_SIZE = getattr(config, 'DEFAULT_DECAL_FONT_SIZE', 12)
DEFAULT_DECAL_BORDER_COLOR = getattr(config, 'DEFAULT_DECAL_BORDER_COLOR', 'grey')
DEFAULT_DECAL_BORDER_WIDTH = getattr(config, 'DEFAULT_DECAL_BORDER_WIDTH', 1)
# Assuming Klimp properties might be in config, or use defaults
KLIMP_SIZE_VIZ = getattr(config, 'KLIMP_SIZE_VIZ', 1.0) # Default visual size (e.g., diameter or width)
KLIMP_COUNT_PER_EDGE = getattr(config, 'KLIMP_COUNT_PER_EDGE', 3) # Default number of Klimps


def _get_cleat_segments(
    cleat_orientation: str, cleat_fixed_coord_rel: float, panel_dim_along_cleat: float,
    panel_center_along_cleat: float, obstructing_cleat_lines_rel: List[float],
    obstructing_cleat_width: float, cleat_thickness_self: float, cleat_width_self: float
) -> List[Dict[str, Any]]:
    segments = []
    span_start_rel = -panel_dim_along_cleat / 2.0
    span_end_rel = panel_dim_along_cleat / 2.0
    cut_points_rel = {span_start_rel, span_end_rel}
    for obs_center_rel in obstructing_cleat_lines_rel:
        cut_points_rel.add(obs_center_rel - obstructing_cleat_width / 2.0)
        cut_points_rel.add(obs_center_rel + obstructing_cleat_width / 2.0)
    sorted_cuts_rel = sorted(list(pt for pt in cut_points_rel if span_start_rel - FLOAT_TOL <= pt <= span_end_rel + FLOAT_TOL))
    unique_sorted_cuts_rel = []
    if sorted_cuts_rel:
        unique_sorted_cuts_rel.append(sorted_cuts_rel[0])
        for i in range(1, len(sorted_cuts_rel)):
            if abs(sorted_cuts_rel[i] - unique_sorted_cuts_rel[-1]) > FLOAT_TOL:
                unique_sorted_cuts_rel.append(sorted_cuts_rel[i])
    for i in range(len(unique_sorted_cuts_rel) - 1):
        seg_start_rel, seg_end_rel = unique_sorted_cuts_rel[i], unique_sorted_cuts_rel[i+1]
        seg_len = seg_end_rel - seg_start_rel
        if seg_len > FLOAT_TOL:
            seg_mid_point_rel = (seg_start_rel + seg_end_rel) / 2.0
            is_gap_segment = any(
                obs_center_rel - obstructing_cleat_width / 2.0 - FLOAT_TOL <= seg_mid_point_rel <=
                obs_center_rel + obstructing_cleat_width / 2.0 + FLOAT_TOL
                for obs_center_rel in obstructing_cleat_lines_rel
            )
            if not is_gap_segment:
                segment_data = {
                    "length": round(seg_len, 4), "thickness": cleat_thickness_self,
                    "width": cleat_width_self, "orientation": cleat_orientation
                }
                if cleat_orientation == "horizontal":
                    segment_data["position_x"], segment_data["position_y"] = round(seg_mid_point_rel, 4), round(cleat_fixed_coord_rel, 4)
                else:
                    segment_data["position_x"], segment_data["position_y"] = round(cleat_fixed_coord_rel, 4), round(seg_mid_point_rel, 4)
                segments.append(segment_data)
    return segments

def _calculate_intermediate_cleat_positions(
    span_dimension: float, cleat_actual_width: float, max_spacing: float,
    existing_cleat_centers_relative: List[float]
) -> List[float]:
    intermediate_positions = []
    if len(existing_cleat_centers_relative) < 2: return intermediate_positions
    sorted_existing_cleats = sorted(list(set(existing_cleat_centers_relative)))
    if len(sorted_existing_cleats) < 2: return intermediate_positions
    outermost_span_centers = abs(sorted_existing_cleats[-1] - sorted_existing_cleats[0])
    clear_span_for_intermediates = outermost_span_centers - cleat_actual_width
    if clear_span_for_intermediates <= max_spacing + FLOAT_TOL: return intermediate_positions
    num_spaces = math.ceil(clear_span_for_intermediates / max_spacing)
    num_intermediate_cleats = num_spaces - 1
    if num_intermediate_cleats < 1: return intermediate_positions
    total_cleats_in_section = 2 + num_intermediate_cleats
    actual_spacing_cc = outermost_span_centers / (total_cleats_in_section - 1)
    first_bounding_cleat_pos = sorted_existing_cleats[0]
    for i in range(1, num_intermediate_cleats + 1):
        intermediate_positions.append(round(first_bounding_cleat_pos + i * actual_spacing_cc, 4))
    return intermediate_positions

def _calculate_decal_on_panel(
    panel_width: float, panel_height: float, overall_crate_height: float,
    decal_rule: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    decal_props = {}
    rule_id = decal_rule.get("id", "unknown_decal")
    dims = decal_rule.get("dimensions")
    if not dims:
        small_thresh = decal_rule.get("dimensions_panel_h_small_thresh")
        if small_thresh and panel_height <= small_thresh: dims = decal_rule.get("dimensions_small")
        else: dims = decal_rule.get("dimensions_large", decal_rule.get("dimensions_small"))
    if not dims or not dims.get("width") or not dims.get("height"):
        log.warning(f"Decal rule '{rule_id}' missing valid dimensions for panel H {panel_height}. Skipping decal.")
        return None
    decal_w, decal_h = dims["width"], dims["height"]
    decal_props.update({
        "width": decal_w, "height": decal_h, "text_content": decal_rule.get("text_content", ""),
        "angle": decal_rule.get("angle", 0), "background_color": decal_rule.get("background_color", DEFAULT_DECAL_BACKGROUND_COLOR),
        "text_color": decal_rule.get("text_color", DEFAULT_DECAL_TEXT_COLOR), "font_size": decal_rule.get("font_size", DEFAULT_DECAL_FONT_SIZE),
        "border_color": decal_rule.get("border_color", DEFAULT_DECAL_BORDER_COLOR), "border_width": decal_rule.get("border_width", DEFAULT_DECAL_BORDER_WIDTH),
        "rule_id": rule_id
    })
    h_place = decal_rule.get("horizontal_placement", "center_panel_width")
    if h_place == "center_panel_width": decal_props["x_coord"] = (panel_width / 2.0) - (decal_w / 2.0)
    elif h_place == "upper_right_corner_panel_width": decal_props["x_coord"] = panel_width - decal_w
    else: decal_props["x_coord"] = (panel_width / 2.0) - (decal_w / 2.0)
    v_place = decal_rule.get("vertical_placement")
    v_rules_crate_h = decal_rule.get("vertical_placement_rules_crate_height")
    if v_rules_crate_h:
        panel_mid_y = panel_height / 2.0; cog_y_on_panel = panel_mid_y
        for rule in v_rules_crate_h:
            max_h, min_h, offset, method = rule.get("max_crate_h"), rule.get("min_crate_h"), rule.get("offset_from_crate_mid"), rule.get("method")
            passes = True
            if max_h is not None and overall_crate_height > max_h: passes = False
            if min_h is not None and overall_crate_height <= min_h: passes = False
            if passes:
                if method == "mid_panel_height_relative_to_crate_mid": cog_y_on_panel = panel_mid_y
                elif offset is not None: cog_y_on_panel = panel_mid_y + offset
                break
        decal_props["y_coord"] = cog_y_on_panel - (decal_h / 2.0)
    elif v_place == "center_upper_half_panel_height": decal_props["y_coord"] = (panel_height * 0.75) - (decal_h / 2.0)
    elif v_place == "upper_right_corner_panel_height": decal_props["y_coord"] = panel_height - decal_h
    elif v_place == "middle_panel_height": decal_props["y_coord"] = (panel_height / 2.0) - (decal_h / 2.0)
    else: decal_props["y_coord"] = (panel_height / 2.0) - (decal_h / 2.0)
    if (decal_props["x_coord"] < 0 or decal_props["x_coord"] + decal_w > panel_width + FLOAT_TOL or
        decal_props["y_coord"] < 0 or decal_props["y_coord"] + decal_h > panel_height + FLOAT_TOL):
        log.warning(f"Decal '{rule_id}' may exceed panel boundaries.")
    decal_props["x_coord"], decal_props["y_coord"] = round(decal_props["x_coord"],4), round(decal_props["y_coord"],4)
    return decal_props

def _calculate_single_panel_layout(
    panel_width: float, panel_height: float, plywood_thickness: float,
    cleat_thickness: float, cleat_actual_width: float, panel_type: str,
    overall_crate_height: float,
    apply_klimps_to_vertical_edges: bool = False # MODIFICATION: For Klimp placement
) -> Dict[str, Any]:
    panel_layout = {
        "panel_width": round(panel_width, 4), "panel_height": round(panel_height, 4),
        "plywood_thickness": round(plywood_thickness, 4), "cleats": [], "plywood_pieces": [],
        "cleat_spec": {"thickness": cleat_thickness, "width": cleat_actual_width}, 
        "decals": [],
        "klimps": [] # MODIFICATION: Initialize klimps list
    }
    # --- Plywood and Cleat Logic (condensed for brevity, assumed correct from previous) ---
    cleats_output_list = panel_layout["cleats"]; plywood_pieces = panel_layout["plywood_pieces"]
    needs_vertical_splice = panel_width > PLYWOOD_STD_WIDTH + FLOAT_TOL; needs_horizontal_splice = panel_height > PLYWOOD_STD_HEIGHT + FLOAT_TOL
    if not needs_vertical_splice and not needs_horizontal_splice: plywood_pieces.append({"x0":0,"y0":0,"x1":panel_width,"y1":panel_height})
    elif needs_vertical_splice and not needs_horizontal_splice: plywood_pieces.extend([{"x0":0,"y0":0,"x1":PLYWOOD_STD_WIDTH,"y1":panel_height},{"x0":PLYWOOD_STD_WIDTH,"y0":0,"x1":panel_width,"y1":panel_height}])
    elif not needs_vertical_splice and needs_horizontal_splice: plywood_pieces.extend([{"x0":0,"y0":0,"x1":panel_width,"y1":PLYWOOD_STD_HEIGHT},{"x0":0,"y0":PLYWOOD_STD_HEIGHT,"x1":panel_width,"y1":panel_height}])
    else: plywood_pieces.extend([{"x0":0,"y0":0,"x1":PLYWOOD_STD_WIDTH,"y1":PLYWOOD_STD_HEIGHT},{"x0":PLYWOOD_STD_WIDTH,"y0":0,"x1":panel_width,"y1":PLYWOOD_STD_HEIGHT},{"x0":0,"y0":PLYWOOD_STD_HEIGHT,"x1":PLYWOOD_STD_WIDTH,"y1":panel_height},{"x0":PLYWOOD_STD_WIDTH,"y0":PLYWOOD_STD_HEIGHT,"x1":panel_width,"y1":panel_height}])
    center_x_panel, center_y_panel = panel_width/2.0, panel_height/2.0
    v_pri_cleats_x_rel, h_pri_cleats_y_rel = [], []
    v_edge_l_x, v_edge_r_x = -center_x_panel+cleat_actual_width/2.0, center_x_panel-cleat_actual_width/2.0
    if panel_width > cleat_actual_width-FLOAT_TOL: v_pri_cleats_x_rel.extend([v_edge_l_x,v_edge_r_x])
    h_edge_b_y, h_edge_t_y = -center_y_panel+cleat_actual_width/2.0, center_y_panel-cleat_actual_width/2.0
    if panel_height > cleat_actual_width-FLOAT_TOL: h_pri_cleats_y_rel.extend([h_edge_b_y,h_edge_t_y])
    if needs_vertical_splice: v_pri_cleats_x_rel.append(PLYWOOD_STD_WIDTH-center_x_panel)
    if needs_horizontal_splice: h_pri_cleats_y_rel.append(PLYWOOD_STD_HEIGHT-center_y_panel)
    v_pri_cleats_x_rel, h_pri_cleats_y_rel = sorted(list(set(v_pri_cleats_x_rel))), sorted(list(set(h_pri_cleats_y_rel)))
    if panel_height > cleat_actual_width-FLOAT_TOL:
        for y_rel in [h_edge_b_y,h_edge_t_y]: [cleats_output_list.append({**seg,"type":"edge_horizontal_segment"}) for seg in _get_cleat_segments("horizontal",y_rel,panel_width,center_x_panel,v_pri_cleats_x_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    if panel_width > cleat_actual_width-FLOAT_TOL:
        for x_rel in [v_edge_l_x,v_edge_r_x]: [cleats_output_list.append({**seg,"type":"edge_vertical_segment"}) for seg in _get_cleat_segments("vertical",x_rel,panel_height,center_y_panel,h_pri_cleats_y_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    if needs_horizontal_splice: [cleats_output_list.append({**seg,"type":"splice_horizontal_segment"}) for seg in _get_cleat_segments("horizontal",PLYWOOD_STD_HEIGHT-center_y_panel,panel_width,center_x_panel,v_pri_cleats_x_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    if needs_vertical_splice: [cleats_output_list.append({**seg,"type":"splice_vertical_segment"}) for seg in _get_cleat_segments("vertical",PLYWOOD_STD_WIDTH-center_x_panel,panel_height,center_y_panel,h_pri_cleats_y_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    if len(v_pri_cleats_x_rel)>=2:
        for x_rel in _calculate_intermediate_cleat_positions(panel_width,cleat_actual_width,MAX_CLEAT_SPACING,v_pri_cleats_x_rel): [cleats_output_list.append({**seg,"type":"intermediate_vertical_segment"}) for seg in _get_cleat_segments("vertical",x_rel,panel_height,center_y_panel,h_pri_cleats_y_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    if len(h_pri_cleats_y_rel)>=2:
        for y_rel in _calculate_intermediate_cleat_positions(panel_height,cleat_actual_width,MAX_CLEAT_SPACING,h_pri_cleats_y_rel): [cleats_output_list.append({**seg,"type":"intermediate_horizontal_segment"}) for seg in _get_cleat_segments("horizontal",y_rel,panel_width,center_x_panel,v_pri_cleats_x_rel,cleat_actual_width,cleat_thickness,cleat_actual_width)]
    # --- [End of Plywood and Cleat Logic] ---

    current_panel_type_id = "side" if panel_type.lower() == "side" else "end"
    for rule_name, decal_rule in DECAL_RULES.items():
        if current_panel_type_id in decal_rule.get("apply_to_panels", []):
            calculated_decal = _calculate_decal_on_panel(panel_width, panel_height, overall_crate_height, decal_rule)
            if calculated_decal: panel_layout["decals"].append(calculated_decal)
    
    # MODIFICATION: Add Klimp positions if applicable for this panel type
    if apply_klimps_to_vertical_edges:
        num_klimps = KLIMP_COUNT_PER_EDGE 
        min_edge_dist = panel_height * 0.1 # Avoid placing too close to corners
        usable_klimp_height = panel_height - (2 * min_edge_dist)

        if usable_klimp_height > panel_height * 0.2 and num_klimps > 0: # Only if there's reasonable space
            spacing = usable_klimp_height / (num_klimps + 1) if num_klimps > 0 else usable_klimp_height # Distribute N klimps in N+1 spaces
            for i in range(1, num_klimps + 1):
                y_coord = min_edge_dist + (i * spacing)
                # Klimps on vertical edges (x=0 and x=panel_width) of this End Panel
                panel_layout["klimps"].append({"x_coord": 0, "y_coord": round(y_coord, 2), "size": KLIMP_SIZE_VIZ, "edge": "left"})
                panel_layout["klimps"].append({"x_coord": panel_width, "y_coord": round(y_coord, 2), "size": KLIMP_SIZE_VIZ, "edge": "right"})
            log.debug(f"Added {num_klimps*2} Klimp positions to {panel_type} panel edges.")
        else:
            log.debug(f"Not enough space or zero Klimps specified for {panel_type} panel edges.")


    log.info(f"Final cleat segment count for {panel_type} panel: {len(panel_layout['cleats'])}. Decals: {len(panel_layout['decals'])}. Klimps: {len(panel_layout['klimps'])}")
    return panel_layout

def calculate_wall_panels(
    crate_overall_width: float, crate_overall_length: float, panel_height: float,
    panel_plywood_thickness: float,
    overall_crate_actual_height: float, 
    wall_cleat_actual_thickness: float = config.DEFAULT_CLEAT_NOMINAL_THICKNESS,
    wall_cleat_actual_width: float = config.DEFAULT_CLEAT_NOMINAL_WIDTH
) -> Dict[str, Any]:
    result = {
        "status": "INIT", "message": "Wall panel calculation not started.",
        "side_panels": [], "back_panels": [],
        "panel_height_used": 0.0, "panel_plywood_thickness_used": 0.0,
        "wall_cleat_spec": {"thickness": wall_cleat_actual_thickness, "width": wall_cleat_actual_width}
    }
    if not (crate_overall_width > FLOAT_TOL and crate_overall_length > FLOAT_TOL and panel_height > FLOAT_TOL and overall_crate_actual_height > FLOAT_TOL):
        result["status"] = "ERROR"; result["message"] = "Crate dimensions (W, L, PanelH, OverallH) must be positive."
        log.error(result["message"]); return result
    plywood_thickness_to_use = panel_plywood_thickness
    if panel_plywood_thickness < config.WALL_PLYWOOD_THICKNESS_MIN - FLOAT_TOL:
        plywood_thickness_to_use = config.DEFAULT_WALL_PLYWOOD_THICKNESS
    if not (wall_cleat_actual_thickness > FLOAT_TOL and wall_cleat_actual_width > FLOAT_TOL):
        result["status"] = "ERROR"; result["message"] = "Wall cleat dimensions must be positive."
        log.error(result["message"]); return result
    result["panel_height_used"], result["panel_plywood_thickness_used"] = round(panel_height,4), round(plywood_thickness_to_use,4)
    try:
        # Side panels do not get Klimps directly applied in this model (they are fastened *to*)
        side_panel_layout = _calculate_single_panel_layout(
            panel_width=crate_overall_length, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width,
            panel_type='Side', overall_crate_height=overall_crate_actual_height,
            apply_klimps_to_vertical_edges=False # Side panels receive Klimps from End panels
        )
        result["side_panels"] = [side_panel_layout, side_panel_layout]

        # End panels (Front/Back) get Klimps on their vertical edges
        # The UI will differentiate "Front Assembly" and "Back Plate Assembly" but they use this same panel type
        end_panel_layout = _calculate_single_panel_layout(
            panel_width=crate_overall_width, panel_height=panel_height, plywood_thickness=plywood_thickness_to_use,
            cleat_thickness=wall_cleat_actual_thickness, cleat_actual_width=wall_cleat_actual_width,
            panel_type='End/Back', overall_crate_height=overall_crate_actual_height,
            apply_klimps_to_vertical_edges=True # Apply Klimps to vertical edges of End/Back panels
        )
        result["back_panels"] = [end_panel_layout, end_panel_layout] # Both end panels get Klimp data

        # ... (status messages remain similar - simplified here for brevity) ...
        if len(side_panel_layout["cleats"]) > 0 or len(end_panel_layout["cleats"]) > 0: result["status"] = "OK"; result["message"] = "Wall panel layouts calculated."
        else: result["status"] = "WARNING"; result["message"] = "No cleats generated for wall panels."

    except Exception as e:
        log.error(f"Error during wall panel calculation: {e}", exc_info=True)
        result["status"], result["message"] = "CRITICAL ERROR", f"Wall panel calculation error: {e}"
    log.info(f"Wall Panel Calc Complete. Status: {result['status']}")
    return result