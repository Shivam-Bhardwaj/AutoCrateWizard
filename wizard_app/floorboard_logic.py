# floorboard_logic.py
"""
Logic for calculating floorboard layout for industrial shipping crates.
Uses symmetrical placement. Standard boards >= 5.5" and <= 11.25".
Allows one **custom** narrow board >= 2.5" and < 5.5" IF explicitly allowed.
Boards placed butt-to-butt.

Center fill priority (v0.3.9 - Aggressive Gap Reduction):
1. Perform symmetrical placement. Calculate `center_span_remaining`.
2. Determine the best *single* board (standard, custom, or none) that initially
   minimizes the gap (`initial_center_board`, `gap_after_initial_board`).
3. Place `initial_center_board` (if any).
4. If `allow_custom` is True, AND `initial_center_board` was NOT custom,
   AND `gap_after_initial_board` >= 2.5":
    - Place a *second* center board ('Custom') with width
      min(`gap_after_initial_board`, ~5.5") to further reduce the gap.
5. Calculate final gap.

Final status aims for center gap <= 0.25" (OK), otherwise WARNING.

Version 0.3.9 - Implemented aggressive gap reduction logic.
Version 0.3.17 - Refined gap visualization check logic (strict zero check).
Version 0.3.18 - No logic changes, version updated for consistency with app.py.
Version 0.3.19 - No logic changes, version updated for consistency with app.py import fix. (No changes for v0.4.3)
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

# Configure logging
log = logging.getLogger(__name__)

# --- Constants ---
ALL_STANDARD_FLOORBOARDS: Dict[str, float] = { "2x12": 11.25, "2x10": 9.25, "2x8": 7.25, "2x6": 5.5 }
MIN_CUSTOM_NARROW_WIDTH: float = 2.50
MAX_CUSTOM_NARROW_WIDTH: float = 5.50 # Actual width, not nominal
MIN_STANDARD_BOARD_WIDTH: float = 5.50
MAX_STANDARD_BOARD_WIDTH: float = 11.25
MAX_CENTER_GAP: float = 0.25 # Recommended max gap
FLOAT_TOLERANCE: float = 1e-6 # Calculation tolerance
EFFECTIVE_MAX_CUSTOM_WIDTH = MAX_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE * 10 # Used to avoid placing a board that's effectively MAX_CUSTOM_NARROW_WIDTH but slightly over due to float math

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
    if skid_w <= FLOAT_TOLERANCE: # Check against tolerance
        log.error(f"Invalid skid width ({skid_w}) for span calculation.")
        return None

    if skid_count == 0:
        return 0.0
    elif skid_count == 1:
        return skid_w
    else:
        # Positions are centerlines. Span is from outer edge of first to outer edge of last.
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
        width = ALL_STANDARD_FLOORBOARDS.get(nominal)
        if width is not None:
            # Check if width falls within the defined standard range using tolerance
            if width >= MIN_STANDARD_BOARD_WIDTH - FLOAT_TOLERANCE and \
               width <= MAX_STANDARD_BOARD_WIDTH + FLOAT_TOLERANCE:
                standard_boards.append((nominal, width))
                log.debug(f"  - Added '{nominal}' ({width}\") to standard boards.")
            else:
                log.debug(f"  - '{nominal}' ({width}\") is defined but outside standard width range [{MIN_STANDARD_BOARD_WIDTH}, {MAX_STANDARD_BOARD_WIDTH}].")
        else:
            log.warning(f"Nominal size '{nominal}' not found in ALL_STANDARD_FLOORBOARDS definitions. Skipping.")
    # Sort by actual width, widest first
    standard_boards.sort(key=lambda x: x[1], reverse=True)
    log.debug(f"Available standard boards (Filtered & Sorted by width desc): {standard_boards}")
    return standard_boards

# --- Main Calculation Function ---
def calculate_floorboard_layout(
    skid_layout_data: Dict[str, Any],
    product_length: float, # This is the length of the product, used to determine target span
    clearance_side: float, # Clearance on each side of product_length
    available_nominal_sizes: List[str], # List of selected nominal sizes like "2x6", "2x8"
    allow_custom_narrow_board: bool
) -> Dict[str, Any]:
    """
    Calculates floorboard layout symmetrically.
    """
    result = {
        "status": "INIT", "message": "Floorboard calculation not started.",
        "target_span_along_length": 0.0, "floorboard_length_across_skids": 0.0,
        "floorboards": [], "board_counts": {}, "custom_board_width": None,
        "center_gap": 0.0, "narrow_board_used": False,
        "calculated_span_covered": 0.0, "total_board_width": 0.0,
        "placement_method": "Symmetrical with Aggressive Gap Reduction"
    }

    # --- Input Validation and Setup ---
    if skid_layout_data.get("status") != "OK":
        result["status"] = "ERROR"; result["message"] = "Skid layout status is not OK. Cannot calculate floorboards."
        log.error(result["message"]); return result
    if product_length <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Product length must be positive."
        log.error(result["message"]); return result
    if clearance_side < -FLOAT_TOLERANCE: # Allow zero clearance
        result["status"] = "ERROR"; result["message"] = "Clearance per side cannot be negative."
        log.error(result["message"]); return result
    if not available_nominal_sizes and not allow_custom_narrow_board:
        result["status"] = "ERROR"; result["message"] = "No standard lumber sizes selected AND custom narrow board not allowed."
        log.error(result["message"]); return result

    # Target span for floorboards is along the product_length dimension
    target_span_along_length = product_length + 2 * clearance_side
    if target_span_along_length <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Target span for floorboards (product length + clearances) is zero or negative."
        log.error(result["message"]); return result
    result["target_span_along_length"] = target_span_along_length

    # Floorboard length is across the skids (overall skid span)
    floorboard_length_across_skids = calculate_overall_skid_span(skid_layout_data)
    if floorboard_length_across_skids is None or floorboard_length_across_skids <= FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Could not determine valid floorboard length (overall skid span is zero or invalid)."
        log.error(result["message"]); return result
    result["floorboard_length_across_skids"] = floorboard_length_across_skids

    available_standard_boards = get_available_standard_boards(available_nominal_sizes)
    if not available_standard_boards and not allow_custom_narrow_board:
        result["status"] = "ERROR"; result["message"] = "No valid standard lumber sizes available and custom narrow board not allowed."
        log.error(result["message"]); return result
    elif not available_standard_boards and allow_custom_narrow_board:
        log.warning("No standard lumber selected/available. Layout will depend solely on custom narrow board possibility.")

    log.info(f"Starting floorboard calculation for Target Span (Length): {target_span_along_length:.3f}\", Board Length (Width): {floorboard_length_across_skids:.3f}\", Custom Allowed: {allow_custom_narrow_board}")

    # --- Symmetrical Layout Calculation ---
    bottom_boards: List[Dict[str, Any]] = []; top_boards: List[Dict[str, Any]] = []
    current_pos_bottom: float = 0.0 # Start from 0 for bottom boards
    current_pos_top: float = target_span_along_length # Start from end for top boards
    center_boards: List[Dict[str, Any]] = []
    center_gap: float = 0.0
    narrow_board_used: bool = False; board_count = 0

    # 1. Place symmetrical pairs of STANDARD boards (widest first)
    while True:
        remaining_center_span_for_pairs = current_pos_top - current_pos_bottom
        if remaining_center_span_for_pairs < -FLOAT_TOLERANCE:
            log.error(f"Center span for pairs became negative ({remaining_center_span_for_pairs:.4f}). This indicates a calculation error.");
            result["status"] = "ERROR"; result["message"] = "Internal calculation error during symmetric pairing."; return result

        log.debug(f"Symmetric Pair Loop: Remaining Center Span for Pairs = {remaining_center_span_for_pairs:.3f}")
        best_board_for_pair = None
        for nominal, width in available_standard_boards:
            if remaining_center_span_for_pairs >= (2 * width) - FLOAT_TOLERANCE: # Can fit two of these
                best_board_for_pair = {"nominal": nominal, "actual_width": width}; break
        
        if best_board_for_pair:
            width = best_board_for_pair["actual_width"]
            log.debug(f"Placing symmetric pair: {best_board_for_pair['nominal']} ({width:.3f}\")")
            bottom_boards.append({"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_bottom})
            current_pos_bottom += width
            board_count += 1
            
            # Top boards are placed from the end, so their position is current_pos_top - width
            top_boards.insert(0, {"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_top - width})
            current_pos_top -= width
            board_count += 1
        else:
            log.debug("No more standard board pairs fit symmetrically.")
            break
        if board_count > 200: # Safety break
            result["status"] = "ERROR"; result["message"] = "Exceeded board count limit (200) during symmetric placement."; return result

    # 2. Handle the remaining center span
    center_span_remaining_after_pairs = current_pos_top - current_pos_bottom
    log.info(f"Center span remaining after symmetric standard board placement: {center_span_remaining_after_pairs:.3f}\"")

    initial_center_board_pos = current_pos_bottom # Position for the first center board

    if center_span_remaining_after_pairs < -FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Center span became negative after symmetric placement."; return result
    elif center_span_remaining_after_pairs <= FLOAT_TOLERANCE: # Effectively zero
        center_gap = 0.0
        log.info("Center span is effectively zero after symmetric placement. No center fill needed.")
    else: # Center span > 0, evaluate fill options using aggressive gap reduction
        log.debug("Evaluating center fill options (Aggressive Gap Reduction Logic)...")

        # --- Step 3: Determine Best Initial Single Board for Center ---
        best_initial_center_option = {"type": "none", "gap": center_span_remaining_after_pairs, "board_to_place": None}
        log.debug(f"  - Initial Center Option 'none': Gap = {best_initial_center_option['gap']:.4f}")

        # Option A: Custom Narrow Board as initial single center board
        custom_initial_center_option = {"viable": False, "gap": float('inf'), "board_to_place": None}
        if allow_custom_narrow_board and center_span_remaining_after_pairs >= MIN_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE:
            custom_width_to_place = min(center_span_remaining_after_pairs, EFFECTIVE_MAX_CUSTOM_WIDTH)
            custom_initial_center_option["gap"] = max(0.0, center_span_remaining_after_pairs - custom_width_to_place)
            custom_initial_center_option["board_to_place"] = {"nominal": "Custom", "actual_width": custom_width_to_place, "position": initial_center_board_pos}
            custom_initial_center_option["viable"] = True
            log.debug(f"  - Initial Center Option 'custom': Viable. Width={custom_width_to_place:.4f}, Resulting Gap={custom_initial_center_option['gap']:.4f}")
        else:
            log.debug(f"  - Initial Center Option 'custom': Not viable (AllowCustom={allow_custom_narrow_board}, Span={center_span_remaining_after_pairs:.3f}, MinCustomW={MIN_CUSTOM_NARROW_WIDTH})")

        # Option B: Standard Board as initial single center board
        standard_initial_center_option = {"viable": False, "gap": float('inf'), "board_to_place": None}
        for nominal, width in available_standard_boards: # Widest fitting standard board
            if width <= center_span_remaining_after_pairs + FLOAT_TOLERANCE:
                standard_initial_center_option["gap"] = max(0.0, center_span_remaining_after_pairs - width)
                standard_initial_center_option["board_to_place"] = {"nominal": nominal, "actual_width": width, "position": initial_center_board_pos}
                standard_initial_center_option["viable"] = True
                log.debug(f"  - Initial Center Option 'standard': Viable. Board={nominal}({width:.3f}), Resulting Gap={standard_initial_center_option['gap']:.4f}")
                break # Found the widest fitting standard board
        if not standard_initial_center_option["viable"]:
            log.debug("  - Initial Center Option 'standard': Not viable (no standard board fits the remaining center span).")

        # Compare initial center options to find the best single board to place first
        if custom_initial_center_option["viable"] and custom_initial_center_option["gap"] < best_initial_center_option["gap"] - FLOAT_TOLERANCE:
            best_initial_center_option = {"type": "custom", "gap": custom_initial_center_option["gap"], "board_to_place": custom_initial_center_option["board_to_place"]}
        if standard_initial_center_option["viable"] and standard_initial_center_option["gap"] < best_initial_center_option["gap"] - FLOAT_TOLERANCE:
             best_initial_center_option = {"type": "standard", "gap": standard_initial_center_option["gap"], "board_to_place": standard_initial_center_option["board_to_place"]}

        log.info(f"  Best initial single center board option: '{best_initial_center_option['type']}' resulting in gap {best_initial_center_option['gap']:.4f}")

        # --- Step 4: Place the Initial Center Board ---
        initial_center_board_placed = best_initial_center_option["board_to_place"]
        gap_after_initial_center_board = best_initial_center_option["gap"]
        initial_center_board_was_custom = False

        if initial_center_board_placed is not None:
            center_boards.append(initial_center_board_placed)
            board_count += 1
            current_pos_bottom += initial_center_board_placed["actual_width"] # Advance position
            if best_initial_center_option["type"] == "custom":
                narrow_board_used = True
                result["custom_board_width"] = initial_center_board_placed["actual_width"]
                initial_center_board_was_custom = True
            log.debug(f"  Placed initial center board: {initial_center_board_placed.get('nominal')}({initial_center_board_placed.get('actual_width'):.3f}). Gap remaining: {gap_after_initial_center_board:.4f}")
        else:
             log.debug("  No initial center board placed (type was 'none').")
             gap_after_initial_center_board = center_span_remaining_after_pairs # Gap remains the same

        # --- Step 5: Check for Secondary Custom Fill ---
        center_gap = gap_after_initial_center_board # This is the final gap unless secondary fill happens

        if (allow_custom_narrow_board and
            not initial_center_board_was_custom and # Can only add secondary custom if the first wasn't custom
            gap_after_initial_center_board >= MIN_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE):

            log.debug("  Attempting secondary custom fill for remaining gap...")
            custom_width_secondary = min(gap_after_initial_center_board, EFFECTIVE_MAX_CUSTOM_WIDTH)
            if custom_width_secondary >= MIN_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE : # Ensure it's a valid custom width
                log.info(f"  Placing secondary custom board with width: {custom_width_secondary:.3f}")
                
                # Position for the secondary custom board is after the initial center board (if any)
                secondary_board_pos = initial_center_board_pos + (initial_center_board_placed["actual_width"] if initial_center_board_placed else 0)
                
                custom_board_secondary = {
                    "nominal": "Custom", "actual_width": custom_width_secondary,
                    "position": secondary_board_pos
                }
                center_boards.append(custom_board_secondary)
                board_count += 1
                current_pos_bottom += custom_width_secondary # Advance position
                center_gap = max(0.0, gap_after_initial_center_board - custom_width_secondary)
                narrow_board_used = True
                if result["custom_board_width"] is None: # If first board was standard, this is the first custom
                     result["custom_board_width"] = custom_width_secondary
                elif initial_center_board_placed and result["custom_board_width"] != initial_center_board_placed.get("actual_width"):
                    # This case handles if first was custom, and we add another custom, which shouldn't happen with current logic.
                    # For now, we are just storing one custom width. Could be extended to list of custom widths.
                    log.warning("Multiple distinct custom boards placed; 'custom_board_width' might only reflect one.")


                log.debug(f"  Placed secondary custom board. Final Gap: {center_gap:.4f}")
            else:
                 log.debug(f"  Secondary custom width ({custom_width_secondary:.4f}\") too small or not meeting min custom width. Not placed.")
        else:
            log.debug(f"  Secondary custom fill not applicable. (AllowCustom={allow_custom_narrow_board}, InitialWasCustom={initial_center_board_was_custom}, GapAfterInitial={gap_after_initial_center_board:.3f})")

    # --- Final Validation and Result Assembly ---
    log.info(f"Final calculated center gap: {center_gap:.4f}\"")
    result["center_gap"] = max(0.0, center_gap) # Ensure non-negative
    result["narrow_board_used"] = narrow_board_used

    # Combine all boards in order: bottom, center, top
    final_boards = bottom_boards + center_boards + top_boards
    result["floorboards"] = final_boards

    result["board_counts"] = dict(Counter(b["nominal"] for b in final_boards))
    result["total_board_width"] = sum(b["actual_width"] for b in final_boards)
    # Calculated span covered should be total board width + final center gap
    result["calculated_span_covered"] = result["total_board_width"] + result["center_gap"]

    # Final Status Check
    if board_count == 0 and target_span_along_length > FLOAT_TOLERANCE:
        result["status"] = "ERROR"; result["message"] = "Failed to place any floorboards for a non-zero target span."
        log.error(result["message"])
    elif result["center_gap"] < -FLOAT_TOLERANCE: # Should not happen with max(0,...)
        result["status"] = "ERROR"; result["message"] = f"Layout failed: Calculation resulted in overlap (gap={result['center_gap']:.3f}\")."
        log.error(result["message"])
    elif result["center_gap"] <= MAX_CENTER_GAP + FLOAT_TOLERANCE:
        result["status"] = "OK"; result["message"] = f"Floorboard layout calculated successfully."
        log.info(result["message"])
    else: # Gap is larger than recommended
        result["status"] = "WARNING"; result["message"] = f"Layout calculated, but center gap ({result['center_gap']:.3f}\") exceeds recommended max ({MAX_CENTER_GAP:.3f}\")."
        log.warning(result["message"])

    # Sanity Check: Calculated span covered vs target span
    if not math.isclose(result["calculated_span_covered"], target_span_along_length, abs_tol=FLOAT_TOLERANCE * 10):
        log.error(f"Verification failed: Calculated span covered ({result['calculated_span_covered']:.4f}\") does not match target span ({target_span_along_length:.4f}\"). This is a critical error.")
        # Potentially override status to ERROR if it's not already an error
        if result["status"] not in ["ERROR", "INPUT ERROR"]:
            result["status"] = "ERROR"
            result["message"] += " CRITICAL: Span verification failed."


    log.info(f"Floorboard Calculation Complete. Final Status: {result['status']}")
    return result

