import streamlit as st
import plotly.graph_objects as go
from math import ceil

# --- Core Calculation Logic ---
def calculate_skid_layout(prod_width_in, prod_weight_lbm, clearance_side=2.0, panel_thickness=0.25, cleat_thickness=0.75):
    MAX_SKIDS = 5
    # NX-style crate width logic
    crate_width = prod_width_in + 2 * clearance_side + 2 * panel_thickness + 2 * cleat_thickness
    usable_width = crate_width - 2 * (panel_thickness + cleat_thickness)

    if prod_weight_lbm <= 500:
        max_spacing = 30
    elif prod_weight_lbm <= 6000:
        max_spacing = 41
    elif prod_weight_lbm <= 12000:
        max_spacing = 28
    else:
        max_spacing = 24

    skid_count = min(MAX_SKIDS, ceil(usable_width / max_spacing))
    spacing_actual = 0 if skid_count <= 1 else usable_width / (skid_count - 1)
    start_x = -usable_width / 2
    skid_positions = [start_x + i * spacing_actual for i in range(skid_count)]
    skid_width = 3.5 if prod_weight_lbm <= 4500 else 5.5

    return {
        "crate_width": crate_width,
        "usable_width": usable_width,
        "skid_count": skid_count,
        "spacing_actual": spacing_actual,
        "skid_positions": skid_positions,
        "skid_width": skid_width,
        "max_spacing": max_spacing
    }

# --- Visualization Logic ---
def create_crate_figures(crate_width, skid_positions, skid_width):
    skid_height = 3.5
    canvas_width = max(150, crate_width + 10)

    fig = go.Figure()

    fig.add_shape(type="rect",
                  x0=-crate_width/2, y0=0, x1=crate_width/2, y1=skid_height,
                  line=dict(color='blue', width=1, dash='dash'),
                  fillcolor='rgba(0,0,255,0.02)', layer="below")

    fig.add_shape(type="line",
                  x0=0, y0=0, x1=0, y1=skid_height,
                  line=dict(color='gray', width=1, dash='dot'))

    for i, x in enumerate(skid_positions):
        fig.add_shape(type="rect",
                      x0=x - skid_width/2, y0=0,
                      x1=x + skid_width/2, y1=skid_height,
                      fillcolor="#8B4513", opacity=1.0, line=dict(color="black"))

        fig.add_annotation(x=x, y=-0.3, text=f"X{i}: {round(x, 2)}\"",
                           showarrow=False, font=dict(size=10, color="black"), yanchor="top", bgcolor="white")
        fig.add_annotation(x=x, y=skid_height + 0.2, text=f"{skid_width}\"",
                           showarrow=False, font=dict(size=10, color="black"), yanchor="bottom", bgcolor="white")

    if skid_positions:
        left_edge = skid_positions[0] - skid_width / 2
        right_edge = skid_positions[-1] + skid_width / 2
        total_span = round(right_edge - left_edge, 2)
        fig.add_shape(type="line", x0=left_edge, y0=skid_height + 0.8, x1=right_edge, y1=skid_height + 0.8,
                      line=dict(color="black", width=1, dash="dot"))
        fig.add_annotation(x=(left_edge + right_edge) / 2, y=skid_height + 1.0,
                           text=f"Total Skid Span: {total_span}\"",
                           showarrow=False, font=dict(size=11, color="black"), yanchor="bottom", bgcolor="white")

    fig.update_layout(
        title="Skid Layout – Front Profile (Scaled)",
        xaxis_title="Crate Width (inches)",
        yaxis_title="Skid Height (inches)",
        xaxis=dict(range=[-canvas_width/2, canvas_width/2], zeroline=False),
        yaxis=dict(range=[-1, skid_height + 2], zeroline=False),
        height=420,
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(l=20, r=20, t=40, b=40)
    )

    return fig

# --- Streamlit App ---
st.set_page_config(layout="wide")
st.title("🚧 AutoCrate Wizard")

st.sidebar.header("Product Dimensions")
weight = st.sidebar.slider("Weight (lb)", 5, 20000, 2000, step=5)
width = st.sidebar.slider("Width (in)", 20.0, 125.2, 85.0, step=0.5)
length = st.sidebar.slider("Length (in)", 20.0, 96.0, 70.0, step=0.5)
height = st.sidebar.slider("Height (in)", 20.0, 116.0, 99.0, step=0.5)

st.sidebar.header("Constants")
clearance_side = st.sidebar.number_input("Clearance Side (in)", value=2.0, step=0.5)
clearance_top = st.sidebar.number_input("Clearance Top (in)", value=1.5, step=0.5)
panel_thickness = st.sidebar.number_input("Panel Thickness (in)", value=0.25, step=0.25)
cleat_thickness = st.sidebar.number_input("Cleat Thickness (in)", value=0.75, step=0.25)

layout = calculate_skid_layout(
    prod_width_in=width,
    prod_weight_lbm=weight,
    clearance_side=clearance_side,
    panel_thickness=panel_thickness,
    cleat_thickness=cleat_thickness
)

st.markdown(f"**Recommended Skids:** {layout['skid_count']}")
st.markdown(f"**Skid Width:** {layout['skid_width']}\"")
st.markdown(f"**Spacing (actual):** {round(layout['spacing_actual'], 2)}\"")
st.markdown(f"**Crate Width:** {round(layout['crate_width'], 2)}\"")

fig = create_crate_figures(
    layout["crate_width"],
    layout["skid_positions"],
    layout["skid_width"]
)

st.subheader("📐 Skid Layout View")
st.plotly_chart(fig, use_container_width=True)
