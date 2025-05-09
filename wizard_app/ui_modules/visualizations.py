# wizard_app/ui_modules/visualizations.py
# REV: R8 - Corrected ValueError for Klimp shape layer property to "above".
"""
Handles the generation and display of layout schematics for AutoCrate Wizard.
Provides orthographic views for Base, Wall, and Top assemblies.
Uses centralized styling, coordinate systems, and includes variable annotations.
"""
import streamlit as st
import plotly.graph_objects as go
import math
import logging

try:
    from wizard_app import config
except ImportError:
    config = None 
    logging.warning("visualizations.py: config module not found. Using fallback style values.")

log = logging.getLogger(__name__)

# --- Style and Config Fallbacks ---
NX_LABEL_STYLE = getattr(config, 'NX_LABEL_STYLE', "color:green; font-weight:bold; font-family: 'Courier New', Courier, monospace;")
NX_LABEL_STYLE_HTML_OPEN = getattr(config, 'NX_LABEL_STYLE_HTML_OPEN', f"<span style='{NX_LABEL_STYLE}'>")
NX_LABEL_STYLE_HTML_CLOSE = getattr(config, 'NX_LABEL_STYLE_HTML_CLOSE', "</span>")
NX_ANNOT_FONT_COLOR = "green"

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
DEFAULT_CLEAT_FONT_COLOR = getattr(config, 'CLEAT_FONT_COLOR', '#FFFFFF')
DEFAULT_ANNOT_BGCOLOR_DARK = getattr(config, 'ANNOT_BGCOLOR_DARK', 'rgba(0,0,0,0.5)')
DEFAULT_ANNOT_BGCOLOR_LIGHT = getattr(config, 'ANNOT_BGCOLOR_LIGHT', 'rgba(255,255,255,0.7)')
FLOAT_TOLERANCE_VIZ = getattr(config, 'FLOAT_TOLERANCE', 1e-6)

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

