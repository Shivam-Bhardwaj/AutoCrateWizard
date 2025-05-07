# wizard_app/ui_modules/metrics.py
"""
Handles the display of summary metrics.
"""
import streamlit as st
import math
from wizard_app import config # Use absolute import
from wizard_app import floorboard_logic # Import floorboard logic for helper

def format_metric(value, unit="\"", decimals=2, default="N/A"):
    """Helper to format metric values consistently."""
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(value): return default
    try: return f"{value:.{0 if abs(value - round(value)) < config.FLOAT_TOLERANCE else decimals}f}{unit}"
    except (TypeError, ValueError): return str(value)

def display_metrics(skid_results, floor_results, wall_results, top_panel_results, overall_dims):
    """Displays the summary metrics in columns."""
    st.divider()
    st.subheader("📈 Summary Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)

    # Column 1: Crate Overall
    with col1:
        st.markdown("##### 📦 Crate Overall")
        st.metric("Overall Width (OD)", format_metric(overall_dims['width']))
        st.metric("Overall Length (OD)", format_metric(overall_dims['length']))
        st.metric("Overall Height (OD)", format_metric(overall_dims['height']))
        st.metric("Panel Thickness Used", format_metric(overall_dims['panel_thickness']))

    # Column 2: Base/Skid
    with col2:
        st.markdown("##### 🔩 Base/Skid Setup")
        skid_status = skid_results.get("status", "UNKNOWN")
        st.metric("Skid Type", skid_results.get('skid_type', 'N/A'))
        st.metric("Skid Actual W x H", f"{format_metric(skid_results.get('skid_width'))} x {format_metric(skid_results.get('skid_height'))}")
        skid_count_metric = skid_results.get('skid_count'); st.metric("Skid Count", str(skid_count_metric) if skid_count_metric is not None else "N/A")
        spacing_actual_metric = skid_results.get('spacing_actual'); spacing_display = format_metric(spacing_actual_metric) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"; st.metric("Actual Spacing (C-C)", spacing_display)
        st.metric("Max Allowed Spacing", format_metric(skid_results.get('max_spacing')))

        overall_skid_span_metric = None
        if skid_status == "OK":
            if hasattr(floorboard_logic, 'calculate_overall_skid_span'):
                overall_skid_span_metric = floorboard_logic.calculate_overall_skid_span(skid_results)
            else: # Fallback calculation
                skid_w_m = skid_results.get('skid_width'); pos_m = skid_results.get('skid_positions', []); skid_c_m = skid_results.get('skid_count')
                if skid_c_m == 1 and skid_w_m is not None: overall_skid_span_metric = skid_w_m
                elif skid_c_m is not None and skid_c_m > 1 and pos_m and skid_w_m is not None and len(pos_m) == skid_c_m: overall_skid_span_metric = abs((pos_m[-1] + skid_w_m / 2.0) - (pos_m[0] - skid_w_m / 2.0))
        st.metric("Overall Skid Span", format_metric(overall_skid_span_metric), help="Outer edge to outer edge of skids.")

    # Column 3: Floorboard
    with col3:
        st.markdown("##### 🪵 Floorboard Summary")
        if floor_results and floor_results.get('status') not in ["NOT FOUND", "INPUT ERROR", "CRITICAL ERROR", "SKIPPED"]:
            fb_boards = floor_results.get("floorboards", []); fb_board_counts = floor_results.get("board_counts", {}); st.metric("Total Boards", len(fb_boards) if fb_boards else "N/A"); st.metric("Board Length", format_metric(floor_results.get("floorboard_length_across_skids")), help="= Overall Skid Span"); st.metric("Target Span (Layout)", format_metric(floor_results.get("target_span_along_length")), help="Product Length + 2x Clearance Side")
            gap_val = floor_results.get("center_gap"); gap_disp = f"⚠️ {gap_val:.3f}\"" if floor_results.get("status") == "WARNING" and gap_val is not None else format_metric(gap_val, decimals=3); st.metric("Center Gap", gap_disp); st.metric("Custom Narrow Used", format_metric(floor_results.get("custom_board_width"), decimals=3) if floor_results.get("narrow_board_used") else "Not Used")
            counts_str = ", ".join([f"{nom}: {cnt}" for nom, cnt in sorted(fb_board_counts.items())]); st.markdown(f"**Counts:** {counts_str if counts_str else 'None'}")
            fb_calc_span = floor_results.get("calculated_span_covered"); fb_target_span_check = floor_results.get("target_span_along_length");
            if fb_calc_span is not None and fb_target_span_check is not None:
                if math.isclose(fb_calc_span, fb_target_span_check, abs_tol=config.FLOAT_TOLERANCE * 10): st.success(f"Span Check: OK")
                else: st.error(f"Span Check FAIL: Calc={fb_calc_span:.3f}\" vs Target={fb_target_span_check:.3f}\"")
            else: st.caption("Span Check Pending")
        else: st.caption("No floorboard data.")

    # Column 4: Wall Panel
    with col4:
        st.markdown("##### 🧱 Wall Panel Summary")
        if wall_results and wall_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
            st.metric("Panel Height Used", format_metric(wall_results.get("panel_height_used"))); st.metric("Plywood Thickness", format_metric(wall_results.get("panel_plywood_thickness_used")))
            ws = wall_results.get("wall_cleat_spec", {}); cleat_spec_disp_w = f"{ws.get('thickness', 'N/A'):.2f}x{ws.get('width', 'N/A'):.2f}\" (act.)"; st.metric("Wall Cleat Lumber Spec", cleat_spec_disp_w)
            side_panel_data = wall_results.get("side_panels", [{}])[0]; end_panel_data = wall_results.get("end_panels", [{}])[0]; side_cleat_count = len(side_panel_data.get("cleats", [])); end_cleat_count = len(end_panel_data.get("cleats", [])); st.metric("Side Panel Cleats (ea)", str(side_cleat_count)); st.metric("End Panel Cleats (ea)", str(end_cleat_count)); st.metric("Total Wall Cleats", str(side_cleat_count * 2 + end_cleat_count * 2))
        else: st.caption("No wall panel data.")

    # Column 5: Top Panel
    with col5:
        st.markdown("##### 🧢 Top Panel Summary")
        if top_panel_results and top_panel_results.get('status') not in ["NOT FOUND", "CRITICAL ERROR", "SKIPPED"]:
            st.metric("Panel W x L", f"{format_metric(top_panel_results.get('cap_panel_width'))} x {format_metric(top_panel_results.get('cap_panel_length'))}"); st.metric("Panel Thickness", format_metric(top_panel_results.get("cap_panel_thickness")))
            lc = top_panel_results.get("longitudinal_cleats", {}); tc = top_panel_results.get("transverse_cleats", {}); cs = top_panel_results.get("cap_cleat_spec", {}); cleat_spec_disp_c = f"{cs.get('thickness', 'N/A'):.2f}x{cs.get('width', 'N/A'):.2f}\" (act.)"; st.metric("Top Cleat Lumber Spec", cleat_spec_disp_c)
            st.metric("Long. Cleats (Count)", str(lc.get("count", "N/A"))); st.metric("Long. Spacing (C-C)", format_metric(lc.get("actual_spacing"))); st.metric("Trans. Cleats (Count)", str(tc.get("count", "N/A"))); st.metric("Trans. Spacing (C-C)", format_metric(tc.get("actual_spacing"))); st.metric("Max Cleat Spacing Used", format_metric(top_panel_results.get("max_allowed_cleat_spacing_used")))
        else: st.caption("No top panel data.")

