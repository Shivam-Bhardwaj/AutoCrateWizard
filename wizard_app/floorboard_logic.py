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
Version 0.3.19 - No logic changes, version updated for consistency with app.py import fix.
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
MAX_CUSTOM_NARROW_WIDTH: float = 5.50
MIN_STANDARD_BOARD_WIDTH: float = 5.50
MAX_STANDARD_BOARD_WIDTH: float = 11.25
MAX_CENTER_GAP: float = 0.25
FLOAT_TOLERANCE: float = 1e-6 # Calculation tolerance
EFFECTIVE_MAX_CUSTOM_WIDTH = MAX_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE * 10 # ~5.4999

# --- Helper Functions ---
def calculate_overall_skid_span(skid_layout_data: Dict[str, Any]) -> Optional[float]:
    """Calculates the overall span covered by skids, edge-to-edge."""
    skid_w = skid_layout_data.get('skid_width'); skid_count = skid_layout_data.get('skid_count'); positions = skid_layout_data.get('skid_positions')
    if skid_w is None or skid_count is None or positions is None: log.error("Missing skid data for span calculation."); return None
    if len(positions) != skid_count: log.error(f"Position list length ({len(positions)}) doesn't match skid count ({skid_count})."); return None
    if skid_w <= FLOAT_TOLERANCE: log.error(f"Invalid skid width ({skid_w}) for span calculation."); return None # Use tolerance
    if skid_count == 0: return 0.0
    elif skid_count == 1: return skid_w
    else:
        if not positions: log.error("Empty position list for multi-skid case."); return None
        first_outer_edge = positions[0] - skid_w / 2.0; last_outer_edge = positions[-1] + skid_w / 2.0
        span = abs(last_outer_edge - first_outer_edge)
        log.debug(f"Calculated overall skid span: {span:.3f}\"")
        return span

def get_available_standard_boards(available_nominal_sizes: List[str]) -> List[Tuple[str, float]]:
    """Filters and sorts available NOMINAL boards based on standard width rule."""
    standard_boards = []
    log.debug(f"Filtering available nominal sizes for standard boards: {available_nominal_sizes}")
    for nominal in available_nominal_sizes:
        width = ALL_STANDARD_FLOORBOARDS.get(nominal)
        if width is not None:
            if width >= MIN_STANDARD_BOARD_WIDTH - FLOAT_TOLERANCE and width <= MAX_STANDARD_BOARD_WIDTH + FLOAT_TOLERANCE:
                standard_boards.append((nominal, width))
                log.debug(f"  - Added '{nominal}' ({width}\") to standard boards.")
            else: log.debug(f"  - '{nominal}' ({width}\") is defined but outside standard width range.")
        else: log.warning(f"Nominal size '{nominal}' not found in standard definitions. Skipping.")
    standard_boards.sort(key=lambda x: x[1], reverse=True)
    log.debug(f"Available standard boards (Filtered & Sorted): {standard_boards}")
    return standard_boards

