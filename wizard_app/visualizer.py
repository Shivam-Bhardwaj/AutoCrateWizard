import plotly.graph_objects as go

def create_crate_figures(width, length, height, skid_count):
    # Top View
    fig_top = go.Figure()
    fig_top.add_shape(type="rect", x0=0, y0=0, x1=width, y1=length,
                      line=dict(color='blue', width=3), fillcolor='rgba(0,0,255,0.1)')

    skid_positions = []
    if skid_count > 0:
        if skid_count == 1:
            skid_positions = [width / 2]
        else:
            spacing = width / (skid_count + 1)
            skid_positions = [spacing * (i + 1) for i in range(skid_count)]

        for pos in skid_positions:
            fig_top.add_shape(type="rect",
                              x0=pos - 20, y0=0,
                              x1=pos + 20, y1=length,
                              fillcolor="brown", opacity=0.5, line=dict(color="brown"))
    fig_top.update_layout(title="Top View", xaxis_title="Width", yaxis_title="Length")

    # Side View
    fig_side = go.Figure()
    fig_side.add_shape(type="rect", x0=0, y0=0, x1=length, y1=height,
                       line=dict(color='blue', width=3), fillcolor='rgba(0,0,255,0.1)')
    fig_side.update_layout(title="Side View", xaxis_title="Length", yaxis_title="Height")

    # Front View
    fig_front = go.Figure()
    fig_front.add_shape(type="rect", x0=0, y0=0, x1=width, y1=height,
                        line=dict(color='blue', width=3), fillcolor='rgba(0,0,255,0.1)')

    for pos in skid_positions:
        fig_front.add_shape(type="rect",
                            x0=pos - 20, y0=0,
                            x1=pos + 20, y1=height * 0.1,
                            fillcolor="brown", opacity=0.5, line=dict(color="brown"))
    fig_front.update_layout(title="Front View", xaxis_title="Width", yaxis_title="Height")

    return fig_top, fig_side, fig_front
