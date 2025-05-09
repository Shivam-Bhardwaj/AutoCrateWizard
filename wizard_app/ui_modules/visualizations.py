# wizard_app/ui_modules/visualizations.py
"""
Handles the generation and display of layout schematics for AutoCrate Wizard.
Provides orthographic views for Base, Wall, and Top assemblies.
Uses centralized styling, coordinate systems, and includes variable annotations.
Charts have fixed range (no zoom/pan by default).
Display functions now primarily generate and return figure objects.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging
import io

try:
    from wizard_app import config
    from wizard_app import explanations
except ImportError:
    try: 
        import config
        import explanations
    except ImportError as e:
        logging.error(f"FATAL: Failed to import config/explanations in visualizations.py: {e}", exc_info=True)
        st.error(f"Code Error: Failed to load critical config/text modules: {e}"); st.stop()

try: 
    import kaleido
    KALEIDO_AVAILABLE = True
except ImportError: 
    KALEIDO_AVAILABLE = False
    logging.info("Kaleido library not found (needed for potential future image export).")

log = logging.getLogger(__name__)

# --- Core Plotting Function (create_schematic_view - unchanged from last working version with fixedrange=True) ---
def create_schematic_view(title, width_hint, height_hint, components=[], annotations=[],
                          xlabel="X (inches)", ylabel="Y (inches)"):
    # ... (exact same implementation as the last working version with fixedrange=True)
    fig = go.Figure()
    legend_items_added = set()
    min_x_data, max_x_data = float('inf'), float('-inf')
    min_y_data, max_y_data = float('inf'), float('-inf')
    found_elements = False
    axis_visibility_offset = 0.1

    for comp in components:
        found_elements = True
        shape_type = comp.get("type", "rect")
        x0, y0 = comp.get("x0", 0), comp.get("y0", 0)
        x1, y1 = comp.get("x1", 0), comp.get("y1", 0)
        fig.add_shape(
            type=shape_type, x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color=comp.get("line_color", config.OUTLINE_COLOR), width=comp.get("line_width", 1), dash=comp.get("line_dash", "solid")),
            fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"),
            opacity=comp.get("opacity", 1.0),
            layer=comp.get("layer", "above"),
            name=comp.get("name", "")
        )
        min_x_data, max_x_data = min(min_x_data, x0, x1), max(max_x_data, x0, x1)
        min_y_data, max_y_data = min(min_y_data, y0, y1), max(max_y_data, y0, y1)
        comp_name = comp.get("name")
        if comp_name and comp_name not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line':
                marker_color = comp.get("line_color", config.OUTLINE_COLOR)
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers', name=comp_name,
                marker=dict(color=marker_color, size=10, symbol=marker_symbol, line=dict(color=comp.get("line_color", config.OUTLINE_COLOR), width=1))
            ))
            legend_items_added.add(comp_name)

    for ann in annotations:
        found_elements = True
        x_pos, y_pos = ann.get("x"), ann.get("y")
        fig.add_annotation(
            x=x_pos, y=y_pos, text=ann.get("text", ""), showarrow=ann.get("showarrow", False),
            font=dict(size=ann.get("size", config.ANNOT_FONT_SIZE_NORMAL), color=ann.get("color", config.COMPONENT_FONT_COLOR_DARK)),
            align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0)"),
            xanchor=ann.get("xanchor", "center"), yanchor=ann.get("yanchor", "middle"),
            yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0)
        )
        text_width_approx = len(ann.get("text", "")) * ann.get("size", 10) * 0.3
        text_height_approx = ann.get("size", 10) * 0.5
        if x_pos is not None:
            min_x_data, max_x_data = min(min_x_data, x_pos - text_width_approx), max(max_x_data, x_pos + text_width_approx)
        if y_pos is not None:
            min_y_data, max_y_data = min(min_y_data, y_pos - text_height_approx), max(max_y_data, y_pos + text_height_approx)

    if not found_elements:
        min_x_data, max_x_data, min_y_data, max_y_data = 0, width_hint, 0, height_hint

    actual_data_width = max(max_x_data - min_x_data, 1.0)
    actual_data_height = max(max_y_data - min_y_data, 1.0)
    plot_min_x = min(min_x_data, 0 - axis_visibility_offset) if min_x_data > -1 else min_x_data
    plot_max_x = max(max_x_data, 0 + axis_visibility_offset) if max_x_data < 1 else max_x_data
    plot_min_y = min(min_y_data, 0 - axis_visibility_offset) if min_y_data > -1 else min_y_data
    plot_max_y = max(max_y_data, 0 + axis_visibility_offset) if max_y_data < 1 else max_y_data
    padding_x = max(actual_data_width * 0.1, 5)
    padding_y = max(actual_data_height * 0.1, 5)
    x_range = [plot_min_x - padding_x, plot_max_x + padding_x]
    y_range = [plot_min_y - padding_y, plot_max_y + padding_y]
    plot_aspect_ratio = actual_data_height / actual_data_width if actual_data_width > 0 else 1
    dynamic_plot_height = max(450, min(800, int(550 * plot_aspect_ratio if plot_aspect_ratio < 1.5 else 550 * 1.5)))

    fig.update_layout(
        title=dict(text=title, font=dict(size=config.TITLE_FONT_SIZE, color=config.COMPONENT_FONT_COLOR_DARK)),
        xaxis=dict(
            range=x_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=config.AXIS_ZERO_LINE_COLOR,
            showticklabels=True, tickfont=dict(size=config.TICK_LABEL_FONT_SIZE, color=config.COMPONENT_FONT_COLOR_DARK),
            visible=True, fixedrange=True,
            title_text=xlabel, title_font=dict(size=config.AXIS_LABEL_FONT_SIZE, color=config.COMPONENT_FONT_COLOR_DARK)
        ),
        yaxis=dict(
            range=y_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=config.AXIS_ZERO_LINE_COLOR,
            showticklabels=True, tickfont=dict(size=config.TICK_LABEL_FONT_SIZE, color=config.COMPONENT_FONT_COLOR_DARK),
            visible=True, fixedrange=True,
            scaleanchor="x", scaleratio=1,
            title_text=ylabel, title_font=dict(size=config.AXIS_LABEL_FONT_SIZE, color=config.COMPONENT_FONT_COLOR_DARK)
        ),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60),
        height=dynamic_plot_height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=config.LEGEND_FONT_COLOR, size=config.LEGEND_FONT_SIZE))
    )
    return fig

# --- Figure CREATION Helper Functions (_create_panel_assembly_figure, _create_base_top_view_fig, etc. - unchanged) ---
# These functions (_create_panel_assembly_figure, _create_base_top_view_fig, 
# _create_base_front_view_fig, _create_base_side_view_fig) remain as they were in the user-provided file.
# They are responsible for defining the components and annotations for each specific view and calling `create_schematic_view`.
def _create_panel_assembly_figure(view_type, panel_data, panel_label_base="Panel"):
    # ... (exact same implementation as in the user-provided file)
    if not panel_data: return None, f"{panel_label_base} {view_type} data invalid."
    is_top_panel="cap_panel_width" in panel_data; plywood_pieces=[];
    if is_top_panel:
        panel_w = panel_data.get("cap_panel_width", 0); panel_h = panel_data.get("cap_panel_length", 0); plywood_t = panel_data.get("cap_panel_thickness", 0); cleat_spec = panel_data.get("cap_cleat_spec", {}); panel_color, cleat_color = config.CAP_PANEL_COLOR_VIZ, config.CAP_CLEAT_COLOR_VIZ
        front_xlabel, front_ylabel = "X (Width) [in]", "Y (Length) [in]"; profile_dimension_label, profile_plot_width = "Panel Length", panel_h; profile_xlabel, profile_ylabel = "Y (Length) [in]", "Z (Thickness) [in]"
        all_cleats_for_front_view = []; lc = panel_data.get("longitudinal_cleats", {}); tc = panel_data.get("transverse_cleats", {})
        if lc.get("count", 0) > 0: [all_cleats_for_front_view.append({"orientation": "vertical", "length": lc.get("cleat_length_each"), "width": lc.get("cleat_width_each"), "thickness": lc.get("cleat_thickness_each"), "position_x": pos_x, "position_y": 0, "type": "longitudinal_cleat"}) for pos_x in lc.get("positions", [])]
        if tc.get("count", 0) > 0: [all_cleats_for_front_view.append({"orientation": "horizontal", "length": tc.get("cleat_length_each"), "width": tc.get("cleat_width_each"), "thickness": tc.get("cleat_thickness_each"), "position_x": 0, "position_y": pos_y, "type": "transverse_cleat"}) for pos_y in tc.get("positions", [])]
        plywood_pieces = [{"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h, "label": "Top Sheathing"}]
    else: # Wall Panel
        panel_w = panel_data.get("panel_width", 0); panel_h = panel_data.get("panel_height", 0); plywood_t = panel_data.get("plywood_thickness", 0); all_cleats_for_front_view = panel_data.get("cleats", []); plywood_pieces_data = panel_data.get("plywood_pieces", []); cleat_spec = panel_data.get("cleat_spec", {}); panel_color, cleat_color = config.WALL_PANEL_COLOR_VIZ, config.WALL_CLEAT_COLOR_VIZ
        front_xlabel, front_ylabel = "X (Width/Length) [in]", "Z (Height) [in]"; profile_dimension_label, profile_plot_width = "Panel Height", panel_h; profile_xlabel, profile_ylabel = "Z (Height) [in]", "Y (Thickness) [in]"
        for p in plywood_pieces_data: plywood_pieces.append({"x0":p["x0"], "y0":p["y0"], "x1":p["x1"], "y1":p["y1"], "label":"Plywood Piece"})
    cleat_actual_thickness = cleat_spec.get("thickness", config.DEFAULT_CLEAT_NOMINAL_THICKNESS); cleat_actual_width = cleat_spec.get("width", config.DEFAULT_CLEAT_NOMINAL_WIDTH)
    if panel_w <= config.FLOAT_TOLERANCE or panel_h <= config.FLOAT_TOLERANCE: return None, f"{panel_label_base} dimensions invalid."
    components, annotations = [], []; fig = None
    if view_type == "Front":
        cleats_added_legend, plywood_added_legend, splice_lines_added_legend = False, False, False
        for i, piece in enumerate(plywood_pieces): components.append({"type": "rect", "x0": piece["x0"], "y0": piece["y0"], "x1": piece["x1"], "y1": piece["y1"], "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "line_width": 0.5, "name": "Plywood" if not plywood_added_legend else "", "layer": "below"}); plywood_added_legend = True
        if not is_top_panel and len(plywood_pieces) > 1:
            distinct_x_boundaries = sorted(list(set([p["x0"] for p in plywood_pieces] + [p["x1"] for p in plywood_pieces])))
            for x_bound in distinct_x_boundaries:
                if config.FLOAT_TOLERANCE < x_bound < panel_w - config.FLOAT_TOLERANCE: 
                    components.append({"type":"line", "x0":x_bound, "y0":0, "x1":x_bound, "y1":panel_h, "line_color":config.AXIS_ZERO_LINE_COLOR, "line_width":1.5, "line_dash":"dash", "name": "Splice Line" if not splice_lines_added_legend else "", "layer":"above"}); splice_lines_added_legend = True; break 
            distinct_y_boundaries = sorted(list(set([p["y0"] for p in plywood_pieces] + [p["y1"] for p in plywood_pieces])))
            for y_bound in distinct_y_boundaries:
                if config.FLOAT_TOLERANCE < y_bound < panel_h - config.FLOAT_TOLERANCE: 
                    components.append({"type":"line", "x0":0, "y0":y_bound, "x1":panel_w, "y1":y_bound, "line_color":config.AXIS_ZERO_LINE_COLOR, "line_width":1.5, "line_dash":"dash", "name": "Splice Line" if not splice_lines_added_legend else "", "layer":"above"}); splice_lines_added_legend = True; break
        for cleat in all_cleats_for_front_view:
            c_orient, c_len, c_rect_width = cleat.get("orientation"), cleat.get("length"), cleat.get("width");
            c_x_rel_center, c_y_rel_center = cleat.get("position_x", 0), cleat.get("position_y", 0);
            abs_center_x = panel_w / 2.0 + c_x_rel_center
            abs_center_y = panel_h / 2.0 + c_y_rel_center
            if c_orient == "horizontal": x0, x1, y0, y1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0, abs_center_y - c_rect_width / 2.0, abs_center_y + c_rect_width / 2.0; text_annot = f'{c_len:.1f}" L'
            elif c_orient == "vertical": x0, x1, y0, y1 = abs_center_x - c_rect_width / 2.0, abs_center_x + c_rect_width / 2.0, abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0; text_annot = f'{c_len:.1f}" H'
            else: continue
            components.append({"type":"rect", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleats" if not cleats_added_legend else "", "layer":"above"}); cleats_added_legend = True
            if c_len > 1.0 and c_rect_width > 1.0 : annotations.append({"x": abs_center_x, "y": abs_center_y, "text": text_annot, "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.CLEAT_FONT_COLOR, "bgcolor": config.ANNOT_BGCOLOR_DARK})
        width_var_name = "crate_overall_width" if (is_top_panel or "BACK" in panel_label_base.upper()) else "crate_overall_length"; height_var_name = "cap_panel_length" if is_top_panel else "panel_height_used"
        annotations.append({"x": panel_w / 2.0, "y": - (panel_h * 0.05), "text": f'{front_xlabel.split(" ")[0]}: {panel_w:.2f}" ({width_var_name})', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})
        annotations.append({"x": - (panel_w * 0.05), "y": panel_h / 2.0, "text": f'{front_ylabel.split(" ")[0]}: {panel_h:.2f}" ({height_var_name})', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center", "xshift":-15})
        fig = create_schematic_view(f"{panel_label_base} - Front View ({'XY' if is_top_panel else 'XZ'} Plane)", panel_w, panel_h, components, annotations, xlabel=front_xlabel, ylabel=front_ylabel)
    elif view_type == "Profile":
        profile_plot_height = plywood_t + cleat_actual_thickness
        components.append({"type": "rect", "x0": 0, "y0": 0, "x1": profile_plot_width, "y1": plywood_t, "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "name": "Plywood Thickness", "layer":"below"})
        representative_cleat_profile_width = cleat_actual_width; cleat_x0 = (profile_plot_width / 2.0) - (representative_cleat_profile_width / 2.0); cleat_x1 = cleat_x0 + representative_cleat_profile_width
        components.append({"type":"rect", "x0": cleat_x0, "y0": plywood_t, "x1": cleat_x1, "y1": plywood_t + cleat_actual_thickness, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleat Thickness"})
        height_var_name = "cap_panel_length" if is_top_panel else "panel_height_used"; profile_dim_var = height_var_name; thickness_ply_var = "cap_panel_thickness" if is_top_panel else "plywood_thickness"; thickness_cleat_var = "cap_cleat_thickness" if is_top_panel else "wall_cleat_thickness"
        annotations.append({"x": profile_plot_width / 2.0, "y": - (profile_plot_height * 0.05), "text": f'{profile_xlabel.split(" ")[0]}: {profile_plot_width:.2f}" ({profile_dim_var})', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})
        annotations.append({"x": - (profile_plot_width * 0.05), "y": profile_plot_height / 2.0, "text": f'{profile_ylabel.split(" ")[0]}: {profile_plot_height:.2f}" ({thickness_ply_var} + {thickness_cleat_var})', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center","xshift":-15})
        annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t / 2.0, "text": f'Plywood: {plywood_t:.2f}" ({thickness_ply_var})', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.COMPONENT_FONT_COLOR_DARK, "xanchor": "center"})
        annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t + cleat_actual_thickness / 2.0, "text": f'Cleat: {cleat_actual_thickness:.2f}" ({thickness_cleat_var})', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.CLEAT_FONT_COLOR, "bgcolor": config.ANNOT_BGCOLOR_DARK, "xanchor": "center"})
        profile_plane = "ZY" if not is_top_panel else "YZ"; fig = create_schematic_view(f"{panel_label_base} - Profile View ({profile_plane} Plane)", profile_plot_width, profile_plot_height, components, annotations, xlabel=profile_xlabel, ylabel=profile_ylabel)
    return fig, None

def _create_base_top_view_fig(skid_results, floor_results, overall_dims, ui_inputs):
    # ... (exact same implementation as in the user-provided file)
    try:
        panel_thickness = ui_inputs.get('panel_thickness', config.DEFAULT_PANEL_THICKNESS_UI); wall_cleat_thickness = ui_inputs.get('wall_cleat_thickness', config.DEFAULT_CLEAT_NOMINAL_THICKNESS); wall_assembly_offset = panel_thickness + wall_cleat_thickness
        skid_w = skid_results.get('skid_width'); skid_x_positions = skid_results.get('skid_positions'); overall_skid_span = overall_dims.get('overall_skid_span')
        all_floorboards = floor_results.get("floorboards", []); fb_center_gap_viz = floor_results.get("center_gap", 0.0); crate_length = overall_dims.get('length')
        if not all([skid_w is not None, skid_x_positions is not None, overall_skid_span is not None, all_floorboards is not None, crate_length is not None]): raise ValueError("Missing dimensions for base top view")
        if not skid_x_positions: raise ValueError("Skid positions are empty.")
        plot_x0_boards = skid_x_positions[0] - skid_w / 2.0; plot_x1_boards = skid_x_positions[-1] + skid_w / 2.0; calculated_span = plot_x1_boards - plot_x0_boards
        if not math.isclose(calculated_span, overall_skid_span, rel_tol=1e-3): overall_skid_span = calculated_span
        components_top, annotations_top = [], []; skid_added_legend, fb_std_added, fb_cust_added, fb_gap_added = False, False, False, False
        for i, x_pos in enumerate(skid_x_positions): x0, x1 = x_pos - skid_w / 2.0, x_pos + skid_w / 2.0; y0, y1 = 0.0, crate_length; components_top.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.SKID_COLOR_VIZ, "opacity": 0.5, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "line_width": 0.5, "name": "Skids" if not skid_added_legend else "", "layer": "below"}); skid_added_legend = True
        current_y_plot = wall_assembly_offset
        for board in all_floorboards:
            board_y_extent = board.get("actual_width", 0.0); plot_y0 = wall_assembly_offset + board.get("position", 0.0); plot_y1 = plot_y0 + board_y_extent; plot_x0, plot_x1 = plot_x0_boards, plot_x1_boards
            nominal, is_custom = board.get("nominal", "N/A"), board.get("nominal") == "Custom"; fill_color = config.FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else config.FLOORBOARD_STD_COLOR_VIZ
            comp_name = "";
            if is_custom and not fb_cust_added: comp_name = "Custom Floorboard"; fb_cust_added = True
            elif not is_custom and not fb_std_added: comp_name = "Standard Floorboards"; fb_std_added = True
            components_top.append({"x0": plot_x0, "y0": plot_y0, "x1": plot_x1, "y1": plot_y1, "fillcolor": fill_color, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": comp_name, "layer": "above"})
            if board_y_extent > 0.5: text_color = config.COMPONENT_FONT_COLOR_DARK; bgcolor = config.ANNOT_BGCOLOR_LIGHT if is_custom else "rgba(0,0,0,0)"; annotations_top.append({"x": 0, "y": (plot_y0 + plot_y1) / 2.0, "text": f'{nominal} ({board_y_extent:.2f}" W)', "size": config.ANNOT_FONT_SIZE_SMALL, "color": text_color, "bgcolor": bgcolor})
            current_y_plot = plot_y1
        end_offset_start_y = crate_length - wall_assembly_offset; actual_gap = end_offset_start_y - current_y_plot
        if abs(fb_center_gap_viz) > config.FLOAT_TOLERANCE:
            gap_start_y_plot, gap_end_y_plot = current_y_plot, current_y_plot + fb_center_gap_viz
            if gap_end_y_plot > gap_start_y_plot + config.FLOAT_TOLERANCE: comp_name_gap = f'Center Gap ({fb_center_gap_viz:.3f}")' if not fb_gap_added else ""; fb_gap_added=True; components_top.append({"x0": plot_x0_boards, "y0": gap_start_y_plot, "x1": plot_x1_boards, "y1": gap_end_y_plot, "fillcolor": config.GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, "name": comp_name_gap, "layer":"above"}); gap_annot_y = (gap_start_y_plot + gap_end_y_plot) / 2.0; annotations_top.append({"x": 0, "y": gap_annot_y, "text": f"Gap\n{fb_center_gap_viz:.3f}\" (center_gap)", "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR, "bgcolor": "rgba(255,255,255,0.0)"})
        annotations_top.append({"x": 0, "y": - (crate_length * 0.05), "text": f'Overall Skid Span (X): {overall_skid_span:.2f}" (overall_skid_span)', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_top.append({"x": plot_x0_boards - abs(plot_x0_boards*0.05) - 5, "y": crate_length / 2.0, "text": f'Crate Len (Y): {crate_length:.2f}" (crate_overall_length)', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center", "xshift":-15})
        annotations_top.append({"x": 0, "y": wall_assembly_offset * 0.75, "text": f'Offset: {wall_assembly_offset:.2f}"', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor":"top"})
        annotations_top.append({"x": 0, "y": crate_length - wall_assembly_offset * 0.75, "text": f'Offset: {wall_assembly_offset:.2f}"', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor":"bottom"})
        fig = create_schematic_view( "Base Assy - Top View (XY Plane)", overall_skid_span, crate_length, components_top, annotations_top, xlabel="X (Width) [in]", ylabel="Y (Length) [in]" )
        return fig
    except Exception as e: log.error("Failed to create Base Top View figure", exc_info=True); return None

def _create_base_front_view_fig(skid_results, floor_results, overall_dims):
    # ... (exact same implementation as in the user-provided file)
    try:
        skid_w = skid_results.get('skid_width'); skid_h = skid_results.get('skid_height'); skid_x_positions = skid_results.get('skid_positions'); overall_skid_span = overall_dims.get('overall_skid_span'); floorboard_thick = config.STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS
        if not all([skid_w is not None, skid_h is not None, skid_x_positions is not None, overall_skid_span is not None]): raise ValueError("Missing dimensions")
        if not skid_x_positions: raise ValueError("Skid positions are empty.")
        plot_x0_boards = skid_x_positions[0] - skid_w / 2.0; plot_x1_boards = skid_x_positions[-1] + skid_w / 2.0; calculated_span = plot_x1_boards - plot_x0_boards
        if not math.isclose(calculated_span, overall_skid_span, rel_tol=1e-3): overall_skid_span = calculated_span
        components_front, annotations_front = [], []; skid_prof_added = False; plot_height_hint_front = skid_h + floorboard_thick + skid_h*0.5
        for x_pos in skid_x_positions: x0, x1 = x_pos - skid_w / 2.0, x_pos + skid_w / 2.0; z0, z1 = 0.0, skid_h; components_front.append({"x0": x0, "y0": z0, "x1": x1, "y1": z1, "fillcolor": config.SKID_COLOR_VIZ, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "name": "Skid Profile" if not skid_prof_added else "", "layer": "below"}); skid_prof_added = True
        fb_x0, fb_x1 = plot_x0_boards, plot_x1_boards; fb_z0, fb_z1 = skid_h, skid_h + floorboard_thick
        components_front.append({"x0": fb_x0, "y0": fb_z0, "x1": fb_x1, "y1": fb_z1, "fillcolor": config.FLOORBOARD_STD_COLOR_VIZ, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": "Floorboard Layer", "layer": "above"})
        annotations_front.append({"x": 0, "y": -plot_height_hint_front*0.1, "text": f'Overall Skid Span (X): {overall_skid_span:.2f}" (overall_skid_span)', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_front.append({"x": plot_x0_boards - abs(plot_x0_boards*0.05) - 5, "y": (skid_h + floorboard_thick) / 2.0, "text": f'Total H (Z): {skid_h + floorboard_thick:.2f}" (skid_h+floor_thick)', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center", "xshift":-15})
        annotations_front.append({"x": 0, "y": skid_h / 2.0, "text": f'Skid H: {skid_h:.2f}" (skid_h)', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.COMPONENT_FONT_COLOR_DARK})
        annotations_front.append({"x": 0, "y": skid_h + floorboard_thick / 2.0, "text": f'Floor T: {floorboard_thick:.3f}" (floor_thick)', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.COMPONENT_FONT_COLOR_DARK})
        fig = create_schematic_view( "Base Assy - Front View (XZ Plane)", overall_skid_span, plot_height_hint_front, components_front, annotations_front, xlabel="X (Width) [in]", ylabel="Z (Height) [in]" )
        return fig
    except Exception as e: log.error("Failed to create Base Front View figure", exc_info=True); return None

def _create_base_side_view_fig(skid_results, floor_results, overall_dims, ui_inputs):
    # ... (exact same implementation as in the user-provided file)
    try:
        panel_thickness = ui_inputs.get('panel_thickness', config.DEFAULT_PANEL_THICKNESS_UI); wall_cleat_thickness = ui_inputs.get('wall_cleat_thickness', config.DEFAULT_CLEAT_NOMINAL_THICKNESS); wall_assembly_offset = panel_thickness + wall_cleat_thickness
        skid_h = skid_results.get('skid_height'); floorboard_thick = config.STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS; floorboard_layout_span = floor_results.get("target_span_along_length"); all_floorboards = floor_results.get("floorboards", []); fb_center_gap_viz = floor_results.get("center_gap", 0.0); crate_length = overall_dims.get('length')
        if not all([skid_h is not None, floorboard_thick is not None, floorboard_layout_span is not None, all_floorboards is not None, crate_length is not None]): raise ValueError("Missing dimensions for base side view")
        components_side, annotations_side = [], []; fb_std_added_side, fb_cust_added_side, fb_gap_added_side = False, False, False; plot_width_hint_side, plot_height_hint_side = crate_length, skid_h + floorboard_thick + skid_h*0.5
        skid_y0, skid_y1 = 0.0, crate_length; skid_z0, skid_z1 = 0.0, skid_h
        components_side.append({"x0": skid_y0, "y0": skid_z0, "x1": skid_y1, "y1": skid_z1, "fillcolor": config.SKID_COLOR_VIZ,"opacity":0.7, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "name": "Skid Profile (Side)", "layer": "below"})
        current_y_plot_side = wall_assembly_offset
        for board in all_floorboards:
            board_y_extent = board.get("actual_width", 0.0); plot_y0 = wall_assembly_offset + board.get("position", 0.0); plot_y1 = plot_y0 + board_y_extent; plot_z0, plot_z1 = skid_h, skid_h + floorboard_thick
            nominal, is_custom = board.get("nominal", "N/A"), board.get("nominal") == "Custom"; fill_color = config.FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else config.FLOORBOARD_STD_COLOR_VIZ
            comp_name = "";
            if is_custom and not fb_cust_added_side: comp_name = "Custom Floorboard"; fb_cust_added_side = True
            elif not is_custom and not fb_std_added_side: comp_name = "Standard Floorboards"; fb_std_added_side = True
            components_side.append({"x0": plot_y0, "y0": plot_z0, "x1": plot_y1, "y1": plot_z1, "fillcolor": fill_color, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": comp_name, "layer": "above"})
            if board_y_extent > 0.5: annotations_side.append({"x": (plot_y0 + plot_y1) / 2.0, "y": (plot_z0 + plot_z1) / 2.0, "text": f'{board_y_extent:.2f}"W', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.COMPONENT_FONT_COLOR_DARK, "bgcolor": config.ANNOT_BGCOLOR_LIGHT if is_custom else "rgba(0,0,0,0)"})
            current_y_plot_side = plot_y1
        end_offset_start_y = crate_length - wall_assembly_offset; actual_gap = end_offset_start_y - current_y_plot_side
        if abs(fb_center_gap_viz) > config.FLOAT_TOLERANCE:
            gap_start_y_plot, gap_end_y_plot = current_y_plot_side, current_y_plot_side + fb_center_gap_viz
            if gap_end_y_plot > gap_start_y_plot + config.FLOAT_TOLERANCE:
                comp_name_gap = f'Gap ({fb_center_gap_viz:.3f}")' if not fb_gap_added_side else ""; fb_gap_added_side=True
                components_side.append({"x0": gap_start_y_plot, "y0": skid_h, "x1": gap_end_y_plot, "y1": skid_h + floorboard_thick, "fillcolor": config.GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, "name": comp_name_gap, "layer":"above"})
                annotations_side.append({"x": (gap_start_y_plot + gap_end_y_plot) / 2.0, "y": skid_h + floorboard_thick / 2.0, "text": f"{fb_center_gap_viz:.3f}\"", "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
        annotations_side.append({"x": crate_length / 2.0, "y": -plot_height_hint_side*0.1, "text": f'Crate Length (Y): {crate_length:.2f}" (crate_overall_length)', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_side.append({"x": -plot_width_hint_side*0.05 - 5, "y": (skid_h + floorboard_thick) / 2.0, "text": f'Total H (Z): {skid_h + floorboard_thick:.2f}"', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center", "xshift":-15})
        annotations_side.append({"x": (wall_assembly_offset + wall_assembly_offset + floorboard_layout_span) / 2.0, "y": skid_h + floorboard_thick + plot_height_hint_side*0.05, "text": f'Floorboard Span: {floorboard_layout_span:.2f}" (target_span_along_length)', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
        annotations_side.append({"x": wall_assembly_offset / 2.0, "y": skid_h + floorboard_thick + plot_height_hint_side*0.05, "text": f'Offset: {wall_assembly_offset:.2f}"', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
        annotations_side.append({"x": crate_length - wall_assembly_offset / 2.0, "y": skid_h + floorboard_thick + plot_height_hint_side*0.05, "text": f'Offset: {wall_assembly_offset:.2f}"', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
        fig = create_schematic_view( "Side View (YZ Plane)", crate_length, plot_height_hint_side, components_side, annotations_side, xlabel="Y (Length) [in]", ylabel="Z (Height) [in]" )
        return fig
    except Exception as e: log.error("Failed to create Base Side View figure", exc_info=True); return None


# --- FIGURE GENERATION Functions (New Structure) ---

def generate_base_assembly_figures(skid_results, floor_results, wall_results, overall_dims, ui_inputs):
    """
    Generates and returns Plotly figure objects for Base Assembly views.
    Does NOT display them.
    """
    fig_top = None
    fig_front = None
    fig_side = None

    skid_status = skid_results.get("status", "UNKNOWN")
    floor_status = floor_results.get("status", "UNKNOWN") if floor_results else "NOT RUN"

    if skid_status != "OK":
        log.warning("Base Assembly figures not generated: Skid status not OK.")
        return None, None, None
    if floor_status not in ["OK", "WARNING"]:
        log.warning(f"Base Assembly figures not generated: Floorboard status not OK/WARNING (is {floor_status}).")
        return None, None, None
    
    try:
        fig_top = _create_base_top_view_fig(skid_results, floor_results, overall_dims, ui_inputs)
        fig_front = _create_base_front_view_fig(skid_results, floor_results, overall_dims)
        fig_side = _create_base_side_view_fig(skid_results, floor_results, overall_dims, ui_inputs)
    except Exception as e:
        log.error(f"Error generating Base Assembly figures: {e}", exc_info=True)
        # Return None for any figures that failed
        if fig_top is None: fig_top = go.Figure() # Return empty figure on error
        if fig_front is None: fig_front = go.Figure()
        if fig_side is None: fig_side = go.Figure()

    return fig_top, fig_front, fig_side


def generate_wall_panel_figures(wall_panel_data, panel_label_base, ui_inputs, overall_dims):
    """
    Generates and returns Plotly figure objects for a single Wall Panel's views.
    Does NOT display them.
    """
    fig_front = None
    fig_profile = None
    assy_label = f"{panel_label_base.upper()} ASSY" # For logging/errors if any

    if not wall_panel_data or wall_panel_data.get("panel_width", 0) == 0:
        log.warning(f"{assy_label} figures not generated: Panel data invalid or width is zero.")
        return None, None # Return tuple of Nones

    try:
        fig_front, error_msg_f = _create_panel_assembly_figure("Front", wall_panel_data, panel_label_base)
        fig_profile, error_msg_p = _create_panel_assembly_figure("Profile", wall_panel_data, panel_label_base)
        
        if error_msg_f: log.warning(f"Error generating Front view for {assy_label}: {error_msg_f}")
        if error_msg_p: log.warning(f"Error generating Profile view for {assy_label}: {error_msg_p}")

    except Exception as e:
        log.error(f"Error generating {assy_label} figures: {e}", exc_info=True)
        if fig_front is None: fig_front = go.Figure() # Return empty figure on error
        if fig_profile is None: fig_profile = go.Figure()

    return fig_front, fig_profile


def generate_top_panel_figures(top_panel_data, ui_inputs, overall_dims):
    """
    Generates and returns Plotly figure objects for the Top Panel Assembly views.
    Does NOT display them.
    """
    fig_front = None
    fig_profile = None
    assy_label = "TOP PANEL ASSY"

    if not top_panel_data or top_panel_data.get("status") not in ["OK", "WARNING"]:
        status_msg = top_panel_data.get('status', 'N/A') if top_panel_data else 'N/A'
        log.warning(f"{assy_label} figures not generated: Data invalid or calculation not successful (Status: {status_msg}).")
        return None, None

    try:
        fig_front, error_msg_f = _create_panel_assembly_figure("Front", top_panel_data, assy_label)
        fig_profile, error_msg_p = _create_panel_assembly_figure("Profile", top_panel_data, assy_label)

        if error_msg_f: log.warning(f"Error generating Front view for {assy_label}: {error_msg_f}")
        if error_msg_p: log.warning(f"Error generating Profile view for {assy_label}: {error_msg_p}")

    except Exception as e:
        log.error(f"Error generating {assy_label} figures: {e}", exc_info=True)
        if fig_front is None: fig_front = go.Figure()
        if fig_profile is None: fig_profile = go.Figure()
        
    return fig_front, fig_profile

# --- Old DISPLAY Functions (can be removed or kept for reference, but app.py will handle display) ---
# def display_base_assembly_views(...):
# def display_wall_assembly(...):
# def display_top_panel_assembly(...):
# These are now effectively handled by app.py, which will call the generate_..._figures functions
# and then use st.plotly_chart with the results stored in session state.