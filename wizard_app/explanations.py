# wizard_app/explanations.py
"""
Contains detailed explanation text for the AutoCrate Wizard UI,
closely following the logic and variable names from the provided NX expressions list.
Version 0.4.15
"""
import math
import logging
# Use absolute import assuming execution context is set up correctly
try:
    from . import config
except ImportError:
    # Fallback for potential direct script execution or testing
    import config

log = logging.getLogger(__name__)

def format_metric_for_explanation(value, unit="\"", decimals=2, default="N/A"):
    """Helper to format values consistently in explanations."""
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value): return default
    try: return f"{value:.{0 if abs(value - round(value)) < config.FLOAT_TOLERANCE else decimals}f}{unit}"
    except (TypeError, ValueError): return str(value)

# --- Skid/Base Explanation ---
def get_skid_explanation(skid_results, ui_inputs):
    """Returns the detailed explanation markdown for the skid layout, referencing NX expressions."""
    # Extract results and inputs
    skid_type = skid_results.get('skid_type', 'N/A')
    max_spacing_calc = format_metric_for_explanation(skid_results.get('max_spacing')) # Calculated based on weight rule
    crate_width_calc = format_metric_for_explanation(skid_results.get('crate_width'))
    usable_width_calc = format_metric_for_explanation(skid_results.get('usable_width'))
    actual_spacing_calc = format_metric_for_explanation(skid_results.get('spacing_actual'))
    skid_count_calc = skid_results.get('skid_count', 0)
    skid_width_calc = format_metric_for_explanation(skid_results.get('skid_width'))
    skid_height_calc = format_metric_for_explanation(skid_results.get('skid_height'))

    # Map UI inputs to NX CTRL names (for display)
    ctrl_prod_weight = format_metric_for_explanation(ui_inputs.get('product_weight'), unit=" lbs", decimals=1)
    ctrl_prod_width = format_metric_for_explanation(ui_inputs.get('product_width'))
    ctrl_clearance_side = format_metric_for_explanation(ui_inputs.get('clearance_side'))
    ctrl_panel_thickness = format_metric_for_explanation(ui_inputs.get('panel_thickness'))
    ctrl_cleat_thickness = format_metric_for_explanation(ui_inputs.get('wall_cleat_thickness')) # Using wall cleat thickness

    # Relevant NX Expressions from list
    nx_crate_width = f"OUT_Crate_Width = CTRL_Prod_Width + 2 * CTRL_Clearance_Side + 2 * CTRL_Panel_Thickness + 2 * CTRL_Cleat_Thickness"
    nx_usable_width = f"VAR_Usable_Skid_Width = OUT_Crate_Width - 2 * (CTRL_Panel_Thickness + CTRL_Cleat_Thickness)"
    nx_max_spacing = f"VAR_Max_Skid_Spacing = if(CTRL_Prod_Weight <= 500) then (30) else if ... (etc.)"
    nx_skid_width = f"VAR_Skid_Width = if(CTRL_Prod_Weight <= 4500) then (3.5) else (5.5)"
    nx_skid_height = f"VAR_Skid_Height = 3.5" # Fixed in NX list
    nx_skid_count = f"VAR_Skid_Count = ceil(VAR_Usable_Skid_Width / VAR_Max_Skid_Spacing)" # Simplified concept in NX list
    nx_actual_spacing = f"VAR_Skid_Spacing_Actual = if(VAR_Skid_Count <= 1) then (0) else (VAR_Usable_Skid_Width / (VAR_Skid_Count - 1))"
    nx_skid_start_x = f"VAR_Skid_Start_X = -VAR_Usable_Skid_Width / 2"
    nx_skid_x_n = f"VAR_Skid_X_n = VAR_Skid_Start_X + n * VAR_Skid_Spacing_Actual"

    return f"""
#### Base/Skid Calculation Logic (Based on NX Expressions):

1.  **Determine Skid Dimensions:**
    * `VAR_Skid_Width` = `{skid_width_calc}` (Based on `CTRL_Prod_Weight` = `{ctrl_prod_weight}`. *NX Ref:* `{nx_skid_width}`)
    * `VAR_Skid_Height` = `{skid_height_calc}` (*NX Ref:* `{nx_skid_height}`)

2.  **Calculate Overall Crate Width:**
    * `OUT_Crate_Width` = `CTRL_Prod_Width` (`{ctrl_prod_width}`) + 2 * `CTRL_Clearance_Side` (`{ctrl_clearance_side}`) + 2 * `CTRL_Panel_Thickness` (`{ctrl_panel_thickness}`) + 2 * `CTRL_Cleat_Thickness` (`{ctrl_cleat_thickness}`) = **`{crate_width_calc}`**
    * *NX Ref:* `{nx_crate_width}`

3.  **Calculate Usable Width for Skids:** (Space between inner faces of wall cleats)
    * `VAR_Usable_Skid_Width` = `OUT_Crate_Width` (`{crate_width_calc}`) - 2 * (`CTRL_Panel_Thickness` (`{ctrl_panel_thickness}`) + `CTRL_Cleat_Thickness` (`{ctrl_cleat_thickness}`)) = **`{usable_width_calc}`**
    * *NX Ref:* `{nx_usable_width}`

4.  **Determine Max Skid Spacing:**
    * `VAR_Max_Skid_Spacing` = **`{max_spacing_calc}`** (Based on `CTRL_Prod_Weight`. *NX Ref:* `{nx_max_spacing}`)

5.  **Calculate Skid Count:**
    * The number of skids needed to ensure spacing is less than or equal to `VAR_Max_Skid_Spacing`.
    * *Python Logic:* Iteratively checks or uses `ceil` function based on `VAR_Usable_Skid_Width` and `VAR_Max_Skid_Spacing`. Minimum 2 skids if space allows.
    * *NX Ref (Simplified):* `{nx_skid_count}`
    * *Result:* `VAR_Skid_Count` = **`{skid_count_calc}`**

6.  **Calculate Actual Skid Spacing:**
    * `VAR_Skid_Spacing_Actual` = `VAR_Usable_Skid_Width` / (`VAR_Skid_Count` - 1) (if Count > 1, else 0)
    * *Result:* = **`{actual_spacing_calc}`**
    * *NX Ref:* `{nx_actual_spacing}`

7.  **Calculate Skid Positions:** (Centerlines relative to center of Usable Width)
    * First skid position (`VAR_Skid_Start_X`) = -`VAR_Usable_Skid_Width` / 2
    * Subsequent positions (`VAR_Skid_X_n`) = `VAR_Skid_Start_X` + n * `VAR_Skid_Spacing_Actual`
    * *NX Ref:* `{nx_skid_start_x}`, `{nx_skid_x_n}`
    * *Resulting Positions:* Displayed on schematic relative to 0.0 center.
"""