DEFAULT_DECAL_BACKGROUND_COLOR_VIZ = getattr(config, 'DEFAULT_DECAL_BACKGROUND_COLOR', 'rgba(255, 255, 224, 0.7)')
DEFAULT_DECAL_TEXT_COLOR_VIZ = getattr(config, 'DEFAULT_DECAL_TEXT_COLOR', 'black')
DEFAULT_DECAL_FONT_SIZE_VIZ = getattr(config, 'DEFAULT_DECAL_FONT_SIZE', 12) 
DEFAULT_DECAL_BORDER_COLOR_VIZ = getattr(config, 'DEFAULT_DECAL_BORDER_COLOR', 'grey')
DEFAULT_DECAL_BORDER_WIDTH_VIZ = getattr(config, 'DEFAULT_DECAL_BORDER_WIDTH', 1)
KLIMP_COLOR_VIZ = getattr(config, 'KLIMP_COLOR_VIZ', 'rgba(100, 100, 100, 0.8)')


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
            layer=comp.get("layer", "above"), # Default layer, can be overridden by specific components
            name=comp.get("name", "")
        )
        min_x_data, max_x_data = min(min_x_data, x0, x1), max(max_x_data, x0, x1)
        min_y_data, max_y_data = min(min_y_data, y0, y1), max(max_y_data, y0, y1)
        comp_name_for_legend = comp.get("legend_name", comp.get("name"))
        if comp_name_for_legend and comp_name_for_legend not in legend_items_added:
            marker_symbol = 'line-ns' if shape_type == 'line' else 'square'
            marker_color = comp.get("fillcolor", "rgba(0,0,0,0)")
            if marker_color == "rgba(0,0,0,0)" and shape_type == 'line': marker_color = comp.get("line_color", DEFAULT_OUTLINE_COLOR)
            elif marker_color == "rgba(0,0,0,0)": marker_color = DEFAULT_OUTLINE_COLOR
            fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', name=comp_name_for_legend, marker=dict(color=marker_color, size=10, symbol=marker_symbol, line=dict(color=comp.get("line_color", DEFAULT_OUTLINE_COLOR), width=1))))
            legend_items_added.add(comp_name_for_legend)
    for ann in annotations:
        found_elements = True; x_pos, y_pos = ann.get("x"), ann.get("y"); y_anchor_val = ann.get("yanchor", "middle")
        if y_anchor_val == "center": y_anchor_val = "middle"
        fig.add_annotation(
            x=x_pos, y=y_pos, text=ann.get("text", ""), showarrow=ann.get("showarrow", False),
            font=dict(size=ann.get("size", DEFAULT_ANNOT_FONT_SIZE_NORMAL), color=ann.get("color", DEFAULT_COMPONENT_FONT_COLOR_DARK)),
            align=ann.get("align", "center"), bgcolor=ann.get("bgcolor", "rgba(255,255,255,0)"),
            xanchor=ann.get("xanchor", "center"), yanchor=y_anchor_val,
            yshift=ann.get("yshift", 0), xshift=ann.get("xshift", 0), textangle=ann.get("textangle", 0)
        )
        text_width_approx, text_height_approx = len(str(ann.get("text", ""))) * ann.get("size", 10) * 0.3, ann.get("size", 10) * 0.5
        if x_pos is not None: min_x_data, max_x_data = min(min_x_data, x_pos - text_width_approx), max(max_x_data, x_pos + text_width_approx)
        if y_pos is not None: min_y_data, max_y_data = min(min_y_data, y_pos - text_height_approx), max(max_y_data, y_pos + text_height_approx)
    if not found_elements: min_x_data, max_x_data, min_y_data, max_y_data = 0, width_hint, 0, height_hint
    actual_data_width, actual_data_height = max(max_x_data - min_x_data, 1.0), max(max_y_data - min_y_data, 1.0)
    plot_min_x = min(min_x_data, 0 - axis_visibility_offset) if min_x_data > -1 else min_x_data
    plot_max_x = max(max_x_data, 0 + axis_visibility_offset) if max_x_data < 1 else max_x_data
    plot_min_y = min(min_y_data, 0 - axis_visibility_offset) if min_y_data > -1 else min_y_data
    plot_max_y = max(max_y_data, 0 + axis_visibility_offset) if max_y_data < 1 else max_y_data
    padding_x, padding_y = max(actual_data_width * 0.15, 10), max(actual_data_height * 0.15, 10)
    x_range, y_range = [plot_min_x - padding_x, plot_max_x + padding_x], [plot_min_y - padding_y, plot_max_y + padding_y]
    plot_aspect_ratio = actual_data_height / actual_data_width if actual_data_width > 0 else 1
    dynamic_plot_height = max(450, min(800, int(550 * plot_aspect_ratio if plot_aspect_ratio < 1.5 else 550 * 1.5)))
    fig.update_layout(
        title=dict(text=title_html, font=dict(size=DEFAULT_TITLE_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK)),
        xaxis=dict(range=x_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_AXIS_ZERO_LINE_COLOR, showticklabels=True, tickfont=dict(size=DEFAULT_TICK_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK), visible=True, fixedrange=False, title_text=xlabel_html, title_font=dict(size=DEFAULT_AXIS_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK)),
        yaxis=dict(range=y_range, showgrid=False, zeroline=True, zerolinewidth=1, zerolinecolor=DEFAULT_AXIS_ZERO_LINE_COLOR, showticklabels=True, tickfont=dict(size=DEFAULT_TICK_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK), visible=True, fixedrange=False, scaleanchor="x", scaleratio=1, title_text=ylabel_html, title_font=dict(size=DEFAULT_AXIS_LABEL_FONT_SIZE, color=DEFAULT_COMPONENT_FONT_COLOR_DARK)),
        plot_bgcolor='white', paper_bgcolor='white', margin=dict(l=60, r=30, t=80, b=60), height=dynamic_plot_height,
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=DEFAULT_LEGEND_FONT_COLOR, size=DEFAULT_LEGEND_FONT_SIZE))
    )
    return fig

def nx_annot(text_content, nx_var_name=""):
    if nx_var_name: return f"{text_content} ({NX_LABEL_STYLE_HTML_OPEN}{nx_var_name}{NX_LABEL_STYLE_HTML_CLOSE})"
    return text_content

