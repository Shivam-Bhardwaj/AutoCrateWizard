# wizard_app/floorboard_logic.py
"""
Logic for calculating floorboard layout for industrial shipping crates.
Version 0.4.14 - Simplified center fill logic: Use max one custom board as last board.
Imports constants from config.py
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

# Import from config
try:
    from . import config
except ImportError:
    import config # Fallback for testing

log = logging.getLogger(__name__)

# --- Helper Functions ---
def calculate_overall_skid_span(skid_layout_data: Dict[str, Any]) -> Optional[float]:
    """Calculates the overall span covered by skids, outer edge-to-outer edge."""
    skid_w = skid_layout_data.get('skid_width')
    skid_count = skid_layout_data.get('skid_count')
    positions = skid_layout_data.get('skid_positions')

    if skid_w is None or skid_count is None or positions is None:
        log.error("Missing skid_width, skid_count, or skid_positions for overall span calculation.")
        return None
    if not isinstance(skid_w, (int, float)) or not isinstance(skid_count, int) or not isinstance(positions, list):
        log.error("Invalid data types for skid span calculation inputs.")
        return None
    if len(positions) != skid_count:
        log.error(f"Position list length ({len(positions)}) doesn't match skid count ({skid_count}).")
        return None
    if skid_w <= config.FLOAT_TOLERANCE:
        log.error(f"Invalid skid width ({skid_w}) for span calculation.")
        return None

    if skid_count == 0: return 0.0
    elif skid_count == 1: return skid_w
    else:
        first_skid_outer_edge = positions[0] - (skid_w / 2.0)
        last_skid_outer_edge = positions[-1] + (skid_w / 2.0)
        span = abs(last_skid_outer_edge - first_skid_outer_edge)
        log.debug(f"Calculated overall skid span: {span:.3f}\" from {skid_count} skids.")
        return span

def get_available_standard_boards(available_nominal_sizes: List[str]) -> List[Tuple[str, float]]:
    """Filters and sorts available NOMINAL boards based on standard width rule."""
    standard_boards = []
    log.debug(f"Filtering available nominal sizes for standard boards: {available_nominal_sizes}")
    for nominal in available_nominal_sizes:
        width = config.ALL_STANDARD_FLOORBOARDS.get(nominal)
        if width is not None:
            if width >= config.MIN_STANDARD_BOARD_WIDTH - config.FLOAT_TOLERANCE and \
               width <= config.MAX_STANDARD_BOARD_WIDTH + config.FLOAT_TOLERANCE:
                standard_boards.append((nominal, width))
                log.debug(f"  - Added '{nominal}' ({width}\") to standard boards.")
            else:
                log.debug(f"  - '{nominal}' ({width}\") is defined but outside standard width range [{config.MIN_STANDARD_BOARD_WIDTH}, {config.MAX_STANDARD_BOARD_WIDTH}].")
        else:
            log.warning(f"Nominal size '{nominal}' not found in ALL_STANDARD_FLOORBOARDS definitions. Skipping.")
    standard_boards.sort(key=lambda x: x[1], reverse=True)
    log.debug(f"Available standard boards (Filtered & Sorted by width desc): {standard_boards}")
    return standard_boards

# --- Main Calculation Function ---
def calculate_floorboard_layout(
    skid_layout_data: Dict[str, Any],
    product_length: float,
    clearance_side: float,
    available_nominal_sizes: List[str],
    allow_custom_narrow_board: bool # Name implies narrow, but logic allows any width needed
) -> Dict[str, Any]:
    """
    Calculates floorboard layout symmetrically.
    New Logic: Places standard pairs, then adds at most ONE custom board
               if needed to reduce the center gap to <= MAX_CENTER_GAP.
    """
    result = {
        "status": "INIT", "message": "Floorboard calculation not started.",
        "target_span_along_length": 0.0, "floorboard_length_across_skids": 0.0,
        "floorboards": [], "board_counts": {}, "custom_board_width": None,
        "center_gap": 0.0, "narrow_board_used": False, # Renamed to custom_board_used internally
        "calculated_span_covered": 0.0, "total_board_width": 0.0,
        "placement_method": "Symmetrical with Single Custom Fill" # Updated method name
    }
    custom_board_used = False # Internal flag

    # --- Input Validation and Setup ---
    if skid_layout_data.get("status") != "OK":
        result["status"] = "ERROR"; result["message"] = "Skid layout status is not OK."; return result
    if product_length <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product length must be positive."; return result
    if clearance_side < -config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Clearance per side cannot be negative."; return result
    # Allow running even if no standard boards selected, if custom is allowed
    if not available_nominal_sizes and not allow_custom_narrow_board:
        result["status"] = "ERROR"; result["message"] = "No standard lumber selected AND custom board not allowed."; return result

    target_span_along_length = product_length + 2 * clearance_side
    if target_span_along_length <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Target span for floorboards is zero or negative."; return result
    result["target_span_along_length"] = target_span_along_length

    floorboard_length_across_skids = calculate_overall_skid_span(skid_layout_data)
    if floorboard_length_across_skids is None or floorboard_length_across_skids <= config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Could not determine valid floorboard length (overall skid span)."; return result
    result["floorboard_length_across_skids"] = floorboard_length_across_skids

    available_standard_boards = get_available_standard_boards(available_nominal_sizes)
    if not available_standard_boards and not allow_custom_narrow_board:
        # This case should already be caught, but double-check
        result["status"] = "ERROR"; result["message"] = "No valid standard lumber available and custom board not allowed."; return result
    elif not available_standard_boards:
        log.warning("No standard lumber selected/available. Layout depends solely on custom board possibility.")

    log.info(f"Starting floorboard calculation: Target Span={target_span_along_length:.3f}\", Board Length={floorboard_length_across_skids:.3f}\", Custom Allowed={allow_custom_narrow_board}")

    # --- Symmetrical Layout Calculation ---
    bottom_boards: List[Dict[str, Any]] = []; top_boards: List[Dict[str, Any]] = []
    current_pos_bottom: float = 0.0
    current_pos_top: float = target_span_along_length
    center_boards: List[Dict[str, Any]] = []
    final_gap: float = 0.0
    board_count = 0

    # 1. Place symmetrical pairs of STANDARD boards (widest first)
    while True:
        remaining_center_span_for_pairs = current_pos_top - current_pos_bottom
        if remaining_center_span_for_pairs < -config.FLOAT_TOLERANCE:
            log.error(f"Center span for pairs became negative ({remaining_center_span_for_pairs:.4f}).");
            result["status"] = "ERROR"; result["message"] = "Internal calculation error during symmetric pairing."; return result

        log.debug(f"Symmetric Pair Loop: Remaining Center Span = {remaining_center_span_for_pairs:.3f}")
        best_board_for_pair = None
        for nominal, width in available_standard_boards:
            if remaining_center_span_for_pairs >= (2 * width) - config.FLOAT_TOLERANCE:
                best_board_for_pair = {"nominal": nominal, "actual_width": width}; break

        if best_board_for_pair:
            width = best_board_for_pair["actual_width"]
            log.debug(f"Placing symmetric pair: {best_board_for_pair['nominal']} ({width:.3f}\")")
            bottom_boards.append({"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_bottom})
            current_pos_bottom += width
            board_count += 1

            top_boards.insert(0, {"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_top - width})
            current_pos_top -= width
            board_count += 1
        else:
            log.debug("No more standard board pairs fit symmetrically.")
            break
        if board_count > 200: # Safety break
            result["status"] = "ERROR"; result["message"] = "Exceeded board count limit (200)."; return result

    # 2. Handle the remaining center span
    center_span_remaining = current_pos_top - current_pos_bottom
    log.info(f"Center span remaining after symmetric standard boards: {center_span_remaining:.3f}\"")

    if center_span_remaining < -config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Center span became negative after symmetric placement."; return result

    final_gap = max(0.0, center_span_remaining) # Ensure non-negative gap initially
    custom_board_to_add = None

    # 3. Check if a custom board is needed and allowed
    if allow_custom_narrow_board and center_span_remaining > config.MAX_CENTER_GAP + config.FLOAT_TOLERANCE:
        log.info(f"Remaining span {center_span_remaining:.3f} > max gap {config.MAX_CENTER_GAP:.3f}. Adding custom board.")
        # Calculate width needed for the custom board to leave exactly MAX_CENTER_GAP
        custom_width_needed = center_span_remaining - config.MAX_CENTER_GAP
        custom_width_needed = max(0.0, custom_width_needed) # Ensure non-negative width

        if custom_width_needed > config.FLOAT_TOLERANCE: # Only add if width is meaningful
            custom_board_position = current_pos_bottom # Place it after the last bottom board
            custom_board_to_add = {
                "nominal": "Custom",
                "actual_width": round(custom_width_needed, 4), # Round for precision
                "position": round(custom_board_position, 4)
            }
            final_gap = config.MAX_CENTER_GAP # The gap will now be the target max gap
            custom_board_used = True
            result["custom_board_width"] = custom_board_to_add["actual_width"]
            log.info(f"Calculated custom board width: {custom_width_needed:.3f}\" to leave gap {final_gap:.3f}\"")
        else:
            log.warning(f"Custom board needed but calculated width ({custom_width_needed:.4f}) is too small. Leaving original gap.")
            # Keep final_gap as center_span_remaining

    elif center_span_remaining > config.MAX_CENTER_GAP + config.FLOAT_TOLERANCE:
        log.warning(f"Remaining span {center_span_remaining:.3f} > max gap {config.MAX_CENTER_GAP:.3f}, but custom board not allowed.")
        # Keep final_gap as center_span_remaining

    else: # Gap is already acceptable
        log.info(f"Remaining span {center_span_remaining:.3f} <= max gap {config.MAX_CENTER_GAP:.3f}. No custom board needed.")
        # Keep final_gap as center_span_remaining

    # 4. Add the custom board if calculated
    if custom_board_to_add:
        center_boards.append(custom_board_to_add)
        board_count += 1
        # No need to update current_pos_bottom as this is the last board before the gap

    # --- Final Validation and Result Assembly ---
    log.info(f"Final calculated center gap: {final_gap:.4f}\"")
    result["center_gap"] = final_gap
    result["narrow_board_used"] = custom_board_used # Use the internal flag name for the result key

    final_boards = bottom_boards + center_boards + top_boards
    result["floorboards"] = final_boards
    result["board_counts"] = dict(Counter(b["nominal"] for b in final_boards))
    result["total_board_width"] = sum(b["actual_width"] for b in final_boards)
    result["calculated_span_covered"] = result["total_board_width"] + result["center_gap"]

    # Final Status Check
    if board_count == 0 and target_span_along_length > config.FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Failed to place any floorboards for a non-zero target span."
    elif result["center_gap"] < -config.FLOAT_TOLERANCE: # Should not happen
        result["status"] = "ERROR"; result["message"] = f"Layout failed: Calculation resulted in overlap (gap={result['center_gap']:.3f}\")."
    elif result["center_gap"] <= config.MAX_CENTER_GAP + config.FLOAT_TOLERANCE:
        result["status"] = "OK"; result["message"] = f"Floorboard layout calculated successfully."
    else: # Gap is larger than recommended (should only happen if custom board not allowed)
        result["status"] = "WARNING"; result["message"] = f"Layout calculated, but center gap ({result['center_gap']:.3f}\") exceeds recommended max ({config.MAX_CENTER_GAP:.3f}\"). Custom board not used or not allowed."

    # Sanity Check: Calculated span covered vs target span
    if not math.isclose(result["calculated_span_covered"], target_span_along_length, abs_tol=config.FLOAT_TOLERANCE * 10):
        log.error(f"Verification failed: Calc span covered ({result['calculated_span_covered']:.4f}\") != target span ({target_span_along_length:.4f}\"). Critical error.")
        if result["status"] not in ["ERROR", "INPUT ERROR"]:
            result["status"] = "ERROR"; result["message"] += " CRITICAL: Span verification failed."

    log.info(f"Floorboard Calculation Complete. Final Status: {result['status']}")
    return result

