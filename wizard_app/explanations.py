# wizard_app/explanations.py
"""
Contains explanation text for the AutoCrate Wizard UI.
Version 0.4.14
"""
import math
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

def get_skid_explanation(skid_results, product_weight):
    """Returns the explanation markdown for the skid layout."""
    skid_type = skid_results.get('skid_type', 'N/A')
    max_spacing = format_metric_for_explanation(skid_results.get('max_spacing'))
    crate_width = format_metric_for_explanation(skid_results.get('crate_width'))
    usable_width = format_metric_for_explanation(skid_results.get('usable_width'))
    actual_spacing = format_metric_for_explanation(skid_results.get('spacing_actual'))
    skid_count = skid_results.get('skid_count', 0)

    return f"""
- **Skid Type Selection:** Based on Product Weight (`{product_weight:.1f} lbs`). Rule applied: `{skid_type}` with max C-C spacing of `{max_spacing}` (ref Table 5-3, 5-4).
- **Usable Width:** Calculated as Crate Overall Width (`{crate_width}`) minus 2 * (Panel Thickness + Wall Cleat Thickness). This represents the space *between the inner faces of the wall cleats* where skids are typically placed. Result: `{usable_width}`.
- **Skid Count & Spacing:**
    - If Usable Width < Skid Width: Error.
    - If Usable Width < 2 * Skid Width: Count = 1.
    - Otherwise: Minimum count is 2. The count is increased until the calculated center-to-center spacing (`{actual_spacing}`) is less than or equal to the maximum allowed (`{max_spacing}`).
    - Final Count: `{skid_count}`.
- **Positions:** Show the centerline position of each skid relative to the center (0.0) of the Usable Width. Skids are distributed symmetrically.
"""

def get_floorboard_explanation(floor_results, product_length, clearance_side):
    """Returns the explanation markdown for the floorboard layout."""
    target_span = format_metric_for_explanation(floor_results.get('target_span_along_length'))
    board_length = format_metric_for_explanation(floor_results.get('floorboard_length_across_skids'))
    placement_method = floor_results.get("placement_method", "N/A")
    gap = format_metric_for_explanation(floor_results.get('center_gap'), decimals=3)
    custom_used = floor_results.get("narrow_board_used")
    custom_width = format_metric_for_explanation(floor_results.get("custom_board_width"), decimals=3)
    min_custom = format_metric_for_explanation(config.MIN_CUSTOM_NARROW_WIDTH)
    max_custom = format_metric_for_explanation(config.MAX_CUSTOM_NARROW_WIDTH)

    return f"""
- **Target Span (Layout Height):** Calculated as Product Length (`{format_metric_for_explanation(product_length)}`) + 2 * Side Clearance (`{format_metric_for_explanation(clearance_side)}`) = `{target_span}`.
- **Board Length (Layout Width):** Equal to the Overall Skid Span (`{board_length}`).
- **Placement Method:** `{placement_method}`.
- **Logic (Simplified):**
    1. Place widest available standard boards symmetrically from edges inwards until pairs no longer fit.
    2. Calculate remaining center span.
    3. Determine best *single* initial board (standard or custom if allowed & fits min width `{min_custom}`) to place in the center to minimize the gap.
    4. Place initial board. Calculate gap after initial board.
    5. *If* custom narrow boards are allowed, *and* the initial board was *not* custom, *and* the gap after the initial board is >= `{min_custom}`, place a *second* custom board (width = min(gap, `{max_custom}`)).
    6. Calculate final center gap.
- **Result:** Final calculated gap is `{gap}`. Custom board used: `{'Yes (' + custom_width + ')' if custom_used else 'No'}`.
"""

def get_wall_panel_explanation(panel_data, panel_type_label):
    """Returns the explanation markdown for a wall panel layout."""
    panel_width = format_metric_for_explanation(panel_data.get('panel_width'))
    panel_height = format_metric_for_explanation(panel_data.get('panel_height'))
    threshold = format_metric_for_explanation(config.INTERMEDIATE_CLEAT_THRESHOLD)
    cleat_spec = panel_data.get('cleat_spec', {})
    cleat_dims = f"{format_metric_for_explanation(cleat_spec.get('thickness'), decimals=2)}x{format_metric_for_explanation(cleat_spec.get('width'))}"

    return f"""
- **Dimensions:** Width = `{panel_width}`, Height = `{panel_height}` (based on Product Height + Clearance Above Product).
- **Cleat Size:** `{cleat_dims}` (Actual TxW). Size may vary based on panel area in full spec (ref Table 7-1).
- **Edge Cleats:** Placed along all four edges. Configuration depends on whether it's a Side or End panel (ref Fig 7-4).
- **Intermediate Cleats:** (Simplified Logic) A central vertical cleat is added if panel width > `{threshold}`. A central horizontal cleat is added if panel height > `{threshold}`. (Full spec uses spacing rules, ref Table 7-2).
"""

def get_top_panel_explanation(top_panel_results, max_spacing_input):
    """Returns the explanation markdown for the top panel layout."""
    panel_w = format_metric_for_explanation(top_panel_results.get('cap_panel_width'))
    panel_l = format_metric_for_explanation(top_panel_results.get('cap_panel_length'))
    max_spacing = format_metric_for_explanation(max_spacing_input)
    long_cleats = top_panel_results.get("longitudinal_cleats", {})
    trans_cleats = top_panel_results.get("transverse_cleats", {})
    long_spacing = format_metric_for_explanation(long_cleats.get("actual_spacing"))
    trans_spacing = format_metric_for_explanation(trans_cleats.get("actual_spacing"))
    cleat_spec = top_panel_results.get('cap_cleat_spec', {})
    cleat_dims = f"{format_metric_for_explanation(cleat_spec.get('thickness'), decimals=2)}x{format_metric_for_explanation(cleat_spec.get('width'))}"

    return f"""
- **Panel Dimensions:** Width = Crate Overall Width (`{panel_w}`), Length = Crate Overall Length (`{panel_l}`).
- **Cleat Size:** `{cleat_dims}` (Actual TxW).
- **Cleat Calculation:** Longitudinal (run along Length) and Transverse (run along Width) cleats are calculated based on the panel dimension they span across and the Max Top Panel Cleat Spacing input (`{max_spacing}`).
- **Cleat Count:** Minimum of 1 (if dimension allows) or 2 (if dimension allows > 2x cleat width). Otherwise, count is determined to ensure spacing is <= max allowed (`ceil(centerline_span / max_spacing) + 1`).
- **Transverse Cleat Rule:** A minimum of 2 transverse cleats are enforced if the panel length allows.
- **Spacing:** Calculated C-C spacing for Longitudinal: `{long_spacing}`, Transverse: `{trans_spacing}`.
- **Positions:** Cleat positions in the schematic are relative to the center (0.0) of the panel dimension they span.
"""
