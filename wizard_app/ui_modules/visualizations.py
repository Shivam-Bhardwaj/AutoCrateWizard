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

log = logging.getLogger(__name__)

# --- Define Plotting Function for Schematic Box Views ---
def create_schematic_view(title, width, height, components=[], annotations=[], background_color="#FFFFFF", border_color=config.OUTLINE_COLOR):
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
        if comp_name and comp_name not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line': marker_color = comp.get("line_color", border_color)
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=comp_name, marker=dict(color=marker_color, size=10, symbol=marker_symbol, line=dict(color=comp.get("line_color", border_color), width=1))));
            legend_items_added.add(comp_name)

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
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='white',
        margin=dict(l=10, r=10, t=50, b=10),
        autosize=True,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(color=config.LEGEND_FONT_COLOR, size=11))
    )
    return fig


# --- Visualization Display Functions ---

def display_skid_visualization(skid_results, overall_skid_span_metric, ui_inputs):
    """Displays the skid schematic and explanation."""
    st.subheader("Base/Skid Layout (Top-Down Schematic)")
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