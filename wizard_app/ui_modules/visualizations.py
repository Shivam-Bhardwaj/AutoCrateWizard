# wizard_app/ui_modules/visualizations.py
# REV: R4
"""
Handles the generation and display of layout schematics for AutoCrate Wizard.
Provides orthographic views for Base, Wall, and Top assemblies.
Uses centralized styling, coordinate systems, and includes variable annotations.
MODIFIED: Corrected yanchor value. Ensured fixedrange=False.
          Defined NX_LABEL_STYLE locally for robustness.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging
import io

# Attempt to import config, but have fallbacks for critical style constants
try:
    from wizard_app import config
except ImportError:
    config = None # type: ignore
    logging.warning("visualizations.py: config module not found. Using fallback style values.")

log = logging.getLogger(__name__)

# Define NX style for labels, consistent with app.py
# Fallback if config is not available or doesn't have these specific constants
NX_LABEL_STYLE = getattr(config, 'NX_LABEL_STYLE', "color:green; font-weight:bold; font-family: 'Courier New', Courier, monospace;")
NX_LABEL_STYLE_HTML_OPEN = getattr(config, 'NX_LABEL_STYLE_HTML_OPEN', f"<span style='{NX_LABEL_STYLE}'>")
NX_LABEL_STYLE_HTML_CLOSE = getattr(config, 'NX_LABEL_STYLE_HTML_CLOSE', "</span>")
NX_ANNOT_FONT_COLOR = "green" 

# Fallback values for other config constants if config is not loaded
DEFAULT_OUTLINE_COLOR = getattr(config, 'OUTLINE_COLOR', '#333333')
DEFAULT_ANNOT_FONT_SIZE_NORMAL = getattr(config, 'ANNOT_FONT_SIZE_NORMAL', 10)
DEFAULT_COMPONENT_FONT_COLOR_DARK = getattr(config, 'COMPONENT_FONT_COLOR_DARK', '#000000')
DEFAULT_AXIS_ZERO_LINE_COLOR = getattr(config, 'AXIS_ZERO_LINE_COLOR', '#AAAAAA')
DEFAULT_TICK_LABEL_FONT_SIZE = getattr(config, 'TICK_LABEL_FONT_SIZE', 10)
DEFAULT_AXIS_LABEL_FONT_SIZE = getattr(config, 'AXIS_LABEL_FONT_SIZE', 12)
DEFAULT_TITLE_FONT_SIZE = getattr(config, 'TITLE_FONT_SIZE', 14)
DEFAULT_LEGEND_FONT_COLOR = getattr(config, 'LEGEND_FONT_COLOR', '#000000')
DEFAULT_LEGEND_FONT_SIZE = getattr(config, 'LEGEND_FONT_SIZE', 11)
DEFAULT_ANNOT_FONT_SIZE_SMALL = getattr(config, 'ANNOT_FONT_SIZE_SMALL', 8)
DEFAULT_CLEAT_FONT_COLOR = getattr(config, 'CLEAT_FONT_COLOR', '#FFFFFF') # Often white for dark cleats
DEFAULT_ANNOT_BGCOLOR_DARK = getattr(config, 'ANNOT_BGCOLOR_DARK', 'rgba(0,0,0,0.5)')
DEFAULT_ANNOT_BGCOLOR_LIGHT = getattr(config, 'ANNOT_BGCOLOR_LIGHT', 'rgba(255,255,255,0.7)')
FLOAT_TOLERANCE_VIZ = getattr(config, 'FLOAT_TOLERANCE', 1e-6)

# Specific colors from config, with fallbacks
CAP_PANEL_COLOR_VIZ = getattr(config, 'CAP_PANEL_COLOR_VIZ', '#E0E0E0')
CAP_CLEAT_COLOR_VIZ = getattr(config, 'CAP_CLEAT_COLOR_VIZ', '#A0522D')
WALL_PANEL_COLOR_VIZ = getattr(config, 'WALL_PANEL_COLOR_VIZ', '#F5F5DC')
WALL_CLEAT_COLOR_VIZ = getattr(config, 'WALL_CLEAT_COLOR_VIZ', '#A0522D')
SKID_COLOR_VIZ = getattr(config, 'SKID_COLOR_VIZ', '#8B4513')
SKID_OUTLINE_COLOR_VIZ = getattr(config, 'SKID_OUTLINE_COLOR_VIZ', '#654321')
FLOORBOARD_STD_COLOR_VIZ = getattr(config, 'FLOORBOARD_STD_COLOR_VIZ', '#D2B48C')
FLOORBOARD_CUSTOM_COLOR_VIZ = getattr(config, 'FLOORBOARD_CUSTOM_COLOR_VIZ', '#B0C4DE')
FLOORBOARD_OUTLINE_COLOR_VIZ = getattr(config, 'FLOORBOARD_OUTLINE_COLOR_VIZ', '#4682B4')
GAP_COLOR_VIZ = getattr(config, 'GAP_COLOR_VIZ', 'rgba(173, 216, 230, 0.5)')

DEFAULT_CLEAT_NOMINAL_THICKNESS = getattr(config, 'DEFAULT_CLEAT_NOMINAL_THICKNESS', 0.75)
DEFAULT_CLEAT_NOMINAL_WIDTH = getattr(config, 'DEFAULT_CLEAT_NOMINAL_WIDTH', 3.5)
STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS = getattr(config, 'STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS', 1.5)
DEFAULT_PANEL_THICKNESS_UI = getattr(config, 'DEFAULT_PANEL_THICKNESS_UI', 0.25)


# --- Core Plotting Function ---
def create_schematic_view(title_html, width_hint, height_hint, components=[], annotations=[],
                          xlabel_html="X (inches)", ylabel_html="Y (inches)"):
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
            line=dict(color=comp.get("line_color", DEFAULT_OUTLINE_COLOR), width=comp.get("line_width", 1), dash=comp.get("line_dash", "solid")),
            fillcolor=comp.get("fillcolor", "rgba(0,0,0,0)"),
            opacity=comp.get("opacity", 1.0),
            layer=comp.get("layer", "above"),
            name=comp.get("name", "") 
        )
        min_x_data, max_x_data = min(min_x_data, x0, x1), max(max_x_data, x0, x1)
        min_y_data, max_y_data = min(min_y_data, y0, y1), max(max_y_data, y0, y1)
        
        comp_name_for_legend = comp.get("legend_name", comp.get("name")) 
        if comp_name_for_legend and comp_name_for_legend not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line': 
                marker_color = comp.get("line_color", DEFAULT_OUTLINE_COLOR)
            elif marker_color == "rgba(0,0,0,0)": 
                marker_color = DEFAULT_OUTLINE_COLOR
            
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers', name=comp_name_for_legend, 
                marker=dict(color=marker_color, size=10, symbol=marker_symbol, 
                            line=dict(color=comp.get("line_color", DEFAULT_OUTLINE_COLOR), width=1))
            ))
            legend_items_added.add(comp_name_for_legend)

    for ann in annotations:
        found_elements = True
        x_pos, y_pos = ann.get("x"), ann.get("y")
        y_anchor_val = ann.get("yanchor", "middle")
        if y_anchor_val == "center": y_anchor_val = "middle" 

        fig.add_annotation(
            x=x_pos, y=y_pos, text=ann.get("text", ""), showarrow=ann.get("showarrow", False),
            font=dict(size=ann.get("size", DEFAULT_ANNOT_FONT_SIZE_NORMAL), 
                      color=ann.get("color", DEFAULT_COMPONENT_FONT_COLOR_DARK)), 
            align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0)"),
            xanchor=ann.get("xanchor", "center"), 
            yanchor=y_anchor_val, 
            yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0)
        )
        text_width_approx = len(str(ann.get("text", ""))) * ann.get("size", 10) * 0.3 
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
        title=dict(text=title_html, font=dict(size=DEFAULT_TITLE_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK)), 
        xaxis=dict(
            range=x_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_AXIS_ZERO_LINE_COLOR,
            showticklabels=True, tickfont=dict(size=DEFAULT_TICK_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK),
            visible=True, 
            fixedrange=False, 
            title_text=xlabel_html, title_font=dict(size=DEFAULT_AXIS_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK) 
        ),
        yaxis=dict(
            range=y_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_AXIS_ZERO_LINE_COLOR,
            showticklabels=True, tickfont=dict(size=DEFAULT_TICK_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK),
            visible=True, 
            fixedrange=False, 
            scaleanchor="x", scaleratio=1, 
            title_text=ylabel_html, title_font=dict(size=DEFAULT_AXIS_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK) 
        ),
        plot_bgcolor='white', paper_bgcolor='white',
        margin=dict(l=60, r=30, t=80, b=60), 
        height=dynamic_plot_height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, 
                    font=dict(color=DEFAULT_LEGEND_FONT_COLOR, size=DEFAULT_LEGEND_FONT_SIZE))
    )
    return fig

# --- Helper to create NX-styled annotation text ---
def nx_annot(text_content, nx_var_name=""):
    """Creates annotation text with NX variable in green."""
    if nx_var_name:
        return f"{text_content} ({NX_LABEL_STYLE_HTML_OPEN}{nx_var_name}{NX_LABEL_STYLE_HTML_CLOSE})"
    return text_content

# --- Figure CREATION Helper Functions ---
# (The rest of the file: _create_panel_assembly_figure, _create_base_top_view_fig, etc.
#  and generate_base_assembly_figures, generate_wall_panel_figures, generate_top_panel_figures
#  remain the same as in the artifact autocrate_visualizations_py_nx_styled_autoscale,
#  as they already use the nx_annot helper and pass HTML styled labels to create_schematic_view)
#  Make sure to replace config.CONSTANT with DEFAULT_CONSTANT or getattr(config, 'CONSTANT', fallback)
#  if config might not be loaded. I've done this for the constants used in create_schematic_view.
#  You'll need to do this for all config constants used in the _create_... functions below.

def _create_panel_assembly_figure(view_type, panel_data, panel_label_base="Panel"):
    if not panel_data: return None, f"{panel_label_base} {view_type} data invalid."

    is_top_panel="cap_panel_width" in panel_data
    plywood_pieces_data_list = [] 

    if is_top_panel:
        panel_w = panel_data.get("cap_panel_width", 0)
        panel_h = panel_data.get("cap_panel_length", 0) 
        plywood_t = panel_data.get("cap_panel_thickness", 0)
        cleat_spec = panel_data.get("cap_cleat_spec", {})
        panel_color, cleat_color = CAP_PANEL_COLOR_VIZ, CAP_CLEAT_COLOR_VIZ
        
        fig_title_nx = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_{panel_label_base.upper().replace(' ', '_')}_{view_type.upper()}{NX_LABEL_STYLE_HTML_CLOSE}"
        front_xlabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Cap_Panel_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        front_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Cap_Panel_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        profile_xlabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Cap_Panel_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        profile_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Cap_Thickness_Assy{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        
        all_cleats_for_front_view = []
        lc = panel_data.get("longitudinal_cleats", {})
        tc = panel_data.get("transverse_cleats", {})
        if lc.get("count", 0) > 0:
            [all_cleats_for_front_view.append({"orientation": "vertical", "length": lc.get("cleat_length_each"), "width": lc.get("cleat_width_each"), "thickness": lc.get("cleat_thickness_each"), "position_x": pos_x, "position_y": 0, "type": "longitudinal_cleat"}) for pos_x in lc.get("positions", [])]
        if tc.get("count", 0) > 0:
            [all_cleats_for_front_view.append({"orientation": "horizontal", "length": tc.get("cleat_length_each"), "width": tc.get("cleat_width_each"), "thickness": tc.get("cleat_thickness_each"), "position_x": 0, "position_y": pos_y, "type": "transverse_cleat"}) for pos_y in tc.get("positions", [])]
        
        plywood_pieces_data_list = [{"x0": 0, "y0": 0, "x1": panel_w, "y1": panel_h, "label": "Cap_Sheathing"}]
    else: 
        panel_w = panel_data.get("panel_width", 0)
        panel_h = panel_data.get("panel_height", 0)
        plywood_t = panel_data.get("plywood_thickness", 0)
        all_cleats_for_front_view = panel_data.get("cleats", []) 
        plywood_pieces_input = panel_data.get("plywood_pieces", []) 
        cleat_spec = panel_data.get("cleat_spec", {})
        panel_color, cleat_color = WALL_PANEL_COLOR_VIZ, WALL_CLEAT_COLOR_VIZ

        fig_title_nx = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_{panel_label_base.upper().replace(' ', '_')}_{view_type.upper()}{NX_LABEL_STYLE_HTML_CLOSE}"
        front_xlabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Panel_Width_Or_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        front_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Panel_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        profile_xlabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Panel_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]" 
        profile_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Panel_Thickness_Assy{NX_LABEL_STYLE_HTML_CLOSE} [in]" 

        for p in plywood_pieces_input: 
            plywood_pieces_data_list.append({"x0":p["x0"], "y0":p["y0"], "x1":p["x1"], "y1":p["y1"], "label":"Plywood_Piece"})

    cleat_actual_thickness = cleat_spec.get("thickness", DEFAULT_CLEAT_NOMINAL_THICKNESS)
    cleat_actual_width = cleat_spec.get("width", DEFAULT_CLEAT_NOMINAL_WIDTH)

    if panel_w <= FLOAT_TOLERANCE_VIZ or panel_h <= FLOAT_TOLERANCE_VIZ: 
        return None, f"{panel_label_base} dimensions invalid for visualization."

    components, annotations = [], []
    fig = None

    if view_type == "Front":
        cleats_legend_added, plywood_legend_added, splice_lines_legend_added = False, False, False
        for i, piece in enumerate(plywood_pieces_data_list):
            components.append({
                "type": "rect", "x0": piece["x0"], "y0": piece["y0"], "x1": piece["x1"], "y1": piece["y1"],
                "fillcolor": panel_color, "line_color": DEFAULT_OUTLINE_COLOR, "line_width": 0.5,
                "legend_name": "PLY_Sheathing" if not plywood_legend_added else "", "layer": "below"
            })
            plywood_legend_added = True
        
        if not is_top_panel and len(plywood_pieces_data_list) > 1:
            distinct_x_boundaries = sorted(list(set(p["x0"] for p in plywood_pieces_data_list).union(set(p["x1"] for p in plywood_pieces_data_list))))
            for x_bound in distinct_x_boundaries:
                if FLOAT_TOLERANCE_VIZ < x_bound < panel_w - FLOAT_TOLERANCE_VIZ: 
                    components.append({"type":"line", "x0":x_bound, "y0":0, "x1":x_bound, "y1":panel_h, "line_color":DEFAULT_AXIS_ZERO_LINE_COLOR, "line_width":1.5, "line_dash":"dash", "legend_name": "LINE_Plywood_Splice" if not splice_lines_legend_added else "", "layer":"above"})
                    splice_lines_legend_added = True; 
            distinct_y_boundaries = sorted(list(set(p["y0"] for p in plywood_pieces_data_list).union(set(p["y1"] for p in plywood_pieces_data_list))))
            for y_bound in distinct_y_boundaries:
                if FLOAT_TOLERANCE_VIZ < y_bound < panel_h - FLOAT_TOLERANCE_VIZ: 
                    components.append({"type":"line", "x0":0, "y0":y_bound, "x1":panel_w, "y1":y_bound, "line_color":DEFAULT_AXIS_ZERO_LINE_COLOR, "line_width":1.5, "line_dash":"dash", "legend_name": "LINE_Plywood_Splice" if not splice_lines_legend_added else "", "layer":"above"})
                    splice_lines_legend_added = True; 

        for cleat in all_cleats_for_front_view: 
            c_orient = cleat.get("orientation")
            c_len = cleat.get("length")
            c_rect_width = cleat.get("width") if is_top_panel else cleat_actual_width 
            c_x_rel_center = cleat.get("position_x", 0) 
            c_y_rel_center = cleat.get("position_y", 0) 
            abs_center_x = panel_w / 2.0 + c_x_rel_center
            abs_center_y = panel_h / 2.0 + c_y_rel_center

            if c_orient == "horizontal":
                x0, x1 = abs_center_x - c_len / 2.0, abs_center_x + c_len / 2.0
                y0, y1 = abs_center_y - c_rect_width / 2.0, abs_center_y + c_rect_width / 2.0
                text_annot_val = f'{c_len:.1f}"L'
            elif c_orient == "vertical":
                x0, x1 = abs_center_x - c_rect_width / 2.0, abs_center_x + c_rect_width / 2.0
                y0, y1 = abs_center_y - c_len / 2.0, abs_center_y + c_len / 2.0
                text_annot_val = f'{c_len:.1f}"H'
            else: continue 

            components.append({
                "type":"rect", "x0": x0, "y0": y0, "x1": x1, "y1": y1, 
                "fillcolor": cleat_color, "line_color": DEFAULT_OUTLINE_COLOR, 
                "legend_name": "CLEAT_Framing" if not cleats_legend_added else "", "layer":"above"
            })
            cleats_legend_added = True
            
            if c_len > 1.0 and c_rect_width > 1.0:
                annotations.append({
                    "x": abs_center_x, "y": abs_center_y, 
                    "text": text_annot_val, 
                    "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, 
                    "color": DEFAULT_CLEAT_FONT_COLOR, 
                    "bgcolor": DEFAULT_ANNOT_BGCOLOR_DARK
                })
        
        dim_var_w = "DIM_Cap_Panel_Width" if is_top_panel else ("DIM_Panel_Width_End" if "BACK" in panel_label_base.upper() else "DIM_Panel_Length_Side")
        dim_var_h = "DIM_Cap_Panel_Length" if is_top_panel else "DIM_Panel_Height_Used"
        
        annotations.append({"x": panel_w / 2.0, "y": - (panel_h * 0.05), 
                            "text": nx_annot(f'{panel_w:.2f}"', dim_var_w), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                            "yanchor": "top", "yshift":-5})
        annotations.append({"x": - (panel_w * 0.05), "y": panel_h / 2.0, 
                            "text": nx_annot(f'{panel_h:.2f}"', dim_var_h), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                            "textangle": -90, "xanchor": "center", "xshift":-15})
        
        fig = create_schematic_view(fig_title_nx, panel_w, panel_h, components, annotations, 
                                    xlabel_html=front_xlabel_nx, ylabel_html=front_ylabel_nx)
    
    elif view_type == "Profile":
        profile_plot_width = panel_h if is_top_panel else panel_h 
        profile_plot_height_assy = plywood_t + cleat_actual_thickness 

        components.append({
            "type": "rect", "x0": 0, "y0": 0, "x1": profile_plot_width, "y1": plywood_t, 
            "fillcolor": panel_color, "line_color": DEFAULT_OUTLINE_COLOR, 
            "legend_name": "PLY_Sheathing_Profile", "layer":"below"
        })
        representative_cleat_profile_width_on_plot = cleat_actual_width 
        cleat_x0 = (profile_plot_width / 2.0) - (representative_cleat_profile_width_on_plot / 2.0)
        cleat_x1 = cleat_x0 + representative_cleat_profile_width_on_plot
        components.append({
            "type":"rect", "x0": cleat_x0, "y0": plywood_t, 
            "x1": cleat_x1, "y1": plywood_t + cleat_actual_thickness, 
            "fillcolor": cleat_color, "line_color": DEFAULT_OUTLINE_COLOR, 
            "legend_name": "CLEAT_Framing_Profile"
        })

        dim_var_profile_len = "DIM_Cap_Panel_Length" if is_top_panel else "DIM_Panel_Height_Used"
        dim_var_ply_thick = "DIM_Cap_Panel_Thickness" if is_top_panel else "DIM_Panel_Plywood_Thickness"
        dim_var_cleat_thick = "ATTR_Cap_Cleat_Thickness" if is_top_panel else "ATTR_Wall_Cleat_Thickness"

        annotations.append({"x": profile_plot_width / 2.0, "y": - (profile_plot_height_assy * 0.05), 
                            "text": nx_annot(f'{profile_plot_width:.2f}"', dim_var_profile_len), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                            "yanchor": "top", "yshift":-5})
        annotations.append({"x": - (profile_plot_width * 0.05), "y": profile_plot_height_assy / 2.0, 
                            "text": nx_annot(f'{profile_plot_height_assy:.2f}"', f"{dim_var_ply_thick} + {dim_var_cleat_thick}"), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                            "textangle": -90, "xanchor": "center","xshift":-15})
        
        bgcolor_for_green_text = getattr(config, 'ANNOT_BGCOLOR_DARK_FOR_GREEN_TEXT', DEFAULT_ANNOT_BGCOLOR_DARK)

        annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t / 2.0, 
                            "text": nx_annot(f'Plywood: {plywood_t:.2f}"', dim_var_ply_thick), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "xanchor": "center"})
        annotations.append({"x": profile_plot_width * 0.75, "y": plywood_t + cleat_actual_thickness / 2.0, 
                            "text": nx_annot(f'Cleat: {cleat_actual_thickness:.2f}"', dim_var_cleat_thick), 
                            "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, 
                            "bgcolor": bgcolor_for_green_text if NX_ANNOT_FONT_COLOR == "green" else DEFAULT_ANNOT_BGCOLOR_DARK,
                            "xanchor": "center"})
        
        fig = create_schematic_view(fig_title_nx, profile_plot_width, profile_plot_height_assy, components, annotations, 
                                    xlabel_html=profile_xlabel_nx, ylabel_html=profile_ylabel_nx)
    return fig, None


def _create_base_top_view_fig(skid_results, floor_results, overall_dims, ui_inputs):
    try:
        panel_thickness = ui_inputs.get('panel_thickness', DEFAULT_PANEL_THICKNESS_UI)
        wall_cleat_thickness = ui_inputs.get('wall_cleat_thickness', DEFAULT_CLEAT_NOMINAL_THICKNESS)
        wall_assembly_offset = panel_thickness + wall_cleat_thickness

        skid_w = skid_results.get('skid_width')
        skid_x_positions = skid_results.get('skid_positions') 
        if not skid_x_positions or skid_w is None: raise ValueError("Skid positions or width missing.")
        
        overall_skid_span = overall_dims.get('overall_skid_span')
        if overall_skid_span is None:
            if len(skid_x_positions) == 1: overall_skid_span = skid_w
            else: overall_skid_span = abs(skid_x_positions[-1] - skid_x_positions[0]) + skid_w
        
        all_floorboards = floor_results.get("floorboards", [])
        fb_center_gap_viz = floor_results.get("center_gap", 0.0)
        crate_length = overall_dims.get('length') 

        if not all([skid_w is not None, skid_x_positions is not None, overall_skid_span is not None, all_floorboards is not None, crate_length is not None]):
            raise ValueError("Missing critical dimensions for base top view")
        
        components_top, annotations_top = [], []
        skid_legend_added, fb_std_added, fb_cust_added, fb_gap_added = False, False, False, False

        for x_center_rel_to_span_center in skid_x_positions:
            x0 = x_center_rel_to_span_center - skid_w / 2.0
            x1 = x_center_rel_to_span_center + skid_w / 2.0
            y0, y1 = 0.0, crate_length 
            components_top.append({"type": "rect", "x0": x0, "y0": y0, "x1": x1, "y1": y1, 
                                   "fillcolor": SKID_COLOR_VIZ, "opacity": 0.5, 
                                   "line_color": SKID_OUTLINE_COLOR_VIZ, "line_width": 0.5, 
                                   "legend_name": "SKID_Lumber" if not skid_legend_added else "", "layer": "below"})
            skid_legend_added = True

        plot_x0_boards = -overall_skid_span / 2.0
        plot_x1_boards = overall_skid_span / 2.0
        
        for board in all_floorboards:
            board_y_actual_width = board.get("actual_width", 0.0)
            plot_y0_board = wall_assembly_offset + board.get("position", 0.0) 
            plot_y1_board = plot_y0_board + board_y_actual_width
            nominal, is_custom = board.get("nominal", "N/A"), board.get("nominal") == "Custom"
            fill_color = FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else FLOORBOARD_STD_COLOR_VIZ
            comp_name_fb = ""
            if is_custom and not fb_cust_added: comp_name_fb = "FLOOR_Custom_Board"; fb_cust_added = True
            elif not is_custom and not fb_std_added: comp_name_fb = "FLOOR_Standard_Board"; fb_std_added = True
            
            components_top.append({"type": "rect", "x0": plot_x0_boards, "y0": plot_y0_board, "x1": plot_x1_boards, "y1": plot_y1_board,
                                   "fillcolor": fill_color, "line_color": FLOORBOARD_OUTLINE_COLOR_VIZ, 
                                   "legend_name": comp_name_fb, "layer": "above"})
            if board_y_actual_width > 0.5:
                annotations_top.append({
                    "x": 0, 
                    "y": (plot_y0_board + plot_y1_board) / 2.0, 
                    "text": nx_annot(f'{nominal} ({board_y_actual_width:.2f}"W)', f"ATTR_Board_Nominal_{nominal.replace('x','')}W"),
                    "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, 
                    "color": NX_ANNOT_FONT_COLOR if is_custom else DEFAULT_COMPONENT_FONT_COLOR_DARK, 
                    "bgcolor": DEFAULT_ANNOT_BGCOLOR_LIGHT if is_custom else "rgba(0,0,0,0)"
                })
        
        if abs(fb_center_gap_viz) > FLOAT_TOLERANCE_VIZ:
            last_board_y_top = wall_assembly_offset + floor_results.get("calculated_span_covered", 0) - fb_center_gap_viz \
                               if floor_results.get("calculated_span_covered",0) > 0 else wall_assembly_offset
            gap_start_y_plot = last_board_y_top
            gap_end_y_plot = gap_start_y_plot + fb_center_gap_viz
            if gap_end_y_plot > gap_start_y_plot + FLOAT_TOLERANCE_VIZ:
                comp_name_gap = f'GAP_Center ({fb_center_gap_viz:.3f}")' if not fb_gap_added else ""
                fb_gap_added=True
                components_top.append({"type":"rect", "x0": plot_x0_boards, "y0": gap_start_y_plot, "x1": plot_x1_boards, "y1": gap_end_y_plot, 
                                       "fillcolor": GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, 
                                       "legend_name": comp_name_gap, "layer":"above"})
                gap_annot_y = (gap_start_y_plot + gap_end_y_plot) / 2.0
                annotations_top.append({
                    "x": 0, "y": gap_annot_y, 
                    "text": nx_annot(f"Gap\n{fb_center_gap_viz:.3f}\"", "VAR_Floor_Center_Gap"), 
                    "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, 
                    "bgcolor": "rgba(255,255,255,0.0)"})

        annotations_top.append({"x": 0, "y": - (crate_length * 0.05), 
                                "text": nx_annot(f'Overall Skid Span (X): {overall_skid_span:.2f}"', "VAR_Overall_Skid_Span"), 
                                "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_top.append({"x": plot_x0_boards - abs(plot_x0_boards*0.05) - 5, "y": crate_length / 2.0, 
                                "text": nx_annot(f'Crate Len (Y): {crate_length:.2f}"', "OUT_Crate_Length"), 
                                "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                                "textangle": -90, "xanchor": "center", "xshift":-15})
        annotations_top.append({"x": 0, "y": wall_assembly_offset * 0.5, 
                                "text": nx_annot(f'Offset: {wall_assembly_offset:.2f}"', "VAR_Wall_Assy_Offset"), 
                                "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "yanchor":"middle"})
        annotations_top.append({"x": 0, "y": crate_length - wall_assembly_offset * 0.5, 
                                "text": nx_annot(f'Offset: {wall_assembly_offset:.2f}"', "VAR_Wall_Assy_Offset"), 
                                "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "yanchor":"middle"})
        
        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Top_View_XY{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Crate_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Crate_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, overall_skid_span, crate_length, components_top, annotations_top, 
                                    xlabel_html=xlabel_html, ylabel_html=ylabel_html)
        return fig
    except Exception as e: 
        log.error("Failed to create Base Top View figure", exc_info=True)
        return None 

def _create_base_front_view_fig(skid_results, floor_results, overall_dims):
    try:
        skid_w = skid_results.get('skid_width')
        skid_h = skid_results.get('skid_height')
        skid_x_positions = skid_results.get('skid_positions') 
        overall_skid_span = overall_dims.get('overall_skid_span') 
        floorboard_thick = STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS

        if not all([skid_w is not None, skid_h is not None, skid_x_positions is not None, overall_skid_span is not None]): 
            raise ValueError("Missing dimensions for base front view")
        if not skid_x_positions: raise ValueError("Skid positions are empty for base front view.")

        plot_height_hint_front = skid_h + floorboard_thick + skid_h*0.2 
        components_front, annotations_front = [], []
        skid_prof_added = False
        
        for x_center_rel in skid_x_positions:
            x0, x1 = x_center_rel - skid_w / 2.0, x_center_rel + skid_w / 2.0
            z0, z1 = 0.0, skid_h
            components_front.append({"type":"rect", "x0": x0, "y0": z0, "x1": x1, "y1": z1, 
                                     "fillcolor": SKID_COLOR_VIZ, "line_color": SKID_OUTLINE_COLOR_VIZ, 
                                     "legend_name": "SKID_Profile" if not skid_prof_added else "", "layer": "below"})
            skid_prof_added = True
        
        fb_x0 = -overall_skid_span / 2.0
        fb_x1 = overall_skid_span / 2.0
        fb_z0, fb_z1 = skid_h, skid_h + floorboard_thick
        components_front.append({"type":"rect", "x0": fb_x0, "y0": fb_z0, "x1": fb_x1, "y1": fb_z1, 
                                 "fillcolor": FLOORBOARD_STD_COLOR_VIZ, "line_color": FLOORBOARD_OUTLINE_COLOR_VIZ, 
                                 "legend_name": "FLOOR_Layer_Profile", "layer": "above"})

        total_base_height = skid_h + floorboard_thick
        annotations_front.append({"x": 0, "y": -plot_height_hint_front*0.05, 
                                  "text": nx_annot(f'Overall Skid Span (X): {overall_skid_span:.2f}"', "VAR_Overall_Skid_Span"), 
                                  "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_front.append({"x": fb_x0 - abs(fb_x0*0.05) - 5, "y": total_base_height / 2.0, 
                                  "text": nx_annot(f'Total H (Z): {total_base_height:.2f}"', "DIM_Base_Assy_Height"), 
                                  "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                                  "textangle": -90, "xanchor": "center", "xshift":-15})
        annotations_front.append({"x": 0, "y": skid_h / 2.0, 
                                  "text": nx_annot(f'Skid H: {skid_h:.2f}"', "ATTR_Skid_Height"), 
                                  "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR})
        annotations_front.append({"x": 0, "y": skid_h + floorboard_thick / 2.0, 
                                  "text": nx_annot(f'Floor T: {floorboard_thick:.3f}"', "ATTR_Floor_Thickness"), 
                                  "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR})
        
        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Front_View_XZ{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Crate_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, overall_skid_span, plot_height_hint_front, components_front, annotations_front, 
                                    xlabel_html=xlabel_html, ylabel_html=ylabel_html)
        return fig
    except Exception as e: 
        log.error("Failed to create Base Front View figure", exc_info=True)
        return None

def _create_base_side_view_fig(skid_results, floor_results, overall_dims, ui_inputs):
    try:
        panel_thickness = ui_inputs.get('panel_thickness', DEFAULT_PANEL_THICKNESS_UI)
        wall_cleat_thickness = ui_inputs.get('wall_cleat_thickness', DEFAULT_CLEAT_NOMINAL_THICKNESS)
        wall_assembly_offset = panel_thickness + wall_cleat_thickness
        skid_h = skid_results.get('skid_height')
        floorboard_thick = STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS
        floorboard_layout_span_target = floor_results.get("target_span_along_length") 
        all_floorboards = floor_results.get("floorboards", [])
        fb_center_gap_viz = floor_results.get("center_gap", 0.0)
        crate_length = overall_dims.get('length') 

        if not all([skid_h is not None, floorboard_thick is not None, floorboard_layout_span_target is not None, all_floorboards is not None, crate_length is not None]):
            raise ValueError("Missing dimensions for base side view")

        plot_width_hint_side, plot_height_hint_side = crate_length, skid_h + floorboard_thick + skid_h*0.2
        components_side, annotations_side = [], []
        fb_std_added_side, fb_cust_added_side, fb_gap_added_side = False, False, False
        
        skid_y0_plot, skid_y1_plot = 0.0, crate_length 
        skid_z0_plot, skid_z1_plot = 0.0, skid_h      
        components_side.append({"type":"rect", "x0": skid_y0_plot, "y0": skid_z0_plot, "x1": skid_y1_plot, "y1": skid_z1_plot, 
                                "fillcolor": SKID_COLOR_VIZ,"opacity":0.7, 
                                "line_color": SKID_OUTLINE_COLOR_VIZ, 
                                "legend_name": "SKID_Profile_Side", "layer": "below"})

        for board in all_floorboards:
            board_y_actual_width = board.get("actual_width", 0.0)
            plot_y0_board = wall_assembly_offset + board.get("position", 0.0) 
            plot_y1_board = plot_y0_board + board_y_actual_width
            plot_z0_board, plot_z1_board = skid_h, skid_h + floorboard_thick 
            
            nominal, is_custom = board.get("nominal", "N/A"), board.get("nominal") == "Custom"
            fill_color = FLOORBOARD_CUSTOM_COLOR_VIZ if is_custom else FLOORBOARD_STD_COLOR_VIZ
            comp_name_fb_side = ""
            if is_custom and not fb_cust_added_side: comp_name_fb_side = "FLOOR_Custom_Board_Profile"; fb_cust_added_side = True
            elif not is_custom and not fb_std_added_side: comp_name_fb_side = "FLOOR_Std_Board_Profile"; fb_std_added_side = True
            
            components_side.append({"type":"rect", "x0": plot_y0_board, "y0": plot_z0_board, "x1": plot_y1_board, "y1": plot_z1_board, 
                                    "fillcolor": fill_color, "line_color": FLOORBOARD_OUTLINE_COLOR_VIZ, 
                                    "legend_name": comp_name_fb_side, "layer": "above"})
            if board_y_actual_width > 0.5: 
                annotations_side.append({
                    "x": (plot_y0_board + plot_y1_board) / 2.0, 
                    "y": (plot_z0_board + plot_z1_board) / 2.0, 
                    "text": nx_annot(f'{board_y_actual_width:.2f}"W', f"ATTR_Board_{nominal.replace('x','')}W"), 
                    "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, 
                    "color": NX_ANNOT_FONT_COLOR if is_custom else DEFAULT_COMPONENT_FONT_COLOR_DARK, 
                    "bgcolor": DEFAULT_ANNOT_BGCOLOR_LIGHT if is_custom else "rgba(0,0,0,0)"})
        
        if abs(fb_center_gap_viz) > FLOAT_TOLERANCE_VIZ:
            last_board_y_top = wall_assembly_offset + floor_results.get("calculated_span_covered", 0) - fb_center_gap_viz \
                               if floor_results.get("calculated_span_covered",0) > 0 else wall_assembly_offset
            gap_start_y_plot = last_board_y_top
            gap_end_y_plot = gap_start_y_plot + fb_center_gap_viz
            if gap_end_y_plot > gap_start_y_plot + FLOAT_TOLERANCE_VIZ:
                comp_name_gap_side = f'GAP_Center_Profile ({fb_center_gap_viz:.3f}")' if not fb_gap_added_side else ""
                fb_gap_added_side=True
                components_side.append({"type":"rect", "x0": gap_start_y_plot, "y0": skid_h, "x1": gap_end_y_plot, "y1": skid_h + floorboard_thick, 
                                        "fillcolor": GAP_COLOR_VIZ, "line_width": 0, "opacity": 0.7, 
                                        "legend_name": comp_name_gap_side, "layer":"above"})
                annotations_side.append({
                    "x": (gap_start_y_plot + gap_end_y_plot) / 2.0, 
                    "y": skid_h + floorboard_thick / 2.0, 
                    "text": nx_annot(f"{fb_center_gap_viz:.3f}\"", "VAR_Floor_Center_Gap"), 
                    "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR})

        total_base_height_side = skid_h + floorboard_thick
        annotations_side.append({"x": crate_length / 2.0, "y": -plot_height_hint_side*0.05, 
                                 "text": nx_annot(f'Crate Length (Y): {crate_length:.2f}"', "OUT_Crate_Length"), 
                                 "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, "yanchor": "top", "yshift":-5})
        annotations_side.append({"x": -plot_width_hint_side*0.05 - 5, "y": total_base_height_side / 2.0, 
                                 "text": nx_annot(f'Total H (Z): {total_base_height_side:.2f}"', "DIM_Base_Assy_Height"), 
                                 "size": DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color": NX_ANNOT_FONT_COLOR, 
                                 "textangle": -90, "xanchor": "center", "xshift":-15})
        
        annotations_side.append({"x": wall_assembly_offset + floorboard_layout_span_target / 2.0, 
                                 "y": skid_h + floorboard_thick + plot_height_hint_side*0.02, 
                                 "text": nx_annot(f'Floorboard Layout Span: {floorboard_layout_span_target:.2f}"', "VAR_Floor_Target_Span"), 
                                 "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "yanchor":"bottom"})
        annotations_side.append({"x": wall_assembly_offset / 2.0, 
                                 "y": skid_h + floorboard_thick + plot_height_hint_side*0.02, 
                                 "text": nx_annot(f'Offset: {wall_assembly_offset:.2f}"', "VAR_Wall_Assy_Offset"), 
                                 "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "yanchor":"bottom"})
        annotations_side.append({"x": crate_length - wall_assembly_offset / 2.0, 
                                 "y": skid_h + floorboard_thick + plot_height_hint_side*0.02, 
                                 "text": nx_annot(f'Offset: {wall_assembly_offset:.2f}"', "VAR_Wall_Assy_Offset"), 
                                 "size": DEFAULT_ANNOT_FONT_SIZE_SMALL, "color": NX_ANNOT_FONT_COLOR, "yanchor":"bottom"})

        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Side_View_YZ{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Crate_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, crate_length, plot_height_hint_side, components_side, annotations_side, 
                                    xlabel_html=xlabel_html, ylabel_html=ylabel_html)
        return fig
    except Exception as e: 
        log.error("Failed to create Base Side View figure", exc_info=True)
        return None


# --- FIGURE GENERATION Functions (New Structure) ---
def generate_base_assembly_figures(skid_results, floor_results, wall_results, overall_dims, ui_inputs):
    fig_top, fig_front, fig_side = None, None, None
    skid_status = skid_results.get("status", "UNKNOWN") if skid_results else "NOT RUN"
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
        fig_top, fig_front, fig_side = None, None, None
    
    return fig_top, fig_front, fig_side

def generate_wall_panel_figures(wall_panel_data, panel_label_base, ui_inputs, overall_dims):
    fig_front, fig_profile = None, None
    assy_label_nx = f"{NX_LABEL_STYLE_HTML_OPEN}{panel_label_base.upper().replace(' ', '_')}_ASSY{NX_LABEL_STYLE_HTML_CLOSE}"

    if not wall_panel_data or wall_panel_data.get("panel_width", 0) == 0:
        log.warning(f"{assy_label_nx} figures not generated: Panel data invalid or width is zero.")
        return None, None 

    try:
        fig_front, error_msg_f = _create_panel_assembly_figure("Front", wall_panel_data, panel_label_base)
        fig_profile, error_msg_p = _create_panel_assembly_figure("Profile", wall_panel_data, panel_label_base)
        
        if error_msg_f: log.warning(f"Error generating Front view for {assy_label_nx}: {error_msg_f}")
        if error_msg_p: log.warning(f"Error generating Profile view for {assy_label_nx}: {error_msg_p}")
    except Exception as e:
        log.error(f"Error generating {assy_label_nx} figures: {e}", exc_info=True)
        fig_front, fig_profile = None, None 
    
    return fig_front, fig_profile

def generate_top_panel_figures(top_panel_data, ui_inputs, overall_dims):
    fig_front, fig_profile = None, None
    assy_label_nx = f"{NX_LABEL_STYLE_HTML_OPEN}CAP_PANEL_ASSY{NX_LABEL_STYLE_HTML_CLOSE}" 

    if not top_panel_data or top_panel_data.get("status") not in ["OK", "WARNING"]:
        status_msg = top_panel_data.get('status', 'N/A') if top_panel_data else 'N/A'
        log.warning(f"{assy_label_nx} figures not generated: Data invalid or calculation not successful (Status: {status_msg}).")
        return None, None

    try:
        fig_front, error_msg_f = _create_panel_assembly_figure("Front", top_panel_data, "CAP_PANEL")
        fig_profile, error_msg_p = _create_panel_assembly_figure("Profile", top_panel_data, "CAP_PANEL")

        if error_msg_f: log.warning(f"Error generating Front view for {assy_label_nx}: {error_msg_f}")
        if error_msg_p: log.warning(f"Error generating Profile view for {assy_label_nx}: {error_msg_p}")
    except Exception as e:
        log.error(f"Error generating {assy_label_nx} figures: {e}", exc_info=True)
        fig_front, fig_profile = None, None
        
    return fig_front, fig_profile
