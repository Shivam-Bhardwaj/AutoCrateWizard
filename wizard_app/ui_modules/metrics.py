# wizard_app/ui_modules/metrics.py
# MODIFIED: Removed HTML styling for labels to ensure readability.
"""
Handles the display of summary metrics.
Organized and more compact display of detailed metrics.
HTML formatting for NX-style labels has been removed to address rendering issues.
"""
import streamlit as st
import math
# Assuming config.py might be used for constants or other settings.
from wizard_app import config # It's good practice to import config if used, even if indirectly
# Assuming floorboard_logic might be used for specific calculations if uncommented.
from wizard_app import floorboard_logic

def _simple_format(val, dec=2, unit=""):
    if val is None: return "N/A"
    try:
        if isinstance(val, str): return val
        return f"{val:.{dec}f}{unit}"
    except: return str(val)

def format_metric_plain_line(nx_var_name, value, unit="\"", decimals=2, default="N/A", help_text=""):
    """Formats a single metric line as plain text: LABEL: Value."""
    val_str = default
    if value is not None :
        if isinstance(value, str):
            val_str = value
        elif isinstance(value, (int, float)) and math.isfinite(value):
            try:
                if unit == "\"" and abs(value - round(value)) < (10**(-decimals -1)):
                    val_str = f"{int(round(value))}{unit}"
                elif unit == "" and abs(value - round(value)) < (10**(-decimals -1)) and decimals == 0 :
                     val_str = f"{int(round(value))}{unit}"
                else:
                    val_str = f"{value:.{decimals}f}{unit}"
            except (TypeError, ValueError):
                val_str = str(value)
        else:
            val_str = str(value)
            unit = "" # No unit for non-numeric typically

    return f"{nx_var_name}: {val_str}"


