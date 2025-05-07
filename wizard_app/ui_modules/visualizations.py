# wizard_app/ui_modules/visualizations.py
"""
Handles the generation and display of layout schematics.
Version 0.4.19 - Fixed AttributeError in wall panel visualization display.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging
try:
    from wizard_app import config
    from wizard_app import explanations
except ImportError:
    import config
    import explanations
try:
    from wizard_app import config
    from wizard_app import explanations
except ImportError:
    import config
    import explanations

log = logging.getLogger(__name__)

# --- Define Plotting Function for Schematic Box Views ---
def create_schematic_view(title, width, height, components=[], annotations=[], background_color="#FFFFFF", border_color=config.OUTLINE_COLOR):
    """Creates a simple schematic box view using Plotly shapes with manual range calculation for reliable autoscaling."""
    """Creates a simple schematic box view using Plotly shapes with manual range calculation for reliable autoscaling."""
    fig = go.Figure()
    legend_items_added = set()

    min_x_data, max_x_data = width, 0 # Initialize inverse to find actual min/max
    min_y_data, max_y_data = height, 0

    # Add component rectangles and lines, track bounds
    for comp in components:
        shape_type = comp.get("type", "rect")
        x0=comp.get("x0", 0); y0=comp.get("y0", 0); x1=comp.get("x1", 0); y1=comp.get("y1", 0)
        fig.add_shape(type=shape_type, x0=x0, y0=y0, x1=x1, y1=y1,
                      line=dict(color=comp.get("line_color", border_color), width=comp.get("line_width", 1), dash=comp.get("line_dash", "solid")),
                      fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"), opacity=comp.get("opacity", 1.0), layer=comp.get("layer", "above"), name=comp.get("name", ""))

        # Update bounds based on component coordinates
        min_x_data = min(min_x_data, x0); max_x_data = max(max_x_data, x1)
        min_y_data = min(min_y_data, y0); max_y_data = max(max_y_data, y1)

        comp_name = comp.get("name");
        shape_type = comp.get("type", "rect")
        x0=comp.get("x0", 0); y0=comp.get("y0", 0); x1=comp.get("x1", 0); y1=comp.get("y1", 0)
        fig.add_shape(type=shape_type, x0=x0, y0=y0, x1=x1, y1=y1,
                      line=dict(color=comp.get("line_color", border_color), width=comp.get("line_width", 1), dash=comp.get("line_dash", "solid")),
                      fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"), opacity=comp.get("opacity", 1.0), layer=comp.get("layer", "above"), name=comp.get("name", ""))

        # Update bounds based on component coordinates
        min_x_data = min(min_x_data, x0); max_x_data = max(max_x_data, x1)
        min_y_data = min(min_y_data, y0); max_y_data = max(max_y_data, y1)

        comp_name = comp.get("name");
        if comp_name and comp_name not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line': marker_color = comp.get("line_color", border_color)
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=comp_name, marker=dict(color=marker_color, size=10, symbol=marker_symbol, line=dict(color=comp.get("line_color", border_color), width=1))));
            legend_items_added.add(comp_name)
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line': marker_color = comp.get("line_color", border_color)
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=comp_name, marker=dict(color=marker_color, size=10, symbol=marker_symbol, line=dict(color=comp.get("line_color", border_color), width=1))));
            legend_items_added.add(comp_name)

    # Add annotations, track bounds
    # Add annotations, track bounds
    for ann in annotations:
        x_pos = ann.get("x"); y_pos = ann.get("y")
        fig.add_annotation(x=x_pos, y=y_pos, text=ann.get("text", ""), showarrow=ann.get("showarrow", False), font=dict(size=ann.get("size", 10), color=ann.get("color", config.DIM_ANNOT_COLOR)), align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0.6)"), xanchor=ann.get("xanchor", "center"), yanchor=ann.get("yanchor", "middle"), yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0))
        # Basic bound update for annotations
        text_buffer_x = ann.get("size", 10) * 0.5 + abs(ann.get("xshift", 0))
        text_buffer_y = ann.get("size", 10) * 0.5 + abs(ann.get("yshift", 0))
        if x_pos is not None: min_x_data = min(min_x_data, x_pos - text_buffer_x); max_x_data = max(max_x_data, x_pos + text_buffer_x)
        if y_pos is not None: min_y_data = min(min_y_data, y_pos - text_buffer_y); max_y_data = max(max_y_data, y_pos + text_buffer_y)

    # Calculate range with padding based on data bounds
    data_width = max_x_data - min_x_data if max_x_data > min_x_data else width
    data_height = max_y_data - min_y_data if max_y_data > min_y_data else height
    padding_x = max(data_width * 0.05, 10)
    padding_y = max(data_height * 0.05, 10)
    x_range = [min_x_data - padding_x, max_x_data + padding_x]
    y_range = [min_y_data - padding_y, max_y_data + padding_y]

    # Update layout with calculated range
    fig.update_layout(
        title=title,
        xaxis=dict(range=x_range, showgrid=False, zeroline=False, showticklabels=False, visible=False, constrain='domain'),
        yaxis=dict(range=y_range, showgrid=False, zeroline=False, showticklabels=False, visible=False, scaleanchor="x", scaleratio=1),
        xaxis=dict(range=x_range, showgrid=False, zeroline=False, showticklabels=False, visible=False, constrain='domain'),
        yaxis=dict(range=y_range, showgrid=False, zeroline=False, showticklabels=False, visible=False, scaleanchor="x", scaleratio=1),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=10),
        autosize=True,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color=config.LEGEND_FONT_COLOR, size=11))
    )
    return fig

# --- New Function for Panel Assembly Views ---
def create_panel_assembly_views(panel_data, panel_label="Panel"):
    """Generates Front and Profile schematic views for a single panel assembly."""
    if not panel_data:
        return (go.Figure(layout=dict(title=f"{panel_label} - Front View (Data Unavailable)")),
                go.Figure(layout=dict(title=f"{panel_label} - Profile View (Data Unavailable)")),
                f"{panel_label} data not valid.")

    # Determine dimensions and components based on panel type (wall vs top)
    is_top_panel = "cap_panel_width" in panel_data
    if is_top_panel:
        panel_w = panel_data.get("cap_panel_width", 0)
        panel_h = panel_data.get("cap_panel_length", 0) # Top panel 'height' is crate length
        plywood_t = panel_data.get("cap_panel_thickness", 0)
        cleat_spec = panel_data.get("cap_cleat_spec", {})
        # Combine longitudinal and transverse cleats for drawing
        cleats = []
        lc = panel_data.get("longitudinal_cleats", {})
        tc = panel_data.get("transverse_cleats", {})
        if lc.get("count", 0) > 0:
            for pos_x in lc.get("positions", []): cleats.append({"orientation": "vertical", "length": lc.get("cleat_length_each"), "width": lc.get("cleat_width_each"), "thickness": lc.get("cleat_thickness_each"), "position_x": pos_x, "position_y": 0, "type": "longitudinal"})
        if tc.get("count", 0) > 0:
            for pos_y in tc.get("positions", []): cleats.append({"orientation": "horizontal", "length": tc.get("cleat_length_each"), "width": tc.get("cleat_width_each"), "thickness": tc.get("cleat_thickness_each"), "position_x": 0, "position_y": pos_y, "type": "transverse"})
        plywood_pieces = [{"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h}] # Top panel is single piece
        panel_color = config.CAP_PANEL_COLOR_VIZ
        cleat_color = config.CAP_CLEAT_COLOR_VIZ
    else: # Wall panel
        panel_w = panel_data.get("panel_width", 0)
        panel_h = panel_data.get("panel_height", 0)
        plywood_t = panel_data.get("plywood_thickness", 0)
        cleats = panel_data.get("cleats", [])
        plywood_pieces = panel_data.get("plywood_pieces", [])
        cleat_spec = panel_data.get("cleat_spec", panel_data.get("wall_cleat_spec", {}))
        panel_color = config.WALL_PANEL_COLOR_VIZ
        cleat_color = config.WALL_CLEAT_COLOR_VIZ

    cleat_t = cleat_spec.get("thickness", config.DEFAULT_CLEAT_NOMINAL_THICKNESS)
    cleat_w = cleat_spec.get("width", config.DEFAULT_CLEAT_NOMINAL_WIDTH)

    if panel_w <= config.FLOAT_TOLERANCE or panel_h <= config.FLOAT_TOLERANCE:
        return (go.Figure(layout=dict(title=f"{panel_label} - Front View (Invalid Dimensions)")),
                go.Figure(layout=dict(title=f"{panel_label} - Profile View (Invalid Dimensions)")),
                f"{panel_label} dimensions invalid.")

    # --- Front View ---
    front_components = []; front_annotations = []; cleats_added = False; plywood_added = False; splice_added = False
    # Draw Plywood Pieces
    for i, piece in enumerate(plywood_pieces):
        comp_name = ""
        if not plywood_added: comp_name = "Plywood"; plywood_added = True
        front_components.append({"type": "rect", "x0": piece.get("x0", 0), "y0": piece.get("y0", 0), "x1": piece.get("x1", 0), "y1": piece.get("y1", 0), "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "line_width": 0.5, "name": comp_name, "layer": "below"})
    # Draw Splice Lines
    splice_line_color = "#888888"; splice_line_width = 1.5
    if len(plywood_pieces) > 1:
        is_vert_spliced = any(math.isclose(p.get("x0", -1), config.PLYWOOD_STD_WIDTH) or math.isclose(p.get("x1", -1), config.PLYWOOD_STD_WIDTH) for p in plywood_pieces)
        if is_vert_spliced: front_components.append({"type": "line", "x0": config.PLYWOOD_STD_WIDTH, "y0": 0, "x1": config.PLYWOOD_STD_WIDTH, "y1": panel_h, "line_color": splice_line_color, "line_width": splice_line_width, "line_dash": "dash", "name": "Splice Line" if not splice_added else "", "layer": "above"}); splice_added = True
        is_horz_spliced = any(math.isclose(p.get("y0", -1), config.PLYWOOD_STD_HEIGHT) or math.isclose(p.get("y1", -1), config.PLYWOOD_STD_HEIGHT) for p in plywood_pieces)
        if is_horz_spliced: front_components.append({"type": "line", "x0": 0, "y0": config.PLYWOOD_STD_HEIGHT, "x1": panel_w, "y1": config.PLYWOOD_STD_HEIGHT, "line_color": splice_line_color, "line_width": splice_line_width, "line_dash": "dash", "name": "Splice Line" if not splice_added else "", "layer": "above"}); splice_added = True
    # Draw Cleats
    for cleat in cleats:
        c_orient = cleat.get("orientation"); c_len = cleat.get("length"); c_width = cleat.get("width"); c_x = cleat.get("position_x"); c_y = cleat.get("position_y"); abs_center_x = c_x + panel_w / 2.0; abs_center_y = c_y + panel_h / 2.0
        if c_orient == "horizontal": x0, x1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0; y0, y1 = abs_center_y - c_width / 2.0, abs_center_y + c_width / 2.0; text_annot = f'{c_len:.1f}" L'
        elif c_orient == "vertical": x0, x1 = abs_center_x - c_width / 2.0, abs_center_x + c_width / 2.0; y0, y1 = abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0; text_annot = f'{c_len:.1f}" H'
        else: continue
        comp_name = "";
        if not cleats_added: comp_name = "Cleats"; cleats_added = True
        front_components.append({"type":"rect", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": comp_name})
        if c_len > 1.0 and c_width > 1.0: front_annotations.append({"x": abs_center_x, "y": abs_center_y, "text": text_annot, "size": 8, "color": config.CLEAT_FONT_COLOR})
    front_annotations.append({"x": -5, "y": panel_h / 2.0, "text": f'{panel_h:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
    front_annotations.append({"x": panel_w / 2.0, "y": -10, "text": f'{panel_w:.2f}"', "size": 10, "yanchor": "top"})
    fig_front = create_schematic_view(title=f"{panel_label} - Front View", width=panel_w, height=panel_h, components=front_components, annotations=front_annotations)

    # --- Profile View ---
    profile_components = []; profile_annotations = []; profile_cleats_added = False
    # Profile view width is the dimension perpendicular to the view (panel_h for side/end, panel_l for top)
    profile_view_width = panel_h if panel_label != "Top Panel" else panel_l
    profile_height = plywood_t + cleat_t # Profile view height is thickness
    # Draw Plywood profile
    profile_components.append({"type": "rect", "x0": 0, "y0": 0, "x1": profile_view_width, "y1": plywood_t, "fillcolor": panel_color, "line_color": config.OUTLINE_COLOR, "name": "Plywood Profile"})
    # Draw Cleat profiles (simplified: show edge cleats and one intermediate if present)
    # Determine which cleats are visible in profile
    profile_cleat_orientation = 'horizontal' if panel_label == "Side Panel" else ('vertical' if panel_label == "End Panel" else 'horizontal') # Default profile for top panel shows horizontal cleats

    visible_cleats = [c for c in cleats if c.get("orientation") == profile_cleat_orientation]
    if visible_cleats:
        # Draw edge cleats (assuming first and last in sorted list are edges)
        edge_cleats = [c for c in visible_cleats if c.get("type","").startswith("edge")]
        edge_cleats.sort(key=lambda c: c.get("position_y" if profile_cleat_orientation == 'horizontal' else "position_x", 0)) # Sort by position
        if len(edge_cleats) >= 2:
             # Draw first edge cleat profile (position is relative to center, need to convert)
             pos_axis = "position_y" if profile_cleat_orientation == 'horizontal' else "position_x"
             center_dim = panel_h / 2.0 if profile_cleat_orientation == 'horizontal' else panel_w / 2.0
             pos1 = edge_cleats[0].get(pos_axis, 0) + center_dim # Convert to 0-based for profile view width
             x0 = pos1 - edge_cleats[0].get("width", cleat_w)/2.0
             x1 = pos1 + edge_cleats[0].get("width", cleat_w)/2.0
             profile_components.append({"type":"rect", "x0":x0, "y0":plywood_t, "x1":x1, "y1":plywood_t+cleat_t, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleat Profile" if not profile_cleats_added else ""}); profile_cleats_added=True
             # Draw second edge cleat profile
             pos2 = edge_cleats[-1].get(pos_axis, 0) + center_dim
             x0 = pos2 - edge_cleats[-1].get("width", cleat_w)/2.0
             x1 = pos2 + edge_cleats[-1].get("width", cleat_w)/2.0
             profile_components.append({"type":"rect", "x0":x0, "y0":plywood_t, "x1":x1, "y1":plywood_t+cleat_t, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": ""}) # No legend for second

        # Draw one intermediate cleat profile if exists
        intermediate_cleats = [c for c in visible_cleats if c.get("type","").startswith("intermediate")]
        if intermediate_cleats:
             pos_int = intermediate_cleats[0].get(pos_axis, 0) + center_dim
             x0 = pos_int - intermediate_cleats[0].get("width", cleat_w)/2.0
             x1 = pos_int + intermediate_cleats[0].get("width", cleat_w)/2.0
             profile_components.append({"type":"rect", "x0":x0, "y0":plywood_t, "x1":x1, "y1":plywood_t+cleat_t, "fillcolor": cleat_color, "line_color": config.OUTLINE_COLOR, "name": "Cleat Profile" if not profile_cleats_added else ""}); profile_cleats_added=True

    profile_annotations.append({"x": profile_view_width / 2.0, "y": -2, "text": f'{profile_view_width:.2f}"', "size": 10, "yanchor": "top"})
    profile_annotations.append({"x": -2, "y": profile_height / 2.0, "text": f'{profile_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
    # Adjust height multiplier for better visibility of thin profile
    fig_profile = create_schematic_view(title=f"{panel_label} - Profile View", width=profile_view_width, height=profile_height * 10, components=profile_components, annotations=profile_annotations)

    return fig_front, fig_profile, None # Return figs and None for error


# --- Visualization Display Functions ---

def display_skid_visualization(skid_results, overall_skid_span_metric, ui_inputs):
    """Displays the skid schematic and explanation."""
    st.subheader("Base/Skid Layout (Top-Down Schematic)")
    skid_status = skid_results.get("status", "UNKNOWN"); skid_plot_generated = False; skid_plot_error = None
    skid_status = skid_results.get("status", "UNKNOWN"); skid_plot_generated = False; skid_plot_error = None
    if skid_status == "OK":
        try:
            skid_w_viz = skid_results.get('skid_width'); skid_count_viz = skid_results.get('skid_count'); positions_viz = skid_results.get('skid_positions'); spacing_viz = skid_results.get('spacing_actual'); usable_w_skids_viz = skid_results.get('usable_width', 0); overall_skid_span_viz = overall_skid_span_metric
            if (skid_w_viz and skid_count_viz and positions_viz and len(positions_viz) == skid_count_viz and usable_w_skids_viz):
                components = []; annotations = []; plot_width = usable_w_skids_viz; plot_height = skid_w_viz * 1.5; origin_x = plot_width / 2.0
                for i, pos in enumerate(positions_viz): x0 = origin_x + pos - skid_w_viz / 2.0; x1 = origin_x + pos + skid_w_viz / 2.0; y0 = plot_height * 0.25; y1 = y0 + skid_w_viz; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.SKID_COLOR_VIZ, "line_color": config.SKID_OUTLINE_COLOR_VIZ, "name": "Skids" if i == 0 else ""}); annotations.append({"x": (x0 + x1) / 2.0, "y": y1 + 5, "text": f"@{pos:.2f}\"", "size": 9, "color": "#555555"})
                if skid_count_viz > 1 and spacing_viz is not None:
                     for i in range(skid_count_viz - 1): x_start = origin_x + positions_viz[i]; x_end = origin_x + positions_viz[i+1]; mid_x = (x_start + x_end) / 2.0; annotations.append({"x": mid_x, "y": y0 - 10, "text": f'↔ {spacing_viz:.2f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
                annotations.append({"x": plot_width / 2.0, "y": -10, "text": f"Usable Width: {usable_w_skids_viz:.2f}\"", "size": 10});
                if overall_skid_span_viz: annotations.append({"x": plot_width / 2.0, "y": plot_height + 15, "text": f"Overall Skid Span: {overall_skid_span_viz:.2f}\"", "size": 10})
                skid_fig = create_schematic_view(title=f"Base/Skid Layout", width=plot_width, height=plot_height, components=components, annotations=annotations); skid_plot_generated = True
            else: skid_p