# --- Main Calculation Function ---
def calculate_floorboard_layout(
    skid_layout_data: Dict[str, Any],
    product_length: float,
    clearance_side: float,
    available_nominal_sizes: List[str],
    allow_custom_narrow_board: bool
) -> Dict[str, Any]:
    """
    Calculates floorboard layout symmetrically using available lumber and revised priority (v0.3.9).
    Places the best single board (standard or custom) first, then adds a secondary
    custom board if allowed and applicable to further minimize the gap.

    Args:
        skid_layout_data: Dictionary result from calculate_skid_layout.
        product_length: Length of the product (along skids) in inches.
        clearance_side: Clearance on each end (along length) in inches.
        available_nominal_sizes: List of *standard* nominal lumber sizes selected.
        allow_custom_narrow_board: Boolean flag to allow using a custom narrow board.

    Returns:
        A dictionary containing the floorboard layout details or an error status.
    """
    result = { "status": "INIT", "message": "Floorboard calculation not started.", "target_span_along_length": 0.0, "floorboard_length_across_skids": 0.0, "floorboards": [], "board_counts": {}, "custom_board_width": None, "center_gap": 0.0, "narrow_board_used": False, "calculated_span_covered": 0.0, "total_board_width": 0.0, "placement_method": "Symmetrical" }

    # --- Input Validation and Setup ---
    if skid_layout_data.get("status") != "OK": result["status"] = "ERROR"; result["message"] = "Skid layout status is not OK."; log.error(result["message"]); return result
    if product_length <= FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Product length must be positive."; log.error(result["message"]); return result # Use tolerance
    if clearance_side < -FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Clearance per side cannot be negative."; log.error(result["message"]); return result # Use tolerance
    if not available_nominal_sizes and not allow_custom_narrow_board: result["status"] = "ERROR"; result["message"] = "No standard lumber sizes selected AND custom narrow board not allowed."; log.error(result["message"]); return result

    target_span_along_length = product_length + 2 * clearance_side
    if target_span_along_length <= FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Target span along length is zero or negative."; log.error(result["message"]); return result # Use tolerance
    result["target_span_along_length"] = target_span_along_length

    floorboard_length_across_skids = calculate_overall_skid_span(skid_layout_data)
    if floorboard_length_across_skids is None or floorboard_length_across_skids <= FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Could not determine valid floorboard length (overall skid span)."; log.error(result["message"]); return result # Use tolerance
    result["floorboard_length_across_skids"] = floorboard_length_across_skids

    available_standard_boards = get_available_standard_boards(available_nominal_sizes)
    if not available_standard_boards and not allow_custom_narrow_board: result["status"] = "ERROR"; result["message"] = "No valid standard lumber sizes available and custom narrow board not allowed."; log.error(result["message"]); return result
    elif not available_standard_boards and allow_custom_narrow_board: log.warning("No standard lumber selected/available. Layout will depend solely on custom narrow board possibility.")

    log.info(f"Starting floorboard calculation for Target Span (Length): {target_span_along_length:.3f}\", Board Length (Width): {floorboard_length_across_skids:.3f}\", Custom Allowed: {allow_custom_narrow_board}")

    # --- Symmetrical Layout Calculation ---
    bottom_boards: List[Dict[str, Any]] = []; top_boards: List[Dict[str, Any]] = []
    current_pos_bottom: float = 0.0; current_pos_top: float = target_span_along_length
    center_boards: List[Dict[str, Any]] = [] # Can hold 0, 1, or 2 boards
    center_gap: float = 0.0
    narrow_board_used: bool = False; board_count = 0

    # 1. Place symmetrical pairs of STANDARD boards (widest first)
    while True:
        remaining_center_span = current_pos_top - current_pos_bottom
        if remaining_center_span < -FLOAT_TOLERANCE: log.error(f"Center span negative ({remaining_center_span:.4f})."); result["status"] = "ERROR"; result["message"] = "Internal calc error."; return result
        log.debug(f"Symmetric Loop: CenterSpan={remaining_center_span:.3f}")
        best_board_for_pair = None
        for nominal, width in available_standard_boards:
            if remaining_center_span >= (2 * width) - FLOAT_TOLERANCE: best_board_for_pair = {"nominal": nominal, "actual_width": width}; break
        if best_board_for_pair:
            width = best_board_for_pair["actual_width"]; log.debug(f"Placing symmetric pair: {best_board_for_pair['nominal']} ({width:.3f}\")")
            bottom_boards.append({"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_bottom}); current_pos_bottom += width; board_count += 1
            top_boards.insert(0, {"nominal": best_board_for_pair["nominal"], "actual_width": width, "position": current_pos_top - width}); current_pos_top -= width; board_count += 1
        else: log.debug("No more standard board pairs fit."); break
        if board_count > 200: result["status"] = "ERROR"; result["message"] = "Exceeded board count limit (symmetric)."; return result

    # 2. Handle the remaining center span
    center_span_remaining = current_pos_top - current_pos_bottom
    log.info(f"Center span remaining after symmetric placement: {center_span_remaining:.3f}\"")

    # Initial placement position for center board(s)
    initial_center_board_pos = current_pos_bottom

    if center_span_remaining < -FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Center span became negative."; return result
    elif center_span_remaining <= FLOAT_TOLERANCE: center_gap = 0.0; log.info("Center span is effectively zero.")
    else: # Center span > 0, evaluate fill options
        log.debug("Evaluating center fill options (Aggressive Gap Reduction Logic)...")

        # --- Step 3: Determine Best Initial Single Board ---
        best_initial_option = {"type": "none", "gap": center_span_remaining, "board": None}
        log.debug(f"  - Initial Option 'none': Gap = {best_initial_option['gap']:.4f}")

        # Option A: Custom Narrow Board (as initial single board)
        custom_initial_option = {"viable": False, "gap": float('inf'), "board": None}
        if allow_custom_narrow_board and center_span_remaining >= MIN_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE:
            custom_width_to_place = min(center_span_remaining, EFFECTIVE_MAX_CUSTOM_WIDTH)
            custom_initial_option["gap"] = max(0.0, center_span_remaining - custom_width_to_place) # Use tolerance in max
            custom_initial_option["board"] = {"nominal": "Custom", "actual_width": custom_width_to_place, "position": initial_center_board_pos}
            custom_initial_option["viable"] = True
            log.debug(f"  - Initial Option 'custom': Viable. Width={custom_width_to_place:.4f}, Gap={custom_initial_option['gap']:.4f}")
        else: log.debug(f"  - Initial Option 'custom': Not viable (Allowed={allow_custom_narrow_board}, Span={center_span_remaining:.3f})")

        # Option B: Standard Board (as initial single board)
        standard_initial_option = {"viable": False, "gap": float('inf'), "board": None}
        standard_center_candidate = None # Store the best standard candidate
        for nominal, width in available_standard_boards:
            if width <= center_span_remaining + FLOAT_TOLERANCE: # Use tolerance
                standard_center_candidate = {"nominal": nominal, "actual_width": width, "position": initial_center_board_pos}
                standard_initial_option["gap"] = max(0.0, center_span_remaining - width) # Use tolerance in max
                standard_initial_option["board"] = standard_center_candidate
                standard_initial_option["viable"] = True
                log.debug(f"  - Initial Option 'standard': Viable. Board={nominal}({width:.3f}), Gap={standard_initial_option['gap']:.4f}")
                break # Found widest fitting standard board
        if not standard_initial_option["viable"]: log.debug("  - Initial Option 'standard': Not viable (no standard board fits).")

        # Compare initial options to find the best single board to place first
        # Use tolerance for comparison
        if custom_initial_option["viable"] and custom_initial_option["gap"] < best_initial_option["gap"] - FLOAT_TOLERANCE:
            best_initial_option = {"type": "custom", "gap": custom_initial_option["gap"], "board": custom_initial_option["board"]}
        if standard_initial_option["viable"] and standard_initial_option["gap"] < best_initial_option["gap"] - FLOAT_TOLERANCE: # Use tolerance
             best_initial_option = {"type": "standard", "gap": standard_initial_option["gap"], "board": standard_initial_option["board"]}


        log.info(f"  Best initial single board option: '{best_initial_option['type']}' resulting in gap {best_initial_option['gap']:.4f}")

        # --- Step 4: Place the Initial Board ---
        initial_center_board = best_initial_option["board"]
        gap_after_initial_board = best_initial_option["gap"]
        initial_board_is_custom = False

        if initial_center_board is not None:
            center_boards.append(initial_center_board)
            board_count += 1
            if best_initial_option["type"] == "custom":
                narrow_board_used = True
                result["custom_board_width"] = initial_center_board["actual_width"]
                initial_board_is_custom = True
            log.debug(f"  Placed initial center board: {initial_center_board.get('nominal')}({initial_center_board.get('actual_width'):.3f}). Gap remaining: {gap_after_initial_board:.4f}")
        else:
             log.debug("  No initial board placed.")
             # Gap remains the original center_span_remaining
             gap_after_initial_board = center_span_remaining


        # --- Step 5: Check for Secondary Custom Fill ---
        center_gap = gap_after_initial_board # Assume this is the final gap unless secondary fill happens

        if (allow_custom_narrow_board and
            not initial_board_is_custom and # Can only add custom if the first wasn't custom
            gap_after_initial_board >= MIN_CUSTOM_NARROW_WIDTH - FLOAT_TOLERANCE): # Use tolerance

            log.debug("  Attempting secondary custom fill...")
            custom_width_secondary = min(gap_after_initial_board, EFFECTIVE_MAX_CUSTOM_WIDTH)
            if custom_width_secondary > FLOAT_TOLERANCE: # Only add if width is non-negligible
                log.info(f"  Placing secondary custom board with width: {custom_width_secondary:.3f}")

                # Calculate position for the secondary board
                secondary_board_pos = initial_center_board_pos + (initial_center_board["actual_width"] if initial_center_board else 0)

                custom_board_secondary = {
                    "nominal": "Custom",
                    "actual_width": custom_width_secondary,
                    "position": secondary_board_pos
                }
                center_boards.append(custom_board_secondary)
                board_count += 1
                center_gap = max(0.0, gap_after_initial_board - custom_width_secondary) # Update final gap, use tolerance in max
                narrow_board_used = True # Mark custom as used
                # Store the width of the *second* custom board if it's the only one
                if result["custom_board_width"] is None:
                     result["custom_board_width"] = custom_width_secondary
                # If a custom board was already placed initially, custom_board_width is already set.
                # We might want to store both widths, but for now, store the first one encountered.

                log.debug(f"  Placed secondary custom board. Final Gap: {center_gap:.4f}")
            else:
                 log.debug(f"  Secondary custom width ({custom_width_secondary:.4f}\") too small to place.")

        else:
            log.debug("  Secondary custom fill not applicable.")


    # --- Final Validation and Result Assembly ---
    log.info(f"Final calculated center gap: {center_gap:.4f}\"")
    result["center_gap"] = max(0.0, center_gap) # Ensure gap is non-negative due to float math
    result["narrow_board_used"] = narrow_board_used

    final_boards = bottom_boards + center_boards + top_boards # Combine all parts
    result["floorboards"] = final_boards

    result["board_counts"] = dict(Counter(b["nominal"] for b in final_boards))
    result["total_board_width"] = sum(b["actual_width"] for b in final_boards)
    result["calculated_span_covered"] = result["total_board_width"] + result["center_gap"]

    # Final Status Check based on gap size
    if board_count == 0 and target_span_along_length > FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = "Failed to place any floorboards."; log.error(result["message"])
    elif result["center_gap"] < -FLOAT_TOLERANCE: result["status"] = "ERROR"; result["message"] = f"Layout failed: Calculation overlap (gap={result['center_gap']:.3f}\")."; log.error(result["message"])
    elif result["center_gap"] <= MAX_CENTER_GAP + FLOAT_TOLERANCE: result["status"] = "OK"; result["message"] = f"Floorboard layout calculated successfully."; log.info(result["message"])
    else: result["status"] = "WARNING"; result["message"] = f"Layout calculated, but center gap ({result['center_gap']:.3f}\") exceeds recommended max ({MAX_CENTER_GAP:.3f}\")."; log.warning(result["message"])

    # Sanity Check
    total_width_check = result["calculated_span_covered"]
    if not math.isclose(total_width_check, target_span_along_length, abs_tol=FLOAT_TOLERANCE * 10): log.error(f"Verification failed: Calc span {total_width_check:.4f} != Target {target_span_along_length:.4f}")

    log.info(f"Floorboard Calculation Complete. Final Status: {result['status']}")
    return result

# --- Example Usage (for testing) ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    test_skid_data_ok = { "skid_type": "4x6", "skid_width": 5.5, "skid_height": 3.5, "skid_count": 5, "spacing_actual": 22.125, "max_spacing": 28.0, "crate_width": 98.0, "usable_width": 96.0, "skid_positions": [-44.25, -22.125, 0.0, 22.125, 44.25], "status": "OK", "message": "Skid layout calculated successfully." }
    default_std_sizes = ["2x12", "2x10", "2x8", "2x6"]

    import json
    def run_test(label, prod_len, clr_side, nominal_list, allow_custom):
        print(f"\n--- {label} (Custom Allowed: {allow_custom}) ---")
        layout = calculate_floorboard_layout(test_skid_data_ok, prod_len, clr_side, nominal_list, allow_custom)
        print(json.dumps(layout, indent=2))

    # --- Test Cases (v0.3.9, v0.3.18 checks) ---

    # Case 1: Target=74.0 (Center=6.5), Custom Allowed
    run_test("Test Case 1 (Center=6.5)", 70.0, 2.0, default_std_sizes, True)
    # Expect: Initial best = 2x6 (5.5), leaves 1.0 gap. Secondary custom fails (1.0 < 2.5). Final Gap=1.0 -> WARNING

    # Case 2: Target=50.0 (Center=5.0), Custom Allowed
    run_test("Test Case 2 (Center=5.0)", 46.0, 2.0, default_std_sizes, True)
    # Expect: Initial best = Custom(5.0), leaves 0 gap. Secondary custom N/A. Final Gap=0 -> OK

    # Case 3: Target=50.5 (Center=5.5), Custom Allowed
    run_test("Test Case 3 (Center=5.5)", 46.5, 2.0, default_std_sizes, True)
    # Expect: Initial best = 2x6 (5.5), leaves 0 gap. Secondary custom fails (0 < 2.5). Final Gap=0 -> OK

    # Case 4: Target=48.8 (Center=3.8), Custom Allowed
    run_test("Test Case 4 (Center=3.8)", 44.8, 2.0, default_std_sizes, True)
    # Expect: Initial best = Custom(3.8), leaves 0 gap. Secondary custom N/A. Final Gap=0 -> OK

    # Case 18 (ACTUAL Two-Stage): Target=59.0 (Center=14.0), Custom Allowed
    run_test("Test Case 18 (Center=14.0)", 55.0, 2.0, default_std_sizes, True)
    # Expect: Initial best = 2x12 (11.25), leaves 2.75 gap. Secondary custom adds Custom(2.75). Final Gap=0 -> OK

    # Case 19 (Target=67.0 / Center=22.0 from screenshot), Custom Allowed
    run_test("Test Case 19 (Center=22.0)", 63.0, 2.0, ["2x12"], True)
    # Expect: Initial best = 2x12 (11.25), leaves 10.75 gap. Secondary custom adds Custom(5.5). Final Gap=5.25 -> WARNING

    # Add a test case for target span just under 2.5 to ensure no custom board is placed
    run_test("Test Case 20 (Center=2.0)", 40.0, 2.0, default_std_sizes, True)
    # Expect: Initial best = none. Secondary custom fails (2.0 < 2.5). Final Gap=2.0 -> WARNING

    # Add a test case with only narrow custom allowed
    run_test("Test Case 21 (Center=4.0, Custom Only)", 40.0, 4.0, [], True)
    # Expect: Initial best = Custom(4.0). Secondary custom N/A. Final Gap=0 -> OK

    # Add a test case with only standard allowed, center needs custom
    run_test("Test Case 22 (Center=4.0, Std Only)", 40.0, 4.0, default_std_sizes, False)
    # Expect: Initial best = none. Secondary custom not allowed. Final Gap=4.0 -> WARNING