def display_metrics(skid_results, floor_results, wall_results, top_panel_results, overall_dims):
    """Displays the summary metrics in columns using plain text labels."""

    if not overall_dims:
        st.caption("Overall dimensions not available for metrics display.")
        return

    main_col1, main_col2, main_col3 = st.columns(3)

    with main_col1:
        st.markdown(f"**GROUP_Crate_Overall**") # Plain bold markdown
        st.markdown(format_metric_plain_line("OUT_Crate_Width_OD", overall_dims.get('width'), help_text="Overall Crate Width (Outer Dimension)"))
        st.markdown(format_metric_plain_line("OUT_Crate_Length_OD", overall_dims.get('length'), help_text="Overall Crate Length (Outer Dimension)"))
        st.markdown(format_metric_plain_line("OUT_Crate_Height_OD", overall_dims.get('height'), help_text="Overall Crate Height (Outer Dimension)"))
        st.markdown(format_metric_plain_line("ATTR_Panel_Thickness_Used", overall_dims.get('panel_thickness'), decimals=3, help_text="Panel Thickness used"))

        st.markdown("<br>", unsafe_allow_html=True) # Keep <br> if you want the space

        st.markdown(f"**GROUP_Base_Skid_Setup**")
        if skid_results:
            st.markdown(format_metric_plain_line("VAR_Skid_Type", skid_results.get('skid_type', 'N/A'), unit="", help_text="Skid Lumber Type"))
            skid_w_val = skid_results.get('skid_width')
            skid_h_val = skid_results.get('skid_height')
            skid_dims_str = f"{_simple_format(skid_w_val)}x{_simple_format(skid_h_val)}\"" if skid_w_val and skid_h_val else "N/A"
            st.markdown(format_metric_plain_line("ATTR_Skid_Actual_WxH", skid_dims_str, unit="", help_text="Skid Actual WxH"))
            st.markdown(format_metric_plain_line("VAR_Skid_Count", skid_results.get('skid_count'), unit="", decimals=0, help_text="Number of Skids"))

            spacing_actual_metric = skid_results.get('spacing_actual')
            skid_count_metric = skid_results.get('skid_count')
            spacing_val_for_format = _simple_format(spacing_actual_metric, dec=2) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"
            st.markdown(format_metric_plain_line("VAR_Skid_Spacing_Actual_CC", spacing_val_for_format, unit="\"", help_text="Skid Spacing (C-C)"))

            st.markdown(format_metric_plain_line("RULE_Max_Skid_Spacing", skid_results.get('max_spacing'), help_text="Max Allowed Skid Spacing"))
            st.markdown(format_metric_plain_line("VAR_Overall_Skid_Span", overall_dims.get('overall_skid_span'), help_text="Overall Skid Span"))
        else:
            st.caption("Skid data not available.")

    with main_col2:
        st.markdown(f"**GROUP_Floorboard_Summary**")
        if floor_results and floor_results.get('status') not in ["NOT FOUND", "INPUT ERROR", "CRITICAL ERROR", "SKIPPED"]:
            fb_boards = floor_results.get("floorboards", [])
            st.markdown(format_metric_plain_line("VAR_Floor_Total_Boards", len(fb_boards) if fb_boards else 0, unit="", decimals=0, help_text="Total floorboards"))
            st.markdown(format_metric_plain_line("DIM_Floorboard_Length", floor_results.get("floorboard_length_across_skids"), help_text="Floorboard Length"))
            st.markdown(format_metric_plain_line("VAR_Floor_Target_Layout_Span", floor_results.get("target_span_along_length"), help_text="Floorboard Target Span"))

            gap_val = floor_results.get("center_gap")
            gap_disp_val_str = f"⚠️ {gap_val:.3f}" if floor_results.get("status") == "WARNING" and isinstance(gap_val, (int,float)) else _simple_format(gap_val, dec=3)
            unit_for_gap = "\"" if isinstance(gap_val, (int,float)) and floor_results.get("status") != "WARNING" else ""
            if floor_results.get("status") == "WARNING" and isinstance(gap_val, (int,float)) : unit_for_gap = "\""
            st.markdown(format_metric_plain_line("VAR_Floor_Center_Gap", gap_disp_val_str, unit=unit_for_gap, decimals=3, help_text="Center gap"))

            custom_board_width_val = floor_results.get("custom_board_width")
            custom_width_disp_str = _simple_format(custom_board_width_val, dec=3) if floor_results.get("narrow_board_used") and custom_board_width_val is not None else "Not Used"
            st.markdown(format_metric_plain_line("ATTR_Floor_Custom_Board_Width", custom_width_disp_str, unit="\"" if isinstance(custom_board_width_val, (int,float)) and floor_results.get("narrow_board_used") else "", decimals=3, help_text="Custom board width"))

            fb_board_counts = floor_results.get("board_counts", {})
            # For counts, we can make the nominal size bold, but not full NX style easily without HTML
            counts_str_list = [f"**{nom}**: {cnt}" for nom, cnt in sorted(fb_board_counts.items())]
            st.markdown(f"**Counts:** {', '.join(counts_str_list) if counts_str_list else 'None'}")

            fb_calc_span = floor_results.get("calculated_span_covered")
            fb_target_span_check = floor_results.get("target_span_along_length")
            if fb_calc_span is not None and fb_target_span_check is not None:
                local_float_tolerance = getattr(config, 'FLOAT_TOLERANCE', 1e-6)
                if math.isclose(fb_calc_span, fb_target_span_check, abs_tol=local_float_tolerance * 10):
                    st.markdown(f"**CHECK_Floor_Span**: ✅ OK")
                else:
                    st.markdown(f"**CHECK_Floor_Span**: ❌ FAIL (Calc: {fb_calc_span:.3f}\" vs Target: {fb_target_span_check:.3f}\")")
        else:
            st.caption("Floorboard data not available.")

    with main_col3:
        st.markdown(f"**GROUP_Wall_Panel_Summary**")
        if wall_results and wall_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
            st.markdown(format_metric_plain_line("DIM_Wall_Panel_Height_Used", wall_results.get("panel_height_used"), help_text="Wall panel height"))
            st.markdown(format_metric_plain_line("ATTR_Wall_Plywood_Thickness", wall_results.get("panel_plywood_thickness_used"), decimals=3, help_text="Wall plywood thickness"))

            ws = wall_results.get("wall_cleat_spec", {})
            wall_cleat_thick_val = ws.get('thickness')
            wall_cleat_width_val = ws.get('width')
            cleat_spec_disp_w = f"{_simple_format(wall_cleat_thick_val)}x{_simple_format(wall_cleat_width_val)}\" (act.)" if ws else "N/A"
            st.markdown(format_metric_plain_line("ATTR_Wall_Cleat_Lumber_Spec", cleat_spec_disp_w, unit="", help_text="Wall Cleat TxW"))

            side_panel_cleats = wall_results.get("side_panels", [{}])[0].get("cleats", [])
            back_panel_cleats = wall_results.get("back_panels", [{}])[0].get("cleats", [])
            st.markdown(format_metric_plain_line("COUNT_Side_Panel_Cleats_Each", len(side_panel_cleats), unit="", decimals=0, help_text="Cleats/Side Panel"))
            st.markdown(format_metric_plain_line("COUNT_Back_Panel_Cleats_Each", len(back_panel_cleats), unit="", decimals=0, help_text="Cleats/Back Panel"))
            st.markdown(format_metric_plain_line("COUNT_Total_Wall_Cleats", len(side_panel_cleats) * 2 + len(back_panel_cleats) * 2, unit="", decimals=0, help_text="Total wall cleats"))
        else:
            st.caption("Wall panel data not available.")

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(f"**GROUP_Cap_Panel_Summary**")
        if top_panel_results and top_panel_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
            cap_w = top_panel_results.get('cap_panel_width')
            cap_l = top_panel_results.get('cap_panel_length')
            cap_dims_str = f"{_simple_format(cap_w)}W x {_simple_format(cap_l)}L" if cap_w and cap_l else "N/A"
            st.markdown(format_metric_plain_line("DIM_Cap_Panel_WxL", cap_dims_str, unit="", help_text="Cap Panel WxL")) # Unit is in the string
            st.markdown(format_metric_plain_line("ATTR_Cap_Panel_Thickness", top_panel_results.get("cap_panel_thickness"), decimals=3, help_text="Cap panel thickness"))

            cs = top_panel_results.get("cap_cleat_spec", {})
            cap_cleat_thick_val = cs.get('thickness')
            cap_cleat_width_val = cs.get('width')
            cleat_spec_disp_c = f"{_simple_format(cap_cleat_thick_val)}x{_simple_format(cap_cleat_width_val)}\" (act.)" if cs else "N/A"
            st.markdown(format_metric_plain_line("ATTR_Cap_Cleat_Lumber_Spec", cleat_spec_disp_c, unit="", help_text="Top Cleat Lumber TxW"))

            lc = top_panel_results.get("longitudinal_cleats", {})
            tc = top_panel_results.get("transverse_cleats", {})
            st.markdown(format_metric_plain_line("COUNT_Cap_Long_Cleats", lc.get("count", "N/A"), unit="", decimals=0, help_text="Long. Cap Cleats"))
            st.markdown(format_metric_plain_line("VAR_Cap_Long_Cleat_Spacing_CC", lc.get("actual_spacing"), help_text="Long. Cleat Spacing"))
            st.markdown(format_metric_plain_line("COUNT_Cap_Trans_Cleats", tc.get("count", "N/A"), unit="", decimals=0, help_text="Trans. Cap Cleats"))
            st.markdown(format_metric_plain_line("VAR_Cap_Trans_Cleat_Spacing_CC", tc.get("actual_spacing"), help_text="Trans. Cleat Spacing"))
            st.markdown(format_metric_plain_line("RULE_Max_Cap_Cleat_Spacing_Used", top_panel_results.get("max_allowed_cleat_spacing_used"), help_text="Max Cap Cleat Spacing Rule"))
        else:
            st.caption("Top panel data not available.")