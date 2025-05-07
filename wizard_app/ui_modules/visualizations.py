# wizard_app/ui_modules/visualizations.py
"""
Handles the generation and display of layout schematics.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging

try:
    from wizard_app import config
    from wizard_app import explanations
except ImportError:
    try:
        import config
        import explanations
    except ImportError as e:
        st.error(f"Failed to import config/explanations in visualizations.py: {e}")
        raise

log = logging.getLogger(__name__)

def create_schematic_view(title, width_hint, height_hint, components=[], annotations=[]):
    """
    Creates a schematic view using Plotly shapes with robust manual range calculation
    for reliable autoscaling and 1:1 aspect ratio. Shows coordinate axes.
    width_hint and height_hint are used as fallbacks if no components determine dimensions.
    """
    fig = go.Figure()
    legend_items_added = set()

    min_x_data, max_x_data = float('inf'), float('-inf')
    min_y_data, max_y_data = float('inf'), float('-inf')
    found_elements = False

    # Define a small offset if data is exactly on an axis to ensure visibility
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

        current_min_x = min(x0, x1)
        current_max_x = max(x0, x1)
        current_min_y = min(y0, y1)
        current_max_y = max(y0, y1)

        min_x_data = min(min_x_data, current_min_x)
        max_x_data = max(max_x_data, current_max_x)
        min_y_data = min(min_y_data, current_min_y)
        max_y_data = max(max_y_data, current_max_y)

        comp_name = comp.get("name")
        if comp_name and comp_name not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line':
                marker_color = comp.get("line_color", config.OUTLINE_COLOR)
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers', name=comp_name,
                marker=dict(color=marker_color, size=10, symbol=marker_symbol,
                            line=dict(color=comp.get("line_color", config.OUTLINE_COLOR), width=1))
            ))
            legend_items_added.add(comp_name)

    for ann in annotations:
        found_elements = True
        x_pos, y_pos = ann.get("x"), ann.get("y")
        text_val = ann.get("text", "")
        fig.add_annotation(
            x=x_pos, y=y_pos, text=text_val,
            showarrow=ann.get("showarrow", False),
            font=dict(size=ann.get("size", 10), color=ann.get("color", config.DIM_ANNOT_COLOR)),
            align=ann.get("align", "center"),
            bgcolor=ann.get("bgcolor", "rgba(255,255,255,0.6)"),
            xanchor=ann.get("xanchor", "center"),
            yanchor=ann.get("yanchor", "middle"),
            yshift=ann.get("yshift", 0),
            xshift=ann.get("xshift", 0),
            textangle=ann.get("textangle", 0)
        )
        text_width_approx = len(text_val) * ann.get("size", 10) * 0.3
        text_height_approx = ann.get("size", 10) * 0.5
        if x_pos is not None:
            min_x_data = min(min_x_data, x_pos - text_width_approx + ann.get("xshift", 0))
            max_x_data = max(max_x_data, x_pos + text_width_approx + ann.get("xshift", 0))
        if y_pos is not None:
            min_y_data = min(min_y_data, y_pos - text_height_approx + ann.get("yshift", 0))
            max_y_data = max(max_y_data, y_pos + text_height_approx + ann.get("yshift", 0))

    if not found_elements:
        min_x_data, max_x_data = 0, width_hint
        min_y_data, max_y_data = 0, height_hint
    
    actual_data_width = max_x_data - min_x_data
    actual_data_height = max_y_data - min_y_data

    if abs(actual_data_width) < config.FLOAT_TOLERANCE:
        actual_data_width = max(width_hint if width_hint > 0 else 10, 10) 
        if min_x_data == float('inf'): min_x_data = 0
        max_x_data = min_x_data + actual_data_width
    if abs(actual_data_height) < config.FLOAT_TOLERANCE:
        actual_data_height = max(height_hint if height_hint > 0 else 10, 10)
        if min_y_data == float('inf'): min_y_data = 0
        max_y_data = min_y_data + actual_data_height

    # Ensure origin (0,0) is included in the view if data is near it or positive
    # And provide a little space if all data is far from origin.
    # This helps make the zeroline visible.
    plot_min_x = min(min_x_data, 0 - axis_visibility_offset) if min_x_data > -config.FLOAT_TOLERANCE * 100 else min_x_data
    plot_max_x = max(max_x_data, 0 + axis_visibility_offset) if max_x_data < config.FLOAT_TOLERANCE * 100 else max_x_data
    plot_min_y = min(min_y_data, 0 - axis_visibility_offset) if min_y_data > -config.FLOAT_TOLERANCE * 100 else min_y_data
    plot_max_y = max(max_y_data, 0 + axis_visibility_offset) if max_y_data < config.FLOAT_TOLERANCE * 100 else max_y_data
    
    # If data is very small, ensure a minimum visual range around origin
    if abs(plot_max_x - plot_min_x) < 1.0:
        plot_min_x = min(plot_min_x, -1.0)
        plot_max_x = max(plot_max_x, 1.0)
    if abs(plot_max_y - plot_min_y) < 1.0:
        plot_min_y = min(plot_min_y, -1.0)
        plot_max_y = max(plot_max_y, 1.0)


    padding_x = max((plot_max_x - plot_min_x) * 0.1, 5)
    padding_y = max((plot_max_y - plot_min_y) * 0.1, 5)

    x_range = [plot_min_x - padding_x, plot_max_x + padding_x]
    y_range = [plot_min_y - padding_y, plot_max_y + padding_y]
    
    plot_aspect_ratio = actual_data_height / actual_data_width if actual_data_width > 0 else 1
    dynamic_plot_height = max(400, min(800, int(550 * plot_aspect_ratio if plot_aspect_ratio < 1.5 else 550 * 1.5))) # Slightly increased base height

    fig.update_layout(
        title=title,
        xaxis=dict(
            range=x_range, 
            showgrid=True, gridwidth=1, gridcolor='rgba(230,230,230,0.5)',
            zeroline=True, zerolinewidth=1, zerolinecolor='rgba(150,150,150,0.8)',
            showticklabels=True, tickfont=dict(size=10),
            visible=True, fixedrange=False,
            title_text="X (inches)", title_font=dict(size=12)
        ),
        yaxis=dict(
            range=y_range, 
            showgrid=True, gridwidth=1, gridcolor='rgba(230,230,230,0.5)',
            zeroline=True, zerolinewidth=1, zerolinecolor='rgba(150,150,150,0.8)',
            showticklabels=True, tickfont=dict(size=10),
            visible=True, fixedrange=False,
            scaleanchor="x", scaleratio=1,
            title_text="Y (inches)", title_font=dict(size=12)
        ),
        plot_bgcolor='rgba(255,255,255,0.9)', # Slightly off-white for better axis visibility
        paper_bgcolor='white',
        margin=dict(l=30, r=30, t=60, b=40), # Adjusted margins for axis titles
        height=dynamic_plot_height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=config.LEGEND_FONT_COLOR, size=11))
    )
    return fig

def create_panel_assembly_views(panel_data, panel_label_base="Panel"):
    """Generates Front and Profile schematic views for a single panel assembly."""
    if not panel_data:
        error_msg = f"{panel_label_base} data not valid."
        fig_unavailable = go.Figure(layout=dict(title=f"{panel_label_base} (Data Unavailable)", width=300, height=200))
        fig_unavailable.update_xaxes(visible=True, showticklabels=True, title_text="X")
        fig_unavailable.update_yaxes(visible=True, showticklabels=True, title_text="Y", scaleanchor="x", scaleratio=1)
        return fig_unavailable, fig_unavailable, error_msg

    is_top_panel = "cap_panel_width" in panel_data
    plywood_pieces = []

    if is_top_panel:
        panel_w = panel_data.get("cap_panel_width", 0)
        panel_h = panel_data.get("cap_panel_length", 0)
        plywood_t = panel_data.get("cap_panel_thickness", 0)
        cleat_spec = panel_data.get("cap_cleat_spec", {})
        cleat_actual_thickness = cleat_spec.get("thickness", config.DEFAULT_CLEAT_NOMINAL_THICKNESS)
        cleat_actual_width = cleat_spec.get("width", config.DEFAULT_CLEAT_NOMINAL_WIDTH)
        all_cleats_for_front_view = []
        lc = panel_data.get("longitudinal_cleats", {})
        if lc.get("count", 0) > 0:
            for pos_x in lc.get("positions", []):
                all_cleats_for_front_view.append({
                    "orientation": "vertical", "length": lc.get("cleat_length_each"),
                    "width": lc.get("cleat_width_each"), "thickness": lc.get("cleat_thickness_each"),
                    "position_x": pos_x, "position_y": 0, "type": "longitudinal_cleat"
                })
        tc = panel_data.get("transverse_cleats", {})
        if tc.get("count", 0) > 0:
            for pos_y in tc.get("positions", []):
                all_cleats_for_front_view.append({
                    "orientation": "horizontal", "length": tc.get("cleat_length_each"),
                    "width": tc.get("cleat_width_each"), "thickness": tc.get("cleat_thickness_each"),
                    "position_x": 0, "position_y": pos_y, "type": "transverse_cleat"
                })
        plywood_pieces = [{"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h, "label": "Top Sheathing"}]
        panel_color = config.CAP_PANEL_COLOR_VIZ
        cleat_color = config.CAP_CLEAT_COLOR_VIZ
        profile_dimension_label = "Panel Length"
        profile_plot_width = panel_h
    else: # Wall Panel
        panel_w = panel_data.get("panel_width", 0)
        panel_h = panel_data.get("panel_height", 0)
        plywood_t = panel_data.get("plywood_thickness", 0)
        all_cleats_for_front_view = panel_data.get("cleats", [])
        plywood_pieces_data = panel_data.get("plywood_pieces", [])
        for p in plywood_pieces_data:
             plywood_pieces.append({"x0":p["x0"], "y0":p["y0"], "x1":p["x1"], "y1":p["y1"], "label":"Plywood Piece"})
        cleat_spec = panel_data.get("cleat_spec", {})
        cleat_actual_thickness = cleat_spec.get("thickness", config.DEFAULT_CLEAT_NOMINAL_THICKNESS)
        cleat_actual_width = cleat_spec.get("width", config.DEFAULT_CLEAT_NOMINAL_WIDTH)
        panel_color = config.WALL_PANEL_COLOR_VIZ
        cleat_color = config.WALL_CLEAT_COLOR_VIZ
        profile_dimension_label = "Panel Height"
        profile_plot_width = panel_h

    if panel_w <= config.FLOAT_TOLERANCE or panel_h <= config.FLOAT_TOLERANCE:
        error_msg = f"{panel_label_base} dimensions invalid (W:{panel_w:.2f}, H:{panel_h:.2f})."
        fig_unavailable = go.Figure(layout=dict(title=f"{panel_label_base} (Invalid Dims)", width=300, height=200))
        fig_unavailable.update_xaxes(visible=True, showticklabels=True, title_text="X")
        fig_unavailable.update_yaxes(visible=True, showticklabels=True, title_text="Y", scaleanchor="x", scaleratio=1)
        return fig_unavailable, fig_unavailable, error_msg

    front_components, front_annotations = [], []
    cleats_added_legend, plywood_added_legend, splice_lines_added_legend = False, False, False
    for i, piece in enumerate(plywood_pieces):
        front_components.append({"type": "rect", "x0": piece["x0"], "y0": piece["y0"], "x1": piece["x1"], "y1": piece["y1"], "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "line_width": 0.5, "name": "Plywood" if not plywood_added_legend else "", "layer": "below"})
        if not plywood_added_legend: plywood_added_legend = True
    if not is_top_panel and len(plywood_pieces) > 1:
        if any(math.isclose(p["x1"], config.PLYWOOD_STD_WIDTH) and p["x1"] < panel_w - config.FLOAT_TOLERANCE for p in plywood_pieces) or \
           any(math.isclose(p["x0"], config.PLYWOOD_STD_WIDTH) and p["x0"] > config.FLOAT_TOLERANCE for p in plywood_pieces):
            front_components.append({"type":"line", "x0":config.PLYWOOD_STD_WIDTH, "y0":0, "x1":config.PLYWOOD_STD_WIDTH, "y1":panel_h, "line_color":"#666666", "line_width":1.5, "line_dash":"dash", "name": "Splice Line" if not splice_lines_added_legend else "", "layer":"above"})
            if not splice_lines_added_legend: splice_lines_added_legend = True
        if any(math.isclose(p["y1"], config.PLYWOOD_STD_HEIGHT) and p["y1"] < panel_h - config.FLOAT_TOLERANCE for p in plywood_pieces) or \
           any(math.isclose(p["y0"], config.PLYWOOD_STD_HEIGHT) and p["y0"] > config.FLOAT_TOLERANCE for p in plywood_pieces):
            front_components.append({"type":"line", "x0":0, "y0":config.PLYWOOD_STD_HEIGHT, "x1":panel_w, "y1":config.PLYWOOD_STD_HEIGHT, "line_color":"#666666", "line_width":1.5, "line_dash":"dash", "name": "Splice Line" if not splice_lines_added_legend else "", "layer":"above"})
            if not splice_lines_added_legend: splice_lines_added_legend = True
    for cleat in all_cleats_for_front_view:
        c_orient, c_len, c_rect_width = cleat.get("orientation"), cleat.get("length"), cleat.get("width")
        c_x_rel_center, c_y_rel_center = cleat.get("position_x", 0), cleat.get("position_y", 0)
        abs_center_x, abs_center_y = c_x_rel_center + panel_w / 2.0, c_y_rel_center + panel_h / 2.0
        if c_orient == "horizontal":
            x0, x1, y0, y1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0, abs_center_y - c_rect_width / 2.0, abs_center_y + c_rect_width / 2.0
            text_annot = f'{c_len:.1f}" L'
        elif c_orient == "vertical":
            x0, x1, y0, y1 = abs_center_x - c_rect_width / 2.0, abs_center_x + c_rect_width / 2.0, abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0
            text_annot = f'{c_len:.1f}" H'
        else: continue
        front_components.append({"type":"rect", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleats" if not cleats_added_legend else "", "layer":"above"})
        if not cleats_added_legend: cleats_added_legend = True
        if c_len > 1.0 and c_rect_width > 1.0 :
             front_annotations.append({"x": abs_center_x, "y": abs_center_y, "text": text_annot, "size": 8, "color": config.CLEAT_FONT_COLOR})
    front_annotations.append({"x": panel_w / 2.0, "y": - (panel_h * 0.05), "text": f'Width: {panel_w:.2f}"', "size": 10, "yanchor": "top", "yshift":-5}) # Adjusted yshift
    front_annotations.append({"x": - (panel_w * 0.05), "y": panel_h / 2.0, "text": f'{("Length" if is_top_panel else "Height")}: {panel_h:.2f}"', "size": 10, "textangle": -90, "xanchor": "center", "xshift":-15}) # Adjusted xshift & anchor
    fig_front = create_schematic_view(f"{panel_label_base} - Front View", panel_w, panel_h, front_components, front_annotations)

    profile_components, profile_annotations = [], []
    profile_plot_height = plywood_t + cleat_actual_thickness
    profile_components.append({"type": "rect", "x0": 0, "y0": 0, "x1": profile_plot_width, "y1": plywood_t, "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "name": "Plywood Thickness", "layer":"below"})
    representative_cleat_profile_width = cleat_actual_width
    cleat_x0 = (profile_plot_width / 2.0) - (representative_cleat_profile_width / 2.0)
    cleat_x1 = cleat_x0 + representative_cleat_profile_width
    profile_components.append({"type":"rect", "x0": cleat_x0, "y0": plywood_t, "x1": cleat_x1, "y1": plywood_t + cleat_actual_thickness, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleat Thickness"})
    profile_annotations.append({"x": profile_plot_width / 2.0, "y": - (profile_plot_height * 0.05), "text": f'{profile_dimension_label}: {profile_plot_width:.2f}"', "size": 10, "yanchor": "top", "yshift":-5})
    profile_annotations.append({"x": - (profile_plot_width * 0.05), "y": profile_plot_height / 2.0, "text": f'Total Thickness: {profile_plot_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "center","xshift":-15})
    profile_annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t / 2.0, "text": f'Plywood: {plywood_t:.2f}"', "size": 8, "color": "#333333", "xanchor": "center"})
    profile_annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t + cleat_actual_thickness / 2.0, "text": f'Cleat: {cleat_actual_thickness:.2f}"', "size": 8, "color": config.CLEAT_FONT_COLOR, "bgcolor": "rgba(0,0,0,0.3)", "xanchor": "center"})
    fig_profile = create_schematic_view(f"{panel_label_base} - Profile View", profile_plot_width, profile_plot_height, profile_components, profile_annotations)

    return fig_front, fig_profile, None

# wizard_app/ui_modules/visualizations.py
# ... (keep create_schematic_view and create_panel_assembly_views as modified in previous step) ...

def display_wall_assembly(wall_panel_data, panel_label_base, ui_inputs, overall_dims):
    """Displays Front and Profile views using updated styling and ASSY naming."""
    assy_label = f"{panel_label_base.upper()} ASSY" # e.g., SIDE PANEL ASSY
    st.markdown(f"#### {assy_label}")
    if not wall_panel_data or wall_panel_data.get("panel_width", 0) == 0:
        st.info(f"{assy_label} data not available or panel has zero width.")
        return
    # Pass the base label to the view generator, it adds " - Front View" etc.
    fig_front, fig_profile, error_msg = create_panel_assembly_views(wall_panel_data, assy_label)
    if error_msg: st.warning(error_msg)
    else:
        col1, col2 = st.columns(2)
        with col1: st.plotly_chart(fig_front, use_container_width=True)
        with col2: st.plotly_chart(fig_profile, use_container_width=True)
        with st.expander("Logic Explanation"):
            try:
                # Pass the original base label for explanation lookup if needed
                explanation_text = explanations.get_wall_panel_explanation(panel_data=wall_panel_data, panel_type_label=panel_label_base, overall_dims=overall_dims)
                st.markdown(explanation_text)
            except Exception as e:
                st.warning(f"Could not generate explanation for {panel_label_base}: {e}")
                log.warning(f"Error generating wall explanation for {panel_label_base}", exc_info=True)

def display_top_panel_assembly(top_panel_data, ui_inputs, overall_dims):
    """Displays Front and Profile views using updated styling and ASSY naming."""
    assy_label = "TOP PANEL ASSY"
    st.markdown(f"#### {assy_label}")
    if not top_panel_data or top_panel_data.get("status") not in ["OK", "WARNING"]:
        st.info(f"{assy_label} data not available or not valid. Status: {top_panel_data.get('status', 'N/A') if top_panel_data else 'No Data'}")
        return
    # Pass the base label to the view generator
    fig_front, fig_profile, error_msg = create_panel_assembly_views(top_panel_data, assy_label)
    if error_msg: st.warning(error_msg)
    else:
        col1, col2 = st.columns(2)
        with col1: st.plotly_chart(fig_front, use_container_width=True)
        with col2: st.plotly_chart(fig_profile, use_container_width=True)
        with st.expander("Logic Explanation"):
            try:
                explanation_text = explanations.get_top_panel_explanation(top_panel_results=top_panel_data, ui_inputs=ui_inputs)
                st.markdown(explanation_text)
            except Exception as e:
                st.warning(f"Could not generate explanation for {assy_label}: {e}")
                log.warning(f"Error generating top panel explanation", exc_info=True)

def display_skid_visualization(skid_results, overall_skid_span_metric, ui_inputs):
    """Displays skid schematic using updated styling."""
    # Use a more descriptive title if desired, e.g., "BASE ASSEMBLY - Skids"
    st.subheader("BASE LAYOUT (Skids - Top-Down)")
    # ... (rest of skid visualization logic remains the same, using create_schematic_view) ...
    skid_status = skid_results.get("status", "UNKNOWN")
    skid_plot_generated = False; skid_plot_error = None
    if skid_status == "OK":
        try:
            skid_w_viz = skid_results.get('skid_width'); skid_count_viz = skid_results.get('skid_count')
            positions_viz = skid_results.get('skid_positions'); spacing_viz = skid_results.get('spacing_actual')
            usable_w_skids_viz = skid_results.get('usable_width', 0)
            if (skid_w_viz and skid_count_viz and positions_viz and len(positions_viz) == skid_count_viz and usable_w_skids_viz > 0):
                # ... (component/annotation generation as before) ...
                components, annotations = [], []
                plot_width_hint, plot_height_hint = usable_w_skids_viz, skid_w_viz * 2.5
                skid_y0, skid_y1 = plot_height_hint * 0.4, plot_height_hint * 0.4 + skid_w_viz
                for i, pos_rel_center in enumerate(positions_viz):
                    abs_skid_center_x = pos_rel_center + usable_w_skids_viz / 2.0
                    x0, x1 = abs_skid_center_x - skid_w_viz / 2.0, abs_skid_center_x + skid_w_viz / 2.0
                    components.append({"x0": x0, "y0": skid_y0, "x1": x1, "y1": skid_y1, "fillcolor": config.SKID_COLOR_VIZ, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "name": "Skids" if i == 0 else ""})
                    annotations.append({"x": abs_skid_center_x, "y": skid_y1 + plot_height_hint * 0.05, "text": f"@{pos_rel_center:.2f}\"", "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
                if skid_count_viz > 1 and spacing_viz is not None:
                    for i in range(skid_count_viz - 1):
                        abs_center1, abs_center2 = positions_viz[i] + usable_w_skids_viz / 2.0, positions_viz[i+1] + usable_w_skids_viz / 2.0
                        annotations.append({"x": (abs_center1 + abs_center2) / 2.0, "y": skid_y0 - plot_height_hint * 0.05, "text": f'↔ {spacing_viz:.2f}"', "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR})
                annotations.append({"x": usable_w_skids_viz / 2.0, "y": -plot_height_hint * 0.05, "text": f"Usable Width (for skids): {usable_w_skids_viz:.2f}\"", "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR,"yanchor":"top", "yshift":-5})
                if overall_skid_span_metric:
                    annotations.append({"x": usable_w_skids_viz / 2.0, "y": plot_height_hint * 1.05, "text": f"Overall Skid Span: {overall_skid_span_metric:.2f}\"", "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor":"bottom", "yshift":5})

                # Pass updated title
                skid_fig = create_schematic_view(title="BASE LAYOUT - Skids", width_hint=plot_width_hint, height_hint=plot_height_hint, components=components, annotations=annotations)
                skid_plot_generated = True
            else: skid_plot_error = "Missing/invalid skid data for visualization."
        except Exception as e: skid_plot_error = f"Skid schematic generation error: {e}"; log.error(skid_plot_error, exc_info=True)
    if skid_plot_generated:
        st.plotly_chart(skid_fig, use_container_width=True)
        with st.expander("Logic Explanation (Skids)"):
            try: st.markdown(explanations.get_skid_explanation(skid_results, ui_inputs))
            except Exception as e: st.warning(f"Could not generate explanation for Skids: {e}"); log.warning("Error generating skid explanation", exc_info=True)
    elif skid_plot_error: st.warning(f"⚠️ {skid_plot_error}")
    elif skid_status != "OK": st.info("Base/Skid schematic requires 'OK' skid status.")
    else: st.info("Enter parameters for Base/Skid schematic.")


def display_floorboard_visualization(floor_results, product_length_input, clearance_side_product, ui_inputs):
    """Displays floorboard schematic using updated styling."""
    # Update title if desired, e.g., "FLOOR ASSEMBLY - Floorboards"
    st.divider(); st.subheader("FLOOR LAYOUT (Floorboards - Top-Down)")
    # ... (rest of floorboard visualization logic remains the same, using create_schematic_view) ...
    floorboard_plot_generated = False; floorboard_plot_error = None
    if floor_results and floor_results.get('status') in ["OK", "WARNING"]:
        fb_boards_viz = floor_results.get("floorboards", [])
        fb_target_span_viz = floor_results.get("target_span_along_length", 0.0)
        fb_length_across_skids_viz = floor_results.get("floorboard_length_across_skids", 0.0)
        fb_center_gap_viz = floor_results.get("center_gap", 0.0)
        if fb_target_span_viz > config.FLOAT_TOLERANCE and fb_length_across_skids_viz > config.FLOAT_TOLERANCE :
            try:
                # ... (component/annotation generation as before, using updated config constants) ...
                components, annotations = [], []
                plot_width_hint, plot_height_hint = fb_length_across_skids_viz, fb_target_span_viz
                custom_added, std_added, gap_added = False, False, False
                for i, board in enumerate(fb_boards_viz):
                    board_actual_width_dim, board_start_y_on_plot = board.get("actual_width", 0.0), board.get("position", 0.0)
                    board_end_y_on_plot = board_start_y_on_plot + board_actual_width_dim
                    board_nominal_label, is_custom_board = board.get("nominal", "N/A"), board.get("nominal") == "Custom"
                    board_fill_color = config.FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom_board else config.FLOORBOARD_STD_COLOR_VIZ
                    comp_name_fb = "";
                    if is_custom_board and not custom_added: comp_name_fb = "Custom Board"; custom_added = True
                    elif not is_custom_board and not std_added: comp_name_fb = "Standard Boards"; std_added = True
                    components.append({"x0": 0, "y0": board_start_y_on_plot, "x1": plot_width_hint, "y1": board_end_y_on_plot, "fillcolor": board_fill_color, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": comp_name_fb})
                    if board_actual_width_dim > 0.5:
                        text_color = config.COMPONENT_FONT_COLOR_DARK
                        bgcolor = config.ANNOT_BGCOLOR_LIGHT if is_custom_board else "rgba(0,0,0,0)"
                        annotations.append({"x": plot_width_hint / 2.0, "y": (board_start_y_on_plot + board_end_y_on_plot) / 2.0, "text": f'{board_nominal_label} ({board_actual_width_dim:.2f}" W)', "size": config.ANNOT_FONT_SIZE_SMALL, "color": text_color, "bgcolor": bgcolor})
                if abs(fb_center_gap_viz) > config.FLOAT_TOLERANCE:
                    total_board_material_height = floor_results.get("total_board_width", 0.0)
                    gap_start_y_plot, gap_end_y_plot = total_board_material_height, total_board_material_height + fb_center_gap_viz
                    if gap_end_y_plot > gap_start_y_plot + config.FLOAT_TOLERANCE:
                        comp_name_gap = f'Center Gap ({fb_center_gap_viz:.3f}")' if not gap_added else ""; gap_added=True
                        components.append({"x0": 0, "y0": gap_start_y_plot, "x1": plot_width_hint, "y1": gap_end_y_plot, "fillcolor": config.GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, "name": comp_name_gap})
                        annotations.append({"x": plot_width_hint / 2.0, "y": (gap_start_y_plot + gap_end_y_plot) / 2.0, "text": f"Gap\n{fb_center_gap_viz:.3f}\"", "size": config.ANNOT_FONT_SIZE_SMALL, "color": config.DIM_ANNOT_COLOR, "bgcolor": "rgba(255,255,255,0.0)"})
                annotations.append({"x": - (plot_width_hint * 0.05), "y": plot_height_hint / 2.0, "text": f'Target Span: {plot_height_hint:.2f}"', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "textangle": -90, "xanchor": "center", "xshift":-15})
                annotations.append({"x": plot_width_hint / 2.0, "y": - (plot_height_hint * 0.05), "text": f'Board Length: {plot_width_hint:.2f}"', "size": config.ANNOT_FONT_SIZE_NORMAL, "color": config.DIM_ANNOT_COLOR, "yanchor": "top", "yshift":-5})

                # Pass updated title
                fb_fig = create_schematic_view(title=f"FLOOR LAYOUT - Floorboards", width_hint=plot_width_hint, height_hint=plot_height_hint, components=components, annotations=annotations)
                floorboard_plot_generated = True
            except Exception as e: floorboard_plot_error = f"Floorboard schematic generation error: {e}"; log.error(floorboard_plot_error, exc_info=True)
        if floorboard_plot_generated:
            st.plotly_chart(fb_fig, use_container_width=True)
            with st.expander("Logic Explanation (Floorboards)"):
                try: st.markdown(explanations.get_floorboard_explanation(floor_results, ui_inputs))
                except Exception as e: st.warning(f"Could not generate explanation for Floorboards: {e}"); log.warning("Error generating floorboard explanation", exc_info=True)
        elif floorboard_plot_error: st.warning(f"⚠️ {floorboard_plot_error}")
        elif not fb_boards_viz and fb_target_span_viz > config.FLOAT_TOLERANCE : st.info("No floorboards were placed for a non-zero target span.")
        elif fb_target_span_viz <= config.FLOAT_TOLERANCE or fb_length_across_skids_viz <= config.FLOAT_TOLERANCE: st.info("Floorboard schematic requires valid positive dimensions for target span and board length.")
    elif floor_results: st.info(f"No Floorboard layout to display: {floor_results.get('message', 'Status: '+floor_results.get('status','N/A'))}")