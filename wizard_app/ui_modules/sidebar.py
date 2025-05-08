# wizard_app/ui_modules/sidebar.py
"""
Handles the Streamlit sidebar inputs for the AutoCrate Wizard.
Sidebar layout optimized with expanders.
Regenerate button moved to sidebar.
Ensures robust session state handling for inputs.
"""
import streamlit as st
# Use absolute import for config within the package
from wizard_app import config

# Helper to manage session state for simple input widgets
def manage_input_state(widget_key, session_value_key, default_value):
    """
    Ensures session state for a widget's value is initialized and updated.
    Returns the current value from session state.
    """
    if session_value_key not in st.session_state:
        st.session_state[session_value_key] = default_value
    
    # If widget has a value (meaning it was rendered and possibly changed by user)
    if widget_key in st.session_state:
        # If widget value differs from our stored session value, update stored session value
        if st.session_state[widget_key] != st.session_state[session_value_key]:
            st.session_state[session_value_key] = st.session_state[widget_key]
            # No st.rerun() here, app.py's main loop handles reruns triggered by widget changes.
            # The purpose here is just to keep our session_value_key in sync.
            
    return st.session_state[session_value_key]

def input_slider_combo(label, min_val, max_val, default_val, step, format_str="%.1f", help_text="", key_prefix=""):
    """
    Creates a slider with a number input box for precise entry.
    Uses session state robustly with unique keys.
    """
    # Sanitize label to create part of the key
    sanitized_label = label.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('.', '').lower()
    
    # Session state keys for the actual values
    session_key_slider_val = f"{key_prefix}_slider_val_{sanitized_label}"
    session_key_num_val = f"{key_prefix}_num_val_{sanitized_label}" # Though they should be the same

    # Widget keys for the st.slider and st.number_input widgets themselves
    widget_slider_key = f"{key_prefix}_widget_slider_{sanitized_label}"
    widget_num_key = f"{key_prefix}_widget_num_{sanitized_label}"

    safe_default = max(min_val, min(max_val, default_val))

    # Initialize session state for the values if they don't exist
    if session_key_slider_val not in st.session_state:
        st.session_state[session_key_slider_val] = safe_default
    # num_val should ideally mirror slider_val, so only one primary state needed.
    # Let's use session_key_slider_val as the primary store.

    # Ensure current session state value is within bounds
    if not (min_val <= st.session_state[session_key_slider_val] <= max_val):
        st.session_state[session_key_slider_val] = safe_default
    
    current_val_from_state = st.session_state[session_key_slider_val]

    col1, col2 = st.columns([3, 1])
    with col1:
        new_slider_widget_val = st.slider(
            label, min_val, max_val, value=current_val_from_state, step=step,
            format=format_str, help=help_text, key=widget_slider_key
        )
        # If slider widget's value changed from our stored state
        if new_slider_widget_val != st.session_state[session_key_slider_val]:
            st.session_state[session_key_slider_val] = new_slider_widget_val
            st.rerun() # Rerun to update the number input and propagate change

    with col2:
        # Number input should also reflect the primary stored value
        new_num_widget_val = st.number_input(
            "Value", min_value=min_val, max_value=max_val, value=st.session_state[session_key_slider_val],
            step=step, format=format_str, label_visibility="collapsed", key=widget_num_key
        )
        if new_num_widget_val != st.session_state[session_key_slider_val]:
            st.session_state[session_key_slider_val] = new_num_widget_val
            st.rerun() # Rerun to update the slider and propagate change
            
    return st.session_state[session_key_slider_val]


