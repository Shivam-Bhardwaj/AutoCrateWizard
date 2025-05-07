# wizard_app/ui_modules/visualizations.py
"""
Handles the generation and display of layout schematics.
Version 0.4.14 - Refined autoscaling and floorboard schematic view.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging
# Use absolute imports within the package
from wizard_app import config
from wizard_app import explanations # Import explanations

log = logging.getLogger(__name__)

# --- Define Plotting Function for Schematic Box Views (Autoscale Fix) ---
def create_schematic_view(title, width, height, components=[], annotations=[], background_color="#FFFFFF", border_color=config.OUTLINE_COLOR):
    """Creates a simple schematic box view using Plotly shapes with autoscaling."""
    fig = go.Figure()
    legend_items_added = set()

    # Add component rectangles
    for comp in components:
        fig.add_shape(
            type="rect",
            x0=comp.get("x0", 0), y0=comp.get("y0", 0),
            x1=comp.get("x1", 0), y1=comp.get("y1", 0),
            line=dict(color=comp.get("line_color", border_color), width=comp.get("line_width", 1)),
            fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"),
            opacity=comp.get("opacity", 1.0),
            layer=comp.get("layer", "above"),
            name=comp.get("name", "") # Name used for hover
        )
        # Add trace for legend entry if name provided and not already added
        comp_name = comp.get("name")
        if comp_name and comp_name not in legend_items_added:
             fig.add_trace(go.Scatter(
                 x=[None], y=[None], mode='markers', name=comp_name,
                 marker=dict(color=comp.get("fillcolor", "rgba(0,0,0,0)"), size=10, symbol='square',
                             line=dict(color=comp.get("line_color", border_color), width=1))
            ))
             legend_items_added.add(comp_name)

    # Add annotations
    for ann in annotations:
        fig.add_annotation(
            x=ann.get("x"), y=ann.get("y"), text=ann.get("text", ""), showarrow=ann.get("showarrow", False),
            font=dict(size=ann.get("size", 10), color=ann.get("color", config.DIM_ANNOT_COLOR)),
            align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0.6)"),
            xanchor=ann.get("xanchor", "center"), yanchor=ann.get("yanchor", "middle"),
            yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0)
        )

    # Update layout for schematic appearance - Rely on default autorange
    fig.update_layout(
        title=title,
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False, visible=False,
            constrain='domain' # Helps maintain aspect ratio with yaxis scaleanchor
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False, visible=False,
            scaleanchor="x", # Anchor y scale to x scale
            scaleratio=1     # Ensure 1:1 aspect ratio
        ),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=20),
        # Let Plotly determine height based on autosize and aspect ratio
        autosize=True,
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1,
            font=dict(color=config.LEGEND_FONT_COLOR, size=11)
        )
    )
    # Explicitly update axes *after* adding shapes/annotations
    # This ensures Plotly's autorange considers all elements
    fig.update_xaxes(autorange=True)
    fig.update_yaxes(autorange=True)

    return fig


# --- Visualization Display Functions ---

def display_skid_visualization(skid_results, overall_skid_span_metric, product_weight):
    """Displays the skid schematic and explanation."""
    st.subheader("Base/Skid Layout (Top-Down Schematic)")
    skid_status = skid_results.get("status", "UNKNOWN")
    skid_plot_generated = False; skid_plot_error = None

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
            else: skid_plot_error = "Missing/invalid skid data."
        except Exception as e: skid_plot_error = f"Skid schematic error: {e}"; log.error(skid_plot_error, exc_info=True)

    if skid_plot_generated:
        st.plotly_chart(skid_fig, use_container_width=True)
        with st.expander("Logic Explanation"):
            st.markdown(explanations.get_skid_explanation(skid_results, product_weight))
    elif skid_plot_error: st.warning(f"⚠️ {skid_plot_error}")
    elif skid_status != "OK": st.info("Base/Skid schematic requires 'OK' skid status.")
    else: st.info("Enter parameters.")

def display_floorboard_visualization(floor_results, product_length, clearance_side):
    """Displays the floorboard schematic and explanation."""
    st.divider(); st.subheader("Floorboard Layout (Top-Down Schematic)")
    floorboard_plot_generated = False; floorboard_plot_error = None
    # Assuming floorboard_logic_available is True if this function is called
    if floor_results and floor_results.get('status') in ["OK", "WARNING"]:
        fb_boards_viz = floor_results.get("floorboards", []); fb_target_span_viz = floor_results.get("target_span_along_length", 0.0); fb_length_across_skids_viz = floor_results.get("floorboard_length_across_skids", 0.0); fb_center_gap_viz = floor_results.get("center_gap", 0.0)
        if fb_boards_viz and fb_length_across_skids_viz > config.FLOAT_TOLERANCE and fb_target_span_viz > config.FLOAT_TOLERANCE:
            try:
                components = []; annotations = []; plot_width = fb_length_across_skids_viz; plot_height = fb_target_span_viz; custom_added_legend = False; std_added_legend = False
                for i, board in enumerate(fb_boards_viz):
                    board_width_dim_fb = board.get("actual_width", 0.0); board_start_y_fb = board.get("position", 0.0); board_end_y_fb = board_start_y_fb + board_width_dim_fb; board_nominal_fb = board.get("nominal", "N/A"); is_custom = board_nominal_fb == "Custom"
                    # Use new custom color
                    board_color_fb = config.FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else config.FLOORBOARD_STD_COLOR_VIZ
                    comp_name = "";
                    if is_custom and not custom_added_legend: comp_name = "Custom Board"; custom_added_legend = True
                    elif not is_custom and not std_added_legend: comp_name = "Standard Boards"; std_added_legend = True
                    components.append({"x0": 0, "y0": board_start_y_fb, "x1": plot_width, "y1": board_end_y_fb, "fillcolor": board_color_fb, "line_color": config.FLOORBOARD_OUTLINE_COLOR_VIZ, "name": comp_name})
                    # Single line annotation
                    if board_width_dim_fb > 0.5: annotations.append({"x": plot_width / 2.0, "y": (board_start_y_fb + board_end_y_fb) / 2.0, "text": f'{board_nominal_fb} / {board_width_dim_fb:.2f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR if is_custom else "#333333"})
                if abs(fb_center_gap_viz) > config.FLOAT_TOLERANCE:
                    gap_start_y_viz = floor_results.get("total_board_width", 0.0); gap_end_y_viz = gap_start_y_viz + fb_center_gap_viz
                    if gap_end_y_viz > gap_start_y_viz + config.FLOAT_TOLERANCE: components.append({"x0": 0, "y0": gap_start_y_viz, "x1": plot_width, "y1": gap_end_y_viz, "fillcolor": config.GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, "name": f'Center Gap ({fb_center_gap_viz:.3f}")'}); annotations.append({"x": plot_width / 2.0, "y": (gap_start_y_viz + gap_end_y_viz) / 2.0, "text": f"Gap\n{fb_center_gap_viz:.3f}\"", "size": 8, "color": config.DIM_ANNOT_COLOR, "bgcolor": "rgba(255,255,255,0.0)"})
                annotations.append({"x": -5, "y": plot_height / 2.0, "text": f'{plot_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
                annotations.append({"x": plot_width / 2.0, "y": -10, "text": f'{plot_width:.2f}"', "size": 10, "yanchor": "top"})
                fb_fig = create_schematic_view(title=f"Floorboard Layout (Target Span: {fb_target_span_viz:.2f}\")", width=plot_width, height=plot_height, components=components, annotations=annotations); floorboard_plot_generated = True
            except Exception as e: floorboard_plot_error = f"FB schematic error: {e}"; log.error(floorboard_plot_error, exc_info=True)

        if floorboard_plot_generated:
            st.plotly_chart(fb_fig, use_container_width=True)
            with st.expander("Logic Explanation"):
                st.markdown(explanations.get_floorboard_explanation(floor_results, product_length, clearance_side))
        elif floorboard_plot_error: st.warning(f"⚠️ {floorboard_plot_error}")
        elif not fb_boards_viz: st.info("No floorboards were placed.")
        else: st.info("FB schematic needs valid boards & positive dims.")
    elif floor_results: st.info(f"No FB layout: {floor_results.get('message', 'Status: '+floor_results.get('status','N/A'))}")
    # Need skid_status here, maybe pass it in? For now, assume if floor_results is None, skid might be bad.
    # elif skid_status != "OK": st.info("FB layout needs OK skid status.")
    else: st.info("Floorboard calculation skipped or failed.")


def display_wall_visualization(wall_results):
    """Displays the wall panel schematics and explanations."""
    st.divider(); st.subheader("Wall Panel Layout Schematics")
    wall_view_tabs = st.tabs(["Side Panel View", "End Panel View"])
    with wall_view_tabs[0]:
        st.markdown("#### Side Panel (Along Crate Length)")
        side_panel_data_to_plot = wall_results.get("side_panels", [None])[0] if wall_results else None
        fig_side_wall, error_side_wall = create_wall_panel_schematic(panel_data=side_panel_data_to_plot, panel_label="Side Panel")
        if error_side_wall: st.info(error_side_wall)
        else:
            st.plotly_chart(fig_side_wall, use_container_width=True)
            if side_panel_data_to_plot:
                 with st.expander("Logic Explanation"):
                    st.markdown(explanations.get_wall_panel_explanation(side_panel_data_to_plot, "Side Panel"))
    with wall_view_tabs[1]:
        st.markdown("#### End Panel (Along Crate Width)")
        end_panel_data_to_plot = wall_results.get("end_panels", [None])[0] if wall_results else None
        fig_end_wall, error_end_wall = create_wall_panel_schematic(panel_data=end_panel_data_to_plot, panel_label="End Panel")
        if error_end_wall: st.info(error_end_wall)
        else:
            st.plotly_chart(fig_end_wall, use_container_width=True)
            if end_panel_data_to_plot:
                with st.expander("Logic Explanation"):
                    st.markdown(explanations.get_wall_panel_explanation(end_panel_data_to_plot, "End Panel"))

def create_wall_panel_schematic(panel_data=None, panel_label="Wall Panel"):
    """Helper to create the schematic view for a wall panel."""
    if not panel_data or not panel_data.get("cleats"): return go.Figure(layout=dict(title=f"{panel_label} Layout (Data Unavailable)")), f"{panel_label} data not valid."
    panel_w = panel_data.get("panel_width", 0); panel_h = panel_data.get("panel_height", 0); cleats = panel_data.get("cleats", [])
    if panel_w <= config.FLOAT_TOLERANCE or panel_h <= config.FLOAT_TOLERANCE: return go.Figure(layout=dict(title=f"{panel_label} Layout (Invalid Dimensions)")), f"{panel_label} dimensions invalid."
    components = []; annotations = []; cleats_added_legend = False
    components.append({"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h, "fillcolor": config.WALL_PANEL_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": "Plywood"})
    for cleat in cleats:
        c_orient = cleat.get("orientation"); c_len = cleat.get("length"); c_width = cleat.get("width"); c_x = cleat.get("position_x"); c_y = cleat.get("position_y"); abs_center_x = c_x + panel_w / 2.0; abs_center_y = c_y + panel_h / 2.0
        if c_orient == "horizontal": x0, x1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0; y0, y1 = abs_center_y - c_width / 2.0, abs_center_y + c_width / 2.0; text_annot = f'{c_len:.1f}" L'
        elif c_orient == "vertical": x0, x1 = abs_center_x - c_width / 2.0, abs_center_x + c_width / 2.0; y0, y1 = abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0; text_annot = f'{c_len:.1f}" H'
        else: continue
        comp_name = "";
        if not cleats_added_legend: comp_name = "Cleats"; cleats_added_legend = True
        components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.WALL_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name})
        if c_len > 1.0 and c_width > 1.0: annotations.append({"x": abs_center_x, "y": abs_center_y, "text": text_annot, "size": 8, "color": config.CLEAT_FONT_COLOR})
    annotations.append({"x": -5, "y": panel_h / 2.0, "text": f'{panel_h:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"})
    annotations.append({"x": panel_w / 2.0, "y": -10, "text": f'{panel_w:.2f}"', "size": 10, "yanchor": "top"})
    fig = create_schematic_view(title=f"{panel_label} Layout", width=panel_w, height=panel_h, components=components, annotations=annotations)
    return fig, None


def display_top_panel_visualization(top_panel_results, max_top_cleat_spacing_ui):
    """Displays the top panel schematic and explanation."""
    st.divider(); st.subheader("Top Panel Layout (Top-Down Schematic)")
    top_panel_plot_generated = False; top_panel_plot_error = None
    # Assuming cap_logic_available is True if this function is called
    if top_panel_results and top_panel_results.get("status") in ["OK", "WARNING"]:
        try:
            panel_w = top_panel_results.get("cap_panel_width", 0); panel_l = top_panel_results.get("cap_panel_length", 0); long_cleats = top_panel_results.get("longitudinal_cleats", {}); trans_cleats = top_panel_results.get("transverse_cleats", {})
            if panel_w > config.FLOAT_TOLERANCE and panel_l > config.FLOAT_TOLERANCE:
                components = []; annotations = []; plot_width = panel_w; plot_height = panel_l; origin_x = plot_width / 2.0; origin_y = plot_height / 2.0; long_cleats_added = False; trans_cleats_added = False
                components.append({"x0": 0, "y0": 0, "x1": plot_width, "y1": plot_height, "fillcolor": config.CAP_PANEL_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": "Top Panel"})
                if long_cleats.get("count", 0) > 0:
                    lc_w = long_cleats.get("cleat_width_each", 0); lc_l = long_cleats.get("cleat_length_each", 0); lc_pos = long_cleats.get("positions", [])
                    for i, x_center_rel in enumerate(lc_pos): abs_x_center = origin_x + x_center_rel; x0 = abs_x_center - lc_w / 2.0; x1 = abs_x_center + lc_w / 2.0; y0 = origin_y - lc_l / 2.0; y1 = origin_y + lc_l / 2.0; comp_name = "";
                    if not long_cleats_added: comp_name = "Longitudinal Cleats"; long_cleats_added = True; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.CAP_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name});
                    if lc_w > 0.5: annotations.append({"x": abs_x_center, "y": origin_y, "text": f'{lc_w:.1f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR})
                    if len(lc_pos) > 1: lc_space = long_cleats.get("actual_spacing", 0);
                    for i in range(len(lc_pos) - 1): mid_x = origin_x + (lc_pos[i] + lc_pos[i+1]) / 2.0; annotations.append({"x": mid_x, "y": plot_height * 0.9, "text": f'↔{lc_space:.1f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
                if trans_cleats.get("count", 0) > 0:
                    tc_w = trans_cleats.get("cleat_width_each", 0); tc_l = trans_cleats.get("cleat_length_each", 0); tc_pos = trans_cleats.get("positions", [])
                    for i, y_center_rel in enumerate(tc_pos): abs_y_center = origin_y + y_center_rel; x0 = origin_x - tc_l / 2.0; x1 = origin_x + tc_l / 2.0; y0 = abs_y_center - tc_w / 2.0; y1 = abs_y_center + tc_w / 2.0; comp_name = "";
                    if not trans_cleats_added: comp_name = "Transverse Cleats"; trans_cleats_added = True; components.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "fillcolor": config.CAP_CLEAT_COLOR_VIZ, "line_color": config.OUTLINE_COLOR, "name": comp_name});
                    if tc_w > 0.5: annotations.append({"x": origin_x, "y": abs_y_center, "text": f'{tc_w:.1f}" W', "size": 8, "color": config.CLEAT_FONT_COLOR})
                    if len(tc_pos) > 1: tc_space = trans_cleats.get("actual_spacing", 0);
                    for i in range(len(tc_pos) - 1): mid_y = origin_y + (tc_pos[i] + tc_pos[i+1]) / 2.0; annotations.append({"x": plot_width * 0.9, "y": mid_y, "text": f'↕{tc_space:.1f}"', "size": 9, "color": config.DIM_ANNOT_COLOR})
                annotations.append({"x": -5, "y": plot_height / 2.0, "text": f'{plot_height:.2f}"', "size": 10, "textangle": -90, "xanchor": "right"}); annotations.append({"x": plot_width / 2.0, "y": -10, "text": f'{plot_width:.2f}"', "size": 10, "yanchor": "top"})
                top_panel_fig = create_schematic_view(title="Top Panel Layout", width=plot_width, height=plot_height, components=components, annotations=annotations); top_panel_plot_generated = True
            else: top_panel_plot_error = "Top panel dimensions invalid."
        except Exception as e: top_panel_plot_error = f"Top Panel schematic error: {e}"; logging.error(top_panel_plot_error, exc_info=True)

    if top_panel_plot_generated:
        st.plotly_chart(top_panel_fig, use_container_width=True)
        with st.expander("Logic Explanation"):
             st.markdown(explanations.get_top_panel_explanation(top_panel_results, max_top_cleat_spacing_ui))
    elif top_panel_plot_error: st.warning(f"⚠️ {top_panel_plot_error}")
    # elif not cap_logic_available: st.info("Top Panel logic not available.") # Redundant check
    elif not top_panel_results or top_panel_results.get("status") not in ["OK","WARNING"]: st.info(f"Top Panel schematic needs OK/Warning. Got: {top_panel_results.get('status') if top_panel_results else 'N/A'}")
    else: st.info("Enter params for Top Panel schematic.")