# --- Floorboard Explanation ---
def get_floorboard_explanation(floor_results, ui_inputs):
    """Returns the detailed explanation markdown for the floorboard layout, referencing NX expressions."""
    # Extract results and inputs
    target_span = format_metric_for_explanation(floor_results.get('target_span_along_length'))
    board_length = format_metric_for_explanation(floor_results.get('floorboard_length_across_skids'))
    placement_method = floor_results.get("placement_method", "N/A")
    gap = format_metric_for_explanation(floor_results.get('center_gap'), decimals=3)
    custom_used = floor_results.get("narrow_board_used")
    custom_width = format_metric_for_explanation(floor_results.get("custom_board_width"), decimals=3)
    max_gap_allowed = format_metric_for_explanation(config.MAX_CENTER_GAP)

    # Map UI inputs to NX CTRL names
    ctrl_prod_length = format_metric_for_explanation(ui_inputs.get('product_length'))
    ctrl_clearance_side = format_metric_for_explanation(ui_inputs.get('clearance_side'))
    ctrl_panel_thickness = format_metric_for_explanation(ui_inputs.get('panel_thickness'))
    ctrl_cleat_thickness = format_metric_for_explanation(ui_inputs.get('wall_cleat_thickness'))
    # Note: NX list uses a fixed CTRL_Board_Width, Python uses available sizes
    nx_board_width_ctrl = 7.5 # From NX list example

    # Relevant NX Expressions (Note: Logic differs significantly from Python implementation)
    nx_floor_span = f"~ OUT_Crate_Width - 2 * (CTRL_Panel_Thickness + CTRL_Cleat_Thickness)" # Span boards cover width-wise
    nx_board_count = f"VAR_Board_Count_Floor = floor(({nx_floor_span}) / CTRL_Board_Width)"
    nx_board_remaining = f"VAR_Board_Remaining_Floor = (({nx_floor_span}) / CTRL_Board_Width) - VAR_Board_Count_Floor"
    nx_final_count = f"VAR_Board_Final_Count = if(VAR_Board_Remaining_Floor <= CTRL_Min_Board_Remaining) then (VAR_Board_Count_Floor - 1) else (VAR_Board_Count_Floor)"
    nx_spacer_x = f"VAR_Floor_Spacer_X = ({nx_floor_span} - (VAR_Board_Final_Count * CTRL_Board_Width)) / 2"

    return f"""
#### Floorboard Calculation Logic:

*Note: The Python implementation uses a symmetrical placement with available board sizes and a potential single custom fill board, which differs from the simpler NX expression logic shown below based on a fixed board width.*

1.  **Target Span (Layout Height):** This is the dimension along the crate length that floorboards need to cover.
    * *Calculation:* `CTRL_Prod_Length` (`{ctrl_prod_length}`) + 2 * `CTRL_Clearance_Side` (`{ctrl_clearance_side}`) = **`{target_span}`**.

2.  **Board Length (Layout Width):** This is the length each floorboard needs to be cut to.
    * *Calculation:* Equal to the Overall Skid Span = **`{board_length}`**.

3.  **Placement (Python Logic - `{placement_method}`):**
    * Standard boards (e.g., 2x6, 2x8) are placed symmetrically from the outside edges inwards.
    * The remaining central gap is calculated.
    * If `Allow Custom Board` is checked and the gap > `{max_gap_allowed}`, one custom board is added to reduce the gap *to* `{max_gap_allowed}`.
    * *Result:* Final Gap = `{gap}`. Custom Board Used: `{'Yes (' + custom_width + ')' if custom_used else 'No'}`.

4.  **NX Expression Logic (Example - Different Approach):**
    * Calculates span: `{nx_floor_span}`
    * Calculates how many fixed-width boards (`CTRL_Board_Width` = {nx_board_width_ctrl}") fit: `{nx_board_count}`
    * Determines if the last board should be dropped based on remainder: `{nx_final_count}`
    * Calculates spacing/gap needed on each side: `{nx_spacer_x}`
"""