def display_sidebar():
    """Displays sidebar inputs and returns a dictionary of values. Manages 'regenerate_clicked' state."""
    
    # Ensure 'regenerate_clicked' is initialized in session_state.
    # app.py also does this, but defense in depth.
    if 'regenerate_clicked' not in st.session_state:
        st.session_state.regenerate_clicked = False

    with st.sidebar:
        st.header(f"AutoCrate Wizard v{config.VERSION}")
        st.caption("Adjust parameters below and regenerate.")
        
        if st.button("🔄 Regenerate Crate", type="primary", use_container_width=True, key="sidebar_regenerate_button"):
            st.session_state.regenerate_clicked = True
            # A rerun is implicitly triggered by Streamlit when a button is clicked.
            # app.py will detect st.session_state.regenerate_clicked as True on the next run.
        
        st.divider()

        # --- Product & Crate Parameters (Always Visible) ---
        st.subheader("📦 Product & Crate")
        
        # Product Weight
        prod_weight_val = manage_input_state('prod_weight_widget', 'prod_weight_ss', 1500.0)
        st.number_input("Product Weight (lbs)", min_value=1.0, max_value=20000.0, value=prod_weight_val, step=10.0, format="%.1f", help="Enter exact product weight.", key='prod_weight_widget')

        # Product Width, Length, Height using input_slider_combo
        # Default values for sliders are handled internally by input_slider_combo's session state logic
        prod_width_val = input_slider_combo("Product Width (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ACROSS skids.", key_prefix='prod_w')
        prod_length_val = input_slider_combo("Product Length (in)", 1.0, 125.0, 90.0, 0.5, "%.1f", "Product dimension ALONG skids.", key_prefix='prod_l')
        prod_height_val = input_slider_combo("Product Actual Height (in)", 1.0, 120.0, 48.0, 0.5, "%.1f", "Actual height of the product itself.", key_prefix='prod_h')

        # --- Construction Constants (Expander) ---
        with st.expander("🛠️ Construction Details", expanded=False):
            clearance_side_val = manage_input_state('clearance_side_widget', 'clearance_side_ss', 2.0)
            st.number_input("Clearance Side (Product W/L) (in)", 0.0, value=clearance_side_val, step=0.1, format="%.2f", key='clearance_side_widget')

            clearance_above_val = manage_input_state('clearance_above_widget', 'clearance_above_ss', config.DEFAULT_CLEARANCE_ABOVE_PRODUCT)
            st.number_input("Clearance Above Product (in)", 0.0, value=clearance_above_val, step=0.1, format="%.2f", key='clearance_above_widget')

            panel_thick_val = manage_input_state('panel_thick_widget', 'panel_thick_ss', config.DEFAULT_PANEL_THICKNESS_UI)
            st.number_input("Panel Thickness (Wall/Floor/Top) (in)", 0.01, value=panel_thick_val, step=0.01, format="%.2f", help="Used for floor, top, and wall panels.", key='panel_thick_widget')
            
            wall_cleat_thick_val = manage_input_state('wall_cleat_thick_widget', 'wall_cleat_thick_ss', config.DEFAULT_CLEAT_NOMINAL_THICKNESS)
            st.number_input("Wall Cleat Actual Thickness (in)", 0.01, value=wall_cleat_thick_val, step=0.01, format="%.2f", help="Thickness of wall framing cleats.", key='wall_cleat_thick_widget')

            wall_cleat_width_val = manage_input_state('wall_cleat_width_widget', 'wall_cleat_width_ss', config.DEFAULT_CLEAT_NOMINAL_WIDTH)
            st.number_input("Wall Cleat Actual Width (in)", 0.1, value=wall_cleat_width_val, step=0.1, format="%.1f", help="Width of wall framing cleats.", key='wall_cleat_width_widget')

        # --- Floorboard Options (Expander) ---
        with st.expander("🔩 Floorboard Options", expanded=False):
            current_multiselect_val = manage_input_state('floor_lumber_widget', 'floor_lumber_ss', config.DEFAULT_UI_LUMBER_SELECTION_APP)
            st.multiselect("Available Floorboard Lumber", options=config.ALL_LUMBER_OPTIONS_UI, default=current_multiselect_val, key='floor_lumber_widget')
            
            # Values used by app.py will be derived from session state after manage_input_state updates it
            selected_floor_nominals_from_ss = st.session_state.get('floor_lumber_ss', config.DEFAULT_UI_LUMBER_SELECTION_APP)


        # --- Top Panel Options (Expander) ---
        with st.expander("🧢 Top Panel Options", expanded=False):
            cap_cleat_thick_val = manage_input_state('cap_cleat_thick_widget', 'cap_cleat_thick_ss', config.DEFAULT_CLEAT_NOMINAL_THICKNESS)
            st.number_input("Top Panel Cleat Actual Thickness (in)", 0.1, value=cap_cleat_thick_val, step=0.01, format="%.2f", help="Actual thickness of top panel cleat.", key='cap_cleat_thick_widget')

            cap_cleat_width_val = manage_input_state('cap_cleat_width_widget', 'cap_cleat_width_ss', config.DEFAULT_CLEAT_NOMINAL_WIDTH)
            st.number_input("Top Panel Cleat Actual Width (in)", 0.1, value=cap_cleat_width_val, step=0.1, format="%.1f", help="Actual width of top panel cleat.", key='cap_cleat_width_widget')

            max_top_cleat_spacing_val = manage_input_state('max_top_cleat_space_widget', 'max_top_cleat_space_ss', 24.0)
            st.number_input("Max Top Panel Cleat Spacing (C-C, in)", 1.0, value=max_top_cleat_spacing_val, step=1.0, format="%.1f", key='max_top_cleat_space_widget')
        
        st.divider()
        st.caption("AutoCrate Wizard")

    # Construct the 'inputs' dictionary from the authoritative session state values
    inputs_to_return = {
        'product_weight': st.session_state.get('prod_weight_ss', 1500.0),
        'product_width': prod_width_val, # From input_slider_combo return
        'product_length': prod_length_val, # From input_slider_combo return
        'product_height': prod_height_val, # From input_slider_combo return
        'clearance_side': st.session_state.get('clearance_side_ss', 2.0),
        'clearance_above': st.session_state.get('clearance_above_ss', config.DEFAULT_CLEARANCE_ABOVE_PRODUCT),
        'panel_thickness': st.session_state.get('panel_thick_ss', config.DEFAULT_PANEL_THICKNESS_UI),
        'wall_cleat_thickness': st.session_state.get('wall_cleat_thick_ss', config.DEFAULT_CLEAT_NOMINAL_THICKNESS),
        'wall_cleat_width': st.session_state.get('wall_cleat_width_ss', config.DEFAULT_CLEAT_NOMINAL_WIDTH),
        
        'selected_floor_nominals': tuple(sorted([opt for opt in st.session_state.get('floor_lumber_ss', config.DEFAULT_UI_LUMBER_SELECTION_APP) if opt != config.CUSTOM_NARROW_OPTION_TEXT_UI])),
        'allow_custom_narrow': config.CUSTOM_NARROW_OPTION_TEXT_UI in st.session_state.get('floor_lumber_ss', config.DEFAULT_UI_LUMBER_SELECTION_APP),
        
        'cap_cleat_thickness': st.session_state.get('cap_cleat_thick_ss', config.DEFAULT_CLEAT_NOMINAL_THICKNESS),
        'cap_cleat_width': st.session_state.get('cap_cleat_width_ss', config.DEFAULT_CLEAT_NOMINAL_WIDTH),
        'max_top_cleat_spacing': st.session_state.get('max_top_cleat_space_ss', 24.0),
    }
    return inputs_to_return