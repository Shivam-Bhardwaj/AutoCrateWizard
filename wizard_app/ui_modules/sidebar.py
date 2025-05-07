# wizard_app/ui_modules/sidebar.py
"""
Handles the Streamlit sidebar inputs for the AutoCrate Wizard.
"""
import streamlit as st
# Use absolute import for config within the package
from wizard_app import config

# --- Helper Function for Combined Slider/Number Input ---
# (Copied from previous app.py version)
def input_slider_combo(label, min_val, max_val, default_val, step, format_str="%.1f", help_text=""):
    """Creates a slider with a number input box for precise entry."""
    state_key_slider = f"{label}_slider"
    state_key_num = f"{label}_num"
    safe_default = max(min_val, min(max_val, default_val))
    if state_key_slider not in st.session_state: st.session_state[state_key_slider] = safe_default
    if state_key_num not in st.session_state: st.session_state[state_key_num] = safe_default
    if not (min_val <= st.session_state[state_key_slider] <= max_val): st.session_state[state_key_slider] = safe_default
    if not (min_val <= st.session_state[state_key_num] <= max_val): st.session_state[state_key_num] = safe_default
    col1, col2 = st.columns([3, 1])
    with col1:
        new_slider_val = st.slider(label, min_val, max_val, st.session_state[state_key_slider], step, format=format_str, help=help_text, key=f"sl_{label}")
        if new_slider_val != st.session_state[state_key_slider]: st.session_state[state_key_slider] = new_slider_val; st.session_state[state_key_num] = new_slider_val; st.rerun()
    with col2:
        new_num_val = st.number_input("Value", min_value=min_val, max_value=max_val, value=st.session_state[state_key_num], step=step, format=format_str, label_visibility="collapsed", key=f"ni_{label}")
        if new_num_val != st.session_state[state_key_num]: st.session_state[state_key_num] = new_num_val; st.session_state[state_key_slider] = new_num_val; st.rerun()
    return st.session_state[state_key_slider]

def display_sidebar():
    """Displays sidebar inputs and returns a dictionary of values."""
    inputs = {}
    with st.sidebar:
        st.header("Product & Crate Parameters")
        inputs['product_weight'] = st.number_input("Product Weight (lbs)", min_value=1.0, max_value=20000.0, value=1500.0, step=10.0, format="%.1f", help="Enter exact product weight.")
        st.caption("Skid type/spacing rules apply based on weight.")
        inputs['product_width'] = input_slider_combo("Product Width (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ACROSS skids.")
        inputs['product_length'] = input_slider_combo("Product Length (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ALONG skids.")
        inputs['product_height'] = input_slider_combo("Product Actual Height (in)", 1.0, 120.0, 48.0, 0.5, "%.1f", "Actual height of the product itself.")

        st.subheader("Crate Construction Constants")
        inputs['clearance_side'] = st.number_input("Clearance Side (Product W/L) (in)", 0.0, value=2.0, step=0.1, format="%.2f")
        inputs['clearance_above'] = st.number_input("Clearance Above Product (to Top Panel) (in)", 0.0, value=config.DEFAULT_CLEARANCE_ABOVE_PRODUCT, step=0.1, format="%.2f")
        inputs['panel_thickness'] = st.number_input("Panel Thickness (Wall/Floor/Top) (in)", 0.01, value=config.DEFAULT_PANEL_THICKNESS_UI, step=0.01, format="%.2f", help="Used for floor, top, and wall panels.")
        inputs['wall_cleat_thickness'] = st.number_input("Wall Cleat Actual Thickness (in)", 0.01, value=config.DEFAULT_CLEAT_NOMINAL_THICKNESS, step=0.01, format="%.2f", help="Thickness of side/end wall framing cleats.")
        inputs['wall_cleat_width'] = st.number_input("Wall Cleat Actual Width (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_WIDTH, step=0.1, format="%.1f", help="Width of side/end wall framing cleats.")

        st.subheader("Floorboard Options")
        selected_ui_options = st.multiselect("Available Floorboard Lumber", options=config.ALL_LUMBER_OPTIONS_UI, default=config.DEFAULT_UI_LUMBER_SELECTION_APP)
        inputs['selected_floor_nominals'] = tuple(sorted([opt for opt in selected_ui_options if opt != config.CUSTOM_NARROW_OPTION_TEXT_UI]))
        inputs['allow_custom_narrow'] = config.CUSTOM_NARROW_OPTION_TEXT_UI in selected_ui_options

        st.subheader("Top Panel Options")
        inputs['cap_cleat_thickness'] = st.number_input("Top Panel Cleat Actual Thickness (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_THICKNESS, step=0.01, format="%.2f", help="Actual thickness of the top panel cleat lumber (defaults to wall cleat thickness).")
        inputs['cap_cleat_width'] = st.number_input("Top Panel Cleat Actual Width (in)", 0.1, value=config.DEFAULT_CLEAT_NOMINAL_WIDTH, step=0.1, format="%.1f", help="Actual width of the top panel cleat lumber (defaults to wall cleat width).")
        inputs['max_top_cleat_spacing'] = st.number_input("Max Top Panel Cleat Spacing (C-C, in)", 1.0, value=24.0, step=1.0, format="%.1f")

        st.divider()
        st.info(f"AutoCrate Wizard v{config.VERSION}\nFor inquiries, contact Shivam Bhardwaj.")

    return inputs