# --- Wall Panel Explanation ---
def get_wall_panel_explanation(panel_data, panel_type_label, overall_dims):
    """Returns the detailed explanation markdown for a wall panel layout, referencing NX expressions."""
    panel_width = format_metric_for_explanation(panel_data.get('panel_width'))
    panel_height = format_metric_for_explanation(panel_data.get('panel_height'))
    threshold = format_metric_for_explanation(config.INTERMEDIATE_CLEAT_THRESHOLD) # This is INTERMEDIATE_CLEAT_ADD_THRESHOLD from wall_logic
    # Correct threshold to match wall_logic constant if different
    # threshold = format_metric_for_explanation(wall_logic.INTERMEDIATE_CLEAT_ADD_THRESHOLD)

    cleat_spec = panel_data.get('cleat_spec', {})
    cleat_dims = f"{format_metric_for_explanation(cleat_spec.get('thickness'), decimals=2)}x{format_metric_for_explanation(cleat_spec.get('width'))}"
    plywood_thickness = format_metric_for_explanation(panel_data.get('plywood_thickness'))

    # Relevant NX Expressions (Mapped)
    nx_panel_height = f"OUT_Front_Panel_Height = if(OUT_Crate_Height - VAR_Front_Top_Offset <= 96) then ... else ..." # Complex conditional logic
    nx_panel_width_side = f"~ OUT_Crate_Length" # Width of side panel is crate length
    nx_panel_width_back = f"~ OUT_Crate_Width"   # Width of back panel is crate width (changed from end)
    nx_cleat_thickness = f"CTRL_Cleat_Thickness"
    nx_panel_thickness = f"CTRL_Panel_Thickness"
    nx_crate_height = f"OUT_Crate_Height = CTRL_Prod_Height + CTRL_Clearance_Top + CTRL_Panel_Thickness + CTRL_Cleat_Thickness + VAR_Skid_Height"


    return f"""
#### {panel_type_label} Calculation Logic:

1.  **Panel Dimensions:**
    * Width (`{'Panel Length' if panel_type_label == 'Side Panel' else 'Panel Width'}`) = **`{panel_width}`** (Matches `{nx_panel_width_side if panel_type_label == 'Side Panel' else nx_panel_width_back}`)
    * Height = **`{panel_height}`**. This is the internal clear height.
        * *Derived from:* `CTRL_Prod_Height` + `CTRL_Clearance_Top`. (These values come from `overall_dims` passed or `ui_inputs`)
        * *NX Ref:* `{nx_panel_height}` (Note: NX has extra conditional logic based on `{nx_crate_height}` which is not implemented here).

2.  **Materials:**
    * Plywood Thickness = `{plywood_thickness}` (*NX Ref:* `{nx_panel_thickness}`)
    * Cleat Size = `{cleat_dims}` (Actual TxW) (*NX Ref:* `{nx_cleat_thickness}` x Width). (Note: Python uses default, NX might vary).

3.  **Cleat Placement:**
    * **Edge Cleats:** Placed along all four edges. Configuration depends on Side/Back type (ref Fig 7-4 in spec 0251-70054).
    * **Intermediate Cleats:** (Simplified Python Logic) A central vertical cleat added if panel width > `{threshold}`. A central horizontal cleat added if panel height > `{threshold}`. (Full spec uses spacing rules, ref Table 7-2).
    * **Plywood Splicing:** If panel width > `{config.PLYWOOD_STD_WIDTH}"` or panel height > `{config.PLYWOOD_STD_HEIGHT}"`, plywood is spliced. Splice cleats are added along join lines.
"""

# --- Top Panel Explanation ---
def get_top_panel_explanation(top_panel_results, ui_inputs):
    """Returns the detailed explanation markdown for the top panel layout, referencing NX expressions."""
    panel_w = format_metric_for_explanation(top_panel_results.get('cap_panel_width'))
    panel_l = format_metric_for_explanation(top_panel_results.get('cap_panel_length'))
    # Use the input value for "Max Spacing" from ui_inputs
    max_spacing_input_val = format_metric_for_explanation(ui_inputs.get('max_top_cleat_spacing'))
    # Also show the value actually used by cap_logic if it differs or for verification
    # max_spacing_used_in_calc = format_metric_for_explanation(top_panel_results.get('max_allowed_cleat_spacing_used'))


    long_cleats = top_panel_results.get("longitudinal_cleats", {})
    trans_cleats = top_panel_results.get("transverse_cleats", {})
    long_spacing = format_metric_for_explanation(long_cleats.get("actual_spacing"))
    trans_spacing = format_metric_for_explanation(trans_cleats.get("actual_spacing"))
    cleat_spec = top_panel_results.get('cap_cleat_spec', {})
    cleat_dims = f"{format_metric_for_explanation(cleat_spec.get('thickness'), decimals=2)}x{format_metric_for_explanation(cleat_spec.get('width'))}"
    plywood_thickness = format_metric_for_explanation(top_panel_results.get('cap_panel_thickness'))


    # Relevant NX Expressions (Mapped)
    nx_panel_width = f"~ OUT_Crate_Width"
    nx_panel_length = f"~ OUT_Crate_Length"
    nx_cleat_thickness = f"CTRL_Cleat_Thickness" # Assumes same as wall cleat thickness
    nx_panel_thickness = f"CTRL_Panel_Thickness"

    return f"""
#### Top Panel Calculation Logic:

1.  **Panel Dimensions:**
    * Width = **`{panel_w}`** (*NX Ref:* `{nx_panel_width}`)
    * Length = **`{panel_l}`** (*NX Ref:* `{nx_panel_length}`)
    * Thickness = **`{plywood_thickness}`** (*NX Ref:* `{nx_panel_thickness}`)

2.  **Cleat Size:** `{cleat_dims}` (Actual TxW) (*NX Ref:* `{nx_cleat_thickness}` x Width).

3.  **Cleat Calculation (Longitudinal - running along Length):**
    * Calculated based on Panel Width (`{panel_w}`) and Max Spacing input (`{max_spacing_input_val}`).
    * Count = `{long_cleats.get("count", "N/A")}`. Actual Spacing (C-C) = `{long_spacing}`.

4.  **Cleat Calculation (Transverse - running along Width):**
    * Calculated based on Panel Length (`{panel_l}`) and Max Spacing input (`{max_spacing_input_val}`).
    * Count = `{trans_cleats.get("count", "N/A")}`. Actual Spacing (C-C) = `{trans_spacing}`.
    * *Rule:* Minimum 2 transverse cleats enforced if panel length allows for two edge cleats.

5.  **Positions:** Cleat centerlines shown relative to the center (0.0) of the panel dimension they span across.
"""