def _create_panel_assembly_figure(view_type, panel_data, panel_label_base="Panel"):
    if not panel_data: return None, f"{panel_label_base} {view_type} data invalid."
    is_top_panel="cap_panel_width" in panel_data
    plywood_pieces_data_list = []
    if is_top_panel:
        panel_w, panel_h, plywood_t = panel_data.get("cap_panel_width",0), panel_data.get("cap_panel_length",0), panel_data.get("cap_panel_thickness",0)
        cleat_spec, panel_color, cleat_color = panel_data.get("cap_cleat_spec",{}), CAP_PANEL_COLOR_VIZ, CAP_CLEAT_COLOR_VIZ
        fig_title_nx = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_{panel_label_base.upper().replace(' ','_')}_{view_type.upper()}{NX_LABEL_STYLE_HTML_CLOSE}"
        front_xlabel_nx, front_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Cap_Panel_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Cap_Panel_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        profile_xlabel_nx, profile_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Cap_Panel_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Cap_Thickness_Assy{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        all_cleats_for_front_view = []
        lc, tc = panel_data.get("longitudinal_cleats",{}), panel_data.get("transverse_cleats",{})
        if lc.get("count",0)>0: [all_cleats_for_front_view.append({"orientation":"vertical", "length":lc.get("cleat_length_each"), "width":lc.get("cleat_width_each"), "thickness":lc.get("cleat_thickness_each"), "position_x":pos_x, "position_y":0, "type":"longitudinal_cleat"}) for pos_x in lc.get("positions",[])]
        if tc.get("count",0)>0: [all_cleats_for_front_view.append({"orientation":"horizontal", "length":tc.get("cleat_length_each"), "width":tc.get("cleat_width_each"), "thickness":tc.get("cleat_thickness_each"), "position_x":0, "position_y":pos_y, "type":"transverse_cleat"}) for pos_y in tc.get("positions",[])]
        plywood_pieces_data_list = [{"x0":0, "y0":0, "x1":panel_w, "y1":panel_h, "label":"Cap_Sheathing"}]
    else: # Wall Panel
        panel_w, panel_h, plywood_t = panel_data.get("panel_width",0), panel_data.get("panel_height",0), panel_data.get("plywood_thickness",0)
        all_cleats_for_front_view, plywood_pieces_input = panel_data.get("cleats",[]), panel_data.get("plywood_pieces",[])
        cleat_spec, panel_color, cleat_color = panel_data.get("cleat_spec",{}), WALL_PANEL_COLOR_VIZ, WALL_CLEAT_COLOR_VIZ
        fig_title_nx = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_{panel_label_base.upper().replace(' ','_')}_{view_type.upper()}{NX_LABEL_STYLE_HTML_CLOSE}"
        front_xlabel_nx, front_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Panel_Width_Or_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Panel_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        profile_xlabel_nx, profile_ylabel_nx = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Panel_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Panel_Thickness_Assy{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        for p in plywood_pieces_input: plywood_pieces_data_list.append({"x0":p["x0"], "y0":p["y0"], "x1":p["x1"], "y1":p["y1"], "label":"Plywood_Piece"})
    
    cleat_actual_thickness = cleat_spec.get("thickness", DEFAULT_CLEAT_NOMINAL_THICKNESS)
    cleat_actual_width = cleat_spec.get("width", DEFAULT_CLEAT_NOMINAL_WIDTH)

    if panel_w <= FLOAT_TOLERANCE_VIZ or panel_h <= FLOAT_TOLERANCE_VIZ: return None, f"{panel_label_base} dimensions invalid."
    components, annotations, fig = [], [], None
    if view_type == "Front":
        cleats_lgnd, ply_lgnd, splice_lgnd, decal_lgnd, klimp_lgnd = False, False, False, False, False
        for i, piece in enumerate(plywood_pieces_data_list): components.append({"type":"rect", "x0":piece["x0"], "y0":piece["y0"], "x1":piece["x1"], "y1":piece["y1"], "fillcolor":panel_color, "line_color":DEFAULT_OUTLINE_COLOR, "line_width":0.5, "legend_name":"Plywood Sheathing" if not ply_lgnd else "","layer":"below"}); ply_lgnd=True
        if not is_top_panel and len(plywood_pieces_data_list) > 1:
            xs=sorted(list(set(p["x0"] for p in plywood_pieces_data_list).union(set(p["x1"] for p in plywood_pieces_data_list))))
            for xb in xs:
                if FLOAT_TOLERANCE_VIZ<xb<panel_w-FLOAT_TOLERANCE_VIZ: components.append({"type":"line","x0":xb,"y0":0,"x1":xb,"y1":panel_h,"line_color":DEFAULT_AXIS_ZERO_LINE_COLOR,"line_width":1.5,"line_dash":"dash","legend_name":"Plywood Splice Line" if not splice_lgnd else "","layer":"above"}); splice_lgnd=True
            ys=sorted(list(set(p["y0"] for p in plywood_pieces_data_list).union(set(p["y1"] for p in plywood_pieces_data_list))))
            for yb in ys:
                if FLOAT_TOLERANCE_VIZ<yb<panel_h-FLOAT_TOLERANCE_VIZ: components.append({"type":"line","x0":0,"y0":yb,"x1":panel_w,"y1":yb,"line_color":DEFAULT_AXIS_ZERO_LINE_COLOR,"line_width":1.5,"line_dash":"dash","legend_name":"Plywood Splice Line" if not splice_lgnd else "","layer":"above"}); splice_lgnd=True
        
        if not is_top_panel and "decals" in panel_data:
            for decal in panel_data["decals"]:
                dx0, dy0, dw, dh = decal.get("x_coord",0), decal.get("y_coord",0), decal.get("width",0), decal.get("height",0)
                components.append({"type":"rect", "x0":dx0, "y0":dy0, "x1":dx0+dw, "y1":dy0+dh, "fillcolor":decal.get("background_color",DEFAULT_DECAL_BACKGROUND_COLOR_VIZ), "line_color":decal.get("border_color",DEFAULT_DECAL_BORDER_COLOR_VIZ), "line_width":decal.get("border_width",DEFAULT_DECAL_BORDER_WIDTH_VIZ), "opacity":0.9, "legend_name":"Decal/Stencil" if not decal_lgnd else "","layer":"above"}); decal_lgnd=True
                if decal.get("text_content"): annotations.append({"x":dx0+dw/2.0, "y":dy0+dh/2.0, "text":decal.get("text_content"), "size":decal.get("font_size",DEFAULT_DECAL_FONT_SIZE_VIZ), "color":decal.get("text_color",DEFAULT_DECAL_TEXT_COLOR_VIZ), "textangle":decal.get("angle",0), "showarrow":False, "align":"center", "yanchor":"middle"})

        klimps_to_render = panel_data.get("klimps") 
        if is_top_panel and "cap_klimps" in panel_data: 
            klimps_to_render = panel_data.get("cap_klimps")
        
        if klimps_to_render:
            for klimp in klimps_to_render:
                kx, ky = klimp.get("x_coord", 0), klimp.get("y_coord", 0) 
                k_size = klimp.get("size", 1.0) 
                k_x0, k_y0 = kx - k_size / 2.0, ky - k_size / 2.0
                k_x1, k_y1 = kx + k_size / 2.0, ky + k_size / 2.0
                components.append({
                    "type":"rect", "x0":k_x0, "y0":k_y0, "x1":k_x1, "y1":k_y1, 
                    "fillcolor":KLIMP_COLOR_VIZ, 
                    "line_color":DEFAULT_OUTLINE_COLOR, "line_width":0.5, 
                    "legend_name":"Klimp Fastener" if not klimp_lgnd else "",
                    "layer":"above" # CORRECTED: Was "top", changed to "above"
                }); klimp_lgnd=True

        for cleat in all_cleats_for_front_view:
            c_orient, c_len = cleat.get("orientation"), cleat.get("length")
            c_rect_w = cleat.get("width") if is_top_panel else cleat_actual_width
            c_x_rel, c_y_rel = cleat.get("position_x",0), cleat.get("position_y",0)
            abs_cx, abs_cy = panel_w/2.0+c_x_rel, panel_h/2.0+c_y_rel
            if c_orient=="horizontal": x0,x1,y0,y1,txt = abs_cx-c_len/2.0, abs_cx+c_len/2.0, abs_cy-c_rect_w/2.0, abs_cy+c_rect_w/2.0, f'{c_len:.1f}"L'
            elif c_orient=="vertical": x0,x1,y0,y1,txt = abs_cx-c_rect_w/2.0, abs_cx+c_rect_w/2.0, abs_cy-c_len/2.0, abs_cy+c_len/2.0, f'{c_len:.1f}"H'
            else: log.warning(f"Unknown cleat orientation: {c_orient}"); continue
            components.append({"type":"rect", "x0":x0, "y0":y0, "x1":x1, "y1":y1, "fillcolor":cleat_color, "line_color":DEFAULT_OUTLINE_COLOR, "legend_name":"Framing Cleat" if not cleats_lgnd else "","layer":"above"}); cleats_lgnd=True
            if c_len>1.0 and c_rect_w>1.0: annotations.append({"x":abs_cx, "y":abs_cy, "text":txt, "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":DEFAULT_CLEAT_FONT_COLOR, "bgcolor":DEFAULT_ANNOT_BGCOLOR_DARK})
        dim_var_w = "DIM_Cap_Panel_Width" if is_top_panel else ("DIM_Panel_Width_End" if "BACK" in panel_label_base.upper() or "END" in panel_label_base.upper() else "DIM_Panel_Length_Side")
        dim_var_h = "DIM_Cap_Panel_Length" if is_top_panel else "DIM_Panel_Height_Used"
        annotations.extend([
            {"x":panel_w/2.0, "y":-(panel_h*0.05)-5, "text":nx_annot(f'{panel_w:.2f}"',dim_var_w), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"top", "yshift":-5},
            {"x":-(panel_w*0.05)-5, "y":panel_h/2.0, "text":nx_annot(f'{panel_h:.2f}"',dim_var_h), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "textangle":-90, "xanchor":"right", "xshift":-15}
        ])
        fig = create_schematic_view(fig_title_nx, panel_w, panel_h, components, annotations, front_xlabel_nx, front_ylabel_nx)
    elif view_type == "Profile":
        profile_plot_width = panel_h if is_top_panel else panel_h 
        profile_plot_height_assy = plywood_t + cleat_actual_thickness 
        components.append({"type": "rect", "x0": 0, "y0": 0, "x1": profile_plot_width, "y1": plywood_t, "fillcolor": panel_color, "line_color": DEFAULT_OUTLINE_COLOR, "legend_name": "Plywood Sheathing (Profile)", "layer":"below"})
        rep_cleat_w = cleat_actual_width 
        cleat_x0, cleat_x1 = (profile_plot_width/2.0)-(rep_cleat_w/2.0), (profile_plot_width/2.0)+(rep_cleat_w/2.0)
        components.append({"type":"rect", "x0": cleat_x0, "y0": plywood_t, "x1": cleat_x1, "y1": plywood_t + cleat_actual_thickness, "fillcolor":cleat_color, "line_color": DEFAULT_OUTLINE_COLOR, "legend_name": "Framing Cleat (Profile)"})
        dim_var_prof_len = "DIM_Cap_Panel_Length" if is_top_panel else "DIM_Panel_Height_Used"
        dim_var_ply_t = "DIM_Cap_Panel_Thickness" if is_top_panel else "DIM_Panel_Plywood_Thickness"
        dim_var_cleat_t = "ATTR_Cap_Cleat_Thickness" if is_top_panel else "ATTR_Wall_Cleat_Thickness"
        annotations.extend([
            {"x":profile_plot_width/2.0, "y":-(profile_plot_height_assy*0.05)-5, "text":nx_annot(f'{profile_plot_width:.2f}"',dim_var_prof_len), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"top", "yshift":-5},
            {"x":-(profile_plot_width*0.05)-5, "y":profile_plot_height_assy/2.0, "text":nx_annot(f'{profile_plot_height_assy:.2f}"',f"{dim_var_ply_t} + {dim_var_cleat_t}"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "textangle":-90, "xanchor":"right","xshift":-15},
            {"x":profile_plot_width*0.75, "y":plywood_t/2.0, "text":nx_annot(f'Plywood: {plywood_t:.2f}"',dim_var_ply_t), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "xanchor":"center"},
            {"x":profile_plot_width*0.75, "y":plywood_t+cleat_actual_thickness/2.0, "text":nx_annot(f'Cleat: {cleat_actual_thickness:.2f}"',dim_var_cleat_t), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "bgcolor":getattr(config,'ANNOT_BGCOLOR_DARK_FOR_GREEN_TEXT',DEFAULT_ANNOT_BGCOLOR_DARK) if NX_ANNOT_FONT_COLOR=="green" else DEFAULT_ANNOT_BGCOLOR_DARK, "xanchor":"center"}
        ])
        fig = create_schematic_view(fig_title_nx, profile_plot_width, profile_plot_height_assy, components, annotations, profile_xlabel_nx, profile_ylabel_nx)
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
        if not all([skid_w, skid_x_positions, overall_skid_span, all_floorboards is not None, crate_length]):
            raise ValueError("Missing critical dimensions for base top view")
        components_top, annotations_top = [], []
        skid_lgnd, fb_std_lgnd, fb_cust_lgnd, fb_gap_lgnd = False, False, False, False
        for x_center_rel in skid_x_positions:
            x0, x1 = x_center_rel - skid_w/2.0, x_center_rel + skid_w/2.0
            components_top.append({"type":"rect", "x0":x0, "y0":0.0, "x1":x1, "y1":crate_length, "fillcolor":SKID_COLOR_VIZ, "opacity":0.5, "line_color":SKID_OUTLINE_COLOR_VIZ, "line_width":0.5, "legend_name":"Skid Lumber" if not skid_lgnd else "","layer":"below"}); skid_lgnd=True
        plot_x0_boards, plot_x1_boards = -overall_skid_span/2.0, overall_skid_span/2.0
        for board in all_floorboards:
            b_actual_w = board.get("actual_width",0.0)
            plot_y0, plot_y1 = wall_assembly_offset+board.get("position",0.0), wall_assembly_offset+board.get("position",0.0)+b_actual_w
            nom, is_cust = board.get("nominal","N/A"), board.get("nominal")=="Custom"
            fill_c = FLOORBOARD_CUSTOM_COLOR_VIZ if is_cust else FLOORBOARD_STD_COLOR_VIZ
            lgnd_name = ""
            if is_cust and not fb_cust_lgnd: lgnd_name="Custom Floorboard"; fb_cust_lgnd=True
            elif not is_cust and not fb_std_lgnd: lgnd_name="Std. Floorboard"; fb_std_lgnd=True
            components_top.append({"type":"rect", "x0":plot_x0_boards, "y0":plot_y0, "x1":plot_x1_boards, "y1":plot_y1, "fillcolor":fill_c, "line_color":FLOORBOARD_OUTLINE_COLOR_VIZ, "legend_name":lgnd_name, "layer":"above"})
            if b_actual_w > 0.5: annotations_top.append({"x":0, "y":(plot_y0+plot_y1)/2.0, "text":nx_annot(f'{nom} ({b_actual_w:.2f}"W)',f"ATTR_Board_Nominal_{nom.replace('x','')}W"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR if is_cust else DEFAULT_COMPONENT_FONT_COLOR_DARK, "bgcolor":DEFAULT_ANNOT_BGCOLOR_LIGHT if is_cust else "rgba(0,0,0,0)"})
        if abs(fb_center_gap_viz) > FLOAT_TOLERANCE_VIZ:
            last_board_y_top = wall_assembly_offset + (floor_results.get("calculated_span_covered",0) - fb_center_gap_viz if floor_results.get("calculated_span_covered",0)>0 else 0)
            gap_y0, gap_y1 = last_board_y_top, last_board_y_top + fb_center_gap_viz
            if gap_y1 > gap_y0 + FLOAT_TOLERANCE_VIZ:
                lgnd_name = f'Center Gap ({fb_center_gap_viz:.3f}")' if not fb_gap_lgnd else ""; fb_gap_lgnd=True
                components_top.append({"type":"rect", "x0":plot_x0_boards, "y0":gap_y0, "x1":plot_x1_boards, "y1":gap_y1, "fillcolor":GAP_COLOR_VIZ, "line_width":0, "opacity":0.7, "legend_name":lgnd_name, "layer":"above"})
                annotations_top.append({"x":0, "y":(gap_y0+gap_y1)/2.0, "text":nx_annot(f"Gap\n{fb_center_gap_viz:.3f}\"", "VAR_Floor_Center_Gap"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "bgcolor":"rgba(255,255,255,0.0)"})
        annotations_top.extend([
            {"x":0, "y":-(crate_length*0.05)-5, "text":nx_annot(f'Overall Skid Span (X): {overall_skid_span:.2f}"',"VAR_Overall_Skid_Span"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"top", "yshift":-5},
            {"x":plot_x0_boards-abs(plot_x0_boards*0.05)-10, "y":crate_length/2.0, "text":nx_annot(f'Crate Len (Y): {crate_length:.2f}"',"OUT_Crate_Length"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "textangle":-90, "xanchor":"right", "xshift":-15},
            {"x":0, "y":wall_assembly_offset*0.5, "text":nx_annot(f'Offset: {wall_assembly_offset:.2f}"',"VAR_Wall_Assy_Offset"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"middle"},
            {"x":0, "y":crate_length-wall_assembly_offset*0.5, "text":nx_annot(f'Offset: {wall_assembly_offset:.2f}"',"VAR_Wall_Assy_Offset"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"middle"}
        ])
        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Top_View_XY{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html, ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Crate_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Crate_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, overall_skid_span, crate_length, components_top, annotations_top, xlabel_html, ylabel_html)
        return fig
    except Exception as e: log.error("Failed to create Base Top View figure", exc_info=True); return None

def _create_base_front_view_fig(skid_results, floor_results, overall_dims):
    try:
        skid_w, skid_h = skid_results.get('skid_width'), skid_results.get('skid_height')
        skid_x_pos, overall_skid_span = skid_results.get('skid_positions'), overall_dims.get('overall_skid_span')
        floor_t = STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS
        if not all([skid_w, skid_h, skid_x_pos, overall_skid_span]): raise ValueError("Missing dims for base front view")
        plot_h_hint = skid_h + floor_t + skid_h*0.2; components, annotations = [], []; skid_prof_lgnd=False
        for x_rel in skid_x_pos:
            x0,x1=x_rel-skid_w/2.0, x_rel+skid_w/2.0
            components.append({"type":"rect", "x0":x0, "y0":0.0, "x1":x1, "y1":skid_h, "fillcolor":SKID_COLOR_VIZ, "line_color":SKID_OUTLINE_COLOR_VIZ, "legend_name":"Skid (Profile)" if not skid_prof_lgnd else "","layer":"below"}); skid_prof_lgnd=True
        fb_x0, fb_x1 = -overall_skid_span/2.0, overall_skid_span/2.0
        components.append({"type":"rect", "x0":fb_x0, "y0":skid_h, "x1":fb_x1, "y1":skid_h+floor_t, "fillcolor":FLOORBOARD_STD_COLOR_VIZ, "line_color":FLOORBOARD_OUTLINE_COLOR_VIZ, "legend_name":"Floorboard Layer (Profile)", "layer":"above"})
        total_base_h = skid_h + floor_t
        annotations.extend([
            {"x":0, "y":-plot_h_hint*0.05-5, "text":nx_annot(f'Overall Skid Span (X): {overall_skid_span:.2f}"',"VAR_Overall_Skid_Span"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"top", "yshift":-5},
            {"x":fb_x0-abs(fb_x0*0.05)-10, "y":total_base_h/2.0, "text":nx_annot(f'Total H (Z): {total_base_h:.2f}"',"DIM_Base_Assy_Height"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "textangle":-90, "xanchor":"right", "xshift":-15},
            {"x":0, "y":skid_h/2.0, "text":nx_annot(f'Skid H: {skid_h:.2f}"',"ATTR_Skid_Height"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR},
            {"x":0, "y":skid_h+floor_t/2.0, "text":nx_annot(f'Floor T: {floor_t:.3f}"',"ATTR_Floor_Thickness"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR}
        ])
        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Front_View_XZ{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html, ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_X_DIM_Crate_Width{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, overall_skid_span, plot_h_hint, components, annotations, xlabel_html, ylabel_html)
        return fig
    except Exception as e: log.error("Failed to create Base Front View figure", exc_info=True); return None

def _create_base_side_view_fig(skid_results, floor_results, overall_dims, ui_inputs):
    try:
        panel_t, wall_cleat_t = ui_inputs.get('panel_thickness',DEFAULT_PANEL_THICKNESS_UI), ui_inputs.get('wall_cleat_thickness',DEFAULT_CLEAT_NOMINAL_THICKNESS)
        wall_assy_offset = panel_t + wall_cleat_t
        skid_h = skid_results.get('skid_height')
        floor_t, floor_target_span = STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS, floor_results.get("target_span_along_length")
        all_fb, fb_gap, crate_l = floor_results.get("floorboards",[]), floor_results.get("center_gap",0.0), overall_dims.get('length')
        if not all([skid_h, floor_t is not None, floor_target_span, all_fb is not None, crate_l]): raise ValueError("Missing dims for base side view")
        plot_w, plot_h = crate_l, skid_h+floor_t+skid_h*0.2; components,annotations=[],[]
        fb_std_lgnd, fb_cust_lgnd, fb_gap_lgnd = False,False,False
        components.append({"type":"rect", "x0":0.0, "y0":0.0, "x1":crate_l, "y1":skid_h, "fillcolor":SKID_COLOR_VIZ, "opacity":0.7, "line_color":SKID_OUTLINE_COLOR_VIZ, "legend_name":"Skid (Side Profile)", "layer":"below"})
        for board in all_fb:
            b_actual_w = board.get("actual_width",0.0)
            plot_x0, plot_x1 = wall_assy_offset+board.get("position",0.0), wall_assy_offset+board.get("position",0.0)+b_actual_w
            plot_z0, plot_z1 = skid_h, skid_h+floor_t
            nom, is_cust = board.get("nominal","N/A"), board.get("nominal")=="Custom"
            fill_c = FLOORBOARD_CUSTOM_COLOR_VIZ if is_cust else FLOORBOARD_STD_COLOR_VIZ
            lgnd_name=""
            if is_cust and not fb_cust_lgnd: lgnd_name="Custom Floorboard (Profile)"; fb_cust_lgnd=True
            elif not is_cust and not fb_std_lgnd: lgnd_name="Std. Floorboard (Profile)"; fb_std_lgnd=True
            components.append({"type":"rect", "x0":plot_x0, "y0":plot_z0, "x1":plot_x1, "y1":plot_z1, "fillcolor":fill_c, "line_color":FLOORBOARD_OUTLINE_COLOR_VIZ, "legend_name":lgnd_name, "layer":"above"})
            if b_actual_w > 0.5: annotations.append({"x":(plot_x0+plot_x1)/2.0, "y":(plot_z0+plot_z1)/2.0, "text":nx_annot(f'{b_actual_w:.2f}"W',f"ATTR_Board_{nom.replace('x','')}W"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR if is_cust else DEFAULT_COMPONENT_FONT_COLOR_DARK, "bgcolor":DEFAULT_ANNOT_BGCOLOR_LIGHT if is_cust else "rgba(0,0,0,0)"})
        if abs(fb_gap) > FLOAT_TOLERANCE_VIZ:
            last_board_x_top = wall_assy_offset + (floor_results.get("calculated_span_covered",0) - fb_gap if floor_results.get("calculated_span_covered",0)>0 else 0)
            gap_x0, gap_x1 = last_board_x_top, last_board_x_top + fb_gap
            if gap_x1 > gap_x0 + FLOAT_TOLERANCE_VIZ:
                lgnd_name = f'Center Gap (Profile {fb_gap:.3f}")' if not fb_gap_lgnd else ""; fb_gap_lgnd=True
                components.append({"type":"rect", "x0":gap_x0, "y0":skid_h, "x1":gap_x1, "y1":skid_h+floor_t, "fillcolor":GAP_COLOR_VIZ, "line_width":0, "opacity":0.7, "legend_name":lgnd_name, "layer":"above"})
                annotations.append({"x":(gap_x0+gap_x1)/2.0, "y":skid_h+floor_t/2.0, "text":nx_annot(f"{fb_gap:.3f}\"","VAR_Floor_Center_Gap"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR})
        total_base_h = skid_h+floor_t
        annotations.extend([
            {"x":crate_l/2.0, "y":-plot_h*0.05-5, "text":nx_annot(f'Crate Length (Y): {crate_l:.2f}"',"OUT_Crate_Length"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"top", "yshift":-5},
            {"x":-plot_w*0.05-10, "y":total_base_h/2.0, "text":nx_annot(f'Total H (Z): {total_base_h:.2f}"',"DIM_Base_Assy_Height"), "size":DEFAULT_ANNOT_FONT_SIZE_NORMAL, "color":NX_ANNOT_FONT_COLOR, "textangle":-90, "xanchor":"right", "xshift":-15},
            {"x":wall_assy_offset+floor_target_span/2.0, "y":skid_h+floor_t+plot_h*0.02, "text":nx_annot(f'Floorboard Layout Span: {floor_target_span:.2f}"',"VAR_Floor_Target_Span"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"bottom"},
            {"x":wall_assy_offset/2.0, "y":skid_h+floor_t+plot_h*0.02, "text":nx_annot(f'Offset: {wall_assy_offset:.2f}"',"VAR_Wall_Assy_Offset"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"bottom"},
            {"x":crate_l-wall_assy_offset/2.0, "y":skid_h+floor_t+plot_h*0.02, "text":nx_annot(f'Offset: {wall_assy_offset:.2f}"',"VAR_Wall_Assy_Offset"), "size":DEFAULT_ANNOT_FONT_SIZE_SMALL, "color":NX_ANNOT_FONT_COLOR, "yanchor":"bottom"}
        ])
        title_html = f"{NX_LABEL_STYLE_HTML_OPEN}FIG_Base_Assy_Side_View_YZ{NX_LABEL_STYLE_HTML_CLOSE}"
        xlabel_html, ylabel_html = f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Y_DIM_Crate_Length{NX_LABEL_STYLE_HTML_CLOSE} [in]", f"{NX_LABEL_STYLE_HTML_OPEN}AXIS_Z_DIM_Height{NX_LABEL_STYLE_HTML_CLOSE} [in]"
        fig = create_schematic_view(title_html, crate_l, plot_h, components, annotations, xlabel_html, ylabel_html)
        return fig
    except Exception as e: log.error("Failed to create Base Side View figure", exc_info=True); return None

# --- Main Figure Generation Functions ---
def generate_base_assembly_figures(skid_results, floor_results, wall_results, overall_dims, ui_inputs):
    fig_top, fig_front, fig_side = None, None, None
    if not (skid_results and skid_results.get("status") == "OK" and
            floor_results and floor_results.get("status") in ["OK", "WARNING"] and
            overall_dims and ui_inputs):
        log.warning("Base Assembly figures prerequisites not met.")
        return None, None, None
    try:
        fig_top = _create_base_top_view_fig(skid_results, floor_results, overall_dims, ui_inputs)
        fig_front = _create_base_front_view_fig(skid_results, floor_results, overall_dims)
        fig_side = _create_base_side_view_fig(skid_results, floor_results, overall_dims, ui_inputs)
    except Exception as e:
        log.error(f"Error generating Base Assembly figures: {e}", exc_info=True)
    return fig_top, fig_front, fig_side

def generate_wall_panel_figures(wall_panel_data, panel_label_base, ui_inputs, overall_dims):
    fig_front, fig_profile = None, None
    if not (wall_panel_data and wall_panel_data.get("panel_width", 0) > 0 and 
            ui_inputs and overall_dims):
        log.warning(f"Wall panel figures prerequisites not met for {panel_label_base}.")
        return None, None
    try:
        fig_front, err_f = _create_panel_assembly_figure("Front", wall_panel_data, panel_label_base)
        fig_profile, err_p = _create_panel_assembly_figure("Profile", wall_panel_data, panel_label_base)
        if err_f: log.warning(f"Error generating Front view for {panel_label_base}: {err_f}")
        if err_p: log.warning(f"Error generating Profile view for {panel_label_base}: {err_p}")
    except Exception as e:
        log.error(f"Error generating {panel_label_base} figures: {e}", exc_info=True)
    return fig_front, fig_profile

def generate_top_panel_figures(top_panel_data, ui_inputs, overall_dims):
    fig_front, fig_profile = None, None
    if not (top_panel_data and top_panel_data.get("status") in ["OK", "WARNING"] and
            ui_inputs and overall_dims):
        status_msg = top_panel_data.get('status', 'N/A') if top_panel_data else 'Data N/A'
        log.warning(f"Top panel figures prerequisites not met. Status: {status_msg}")
        return None, None
    try:
        fig_front, err_f = _create_panel_assembly_figure("Front", top_panel_data, "CAP_PANEL")
        fig_profile, err_p = _create_panel_assembly_figure("Profile", top_panel_data, "CAP_PANEL")
        if err_f: log.warning(f"Error generating Front view for CAP_PANEL: {err_f}")
        if err_p: log.warning(f"Error generating Profile view for CAP_PANEL: {err_p}")
    except Exception as e:
        log.error(f"Error generating CAP_PANEL figures: {e}", exc_info=True)
    return fig_front, fig_profile