# wizard_app/ui_modules/sidebar.py
"""
Handles the Streamlit sidebar inputs for the AutoCrate Wizard.
Sidebar layout optimized with expanders.
Regenerate button moved to sidebar.
Ensures robust session state handling for inputs.
CORRECTED: Uses 'regenerate_data_clicked' session state key to match app.py
"""
import streamlit as st
# Use absolute import for config within the package
from wizard_app import config # Assuming wizard_app is in the Python path or structure allows this

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
    # This will be the primary key to store the component's value in session_state
    session_key_value = f"{key_prefix}_value_ss_{sanitized_label}"

    # Widget keys for the st.slider and st.number_input widgets themselves
    widget_slider_key = f"{key_prefix}_widget_slider_{sanitized_label}"
    widget_num_key = f"{key_prefix}_widget_num_{sanitized_label}"

    safe_default = max(min_val, min(max_val, default_val))

    # Initialize session state for the value if it doesn't exist
    if session_key_value not in st.session_state:
        st.session_state[session_key_value] = safe_default
    
    # Ensure current session state value is within bounds, reset to default if not (e.g., if bounds change)
    current_val_from_state = st.session_state[session_key_value]
    if not (min_val <= current_val_from_state <= max_val):
        st.session_state[session_key_value] = safe_default
        current_val_from_state = safe_default # Update local copy

    col1, col2 = st.columns([3, 1])
    with col1:
        new_slider_widget_val = st.slider(
            label, min_val, max_val, value=current_val_from_state, step=step,
            format=format_str, help=help_text, key=widget_slider_key
        )
        # If slider widget's value changed from our stored state
        if new_slider_widget_val != st.session_state[session_key_value]:
            st.session_state[session_key_value] = new_slider_widget_val
            st.rerun() # Rerun to update the number input and propagate change

    with col2:
        # Number input should also reflect the primary stored value
        new_num_widget_val = st.number_input(
            "Value", min_value=min_val, max_value=max_val, value=st.session_state[session_key_value],
            step=step, format=format_str, label_visibility="collapsed", key=widget_num_key
        )
        if new_num_widget_val != st.session_state[session_key_value]:
            st.session_state[session_key_value] = new_num_widget_val
            st.rerun() # Rerun to update the slider and propagate change
            
    return st.session_state[session_key_value]


def display_sidebar():
    """Displays sidebar inputs and returns a dictionary of values. Manages 'regenerate_data_clicked' state."""
    
    # Ensure 'regenerate_data_clicked' is initialized in session_state.
    # app.py also does this, but defense in depth.
    if 'regenerate_data_clicked' not in st.session_state:
        st.session_state.regenerate_data_clicked = False

    with st.sidebar:
        st.header(f"AutoCrate Wizard v{config.VERSION if config else 'N/A'}") # Handle if config is None
        st.caption("Adjust parameters below and regenerate.")
        
        # CORRECTED: Use 'regenerate_data_clicked' to match app.py
        if st.button("🔄 Regenerate Crate", type="primary", use_container_width=True, key="sidebar_regenerate_button"):
            st.session_state.regenerate_data_clicked = True 
            # A rerun is implicitly triggered by Streamlit when a button is clicked.
            # app.py will detect st.session_state.regenerate_data_clicked as True on the next run.
        
        st.divider()

        # --- Product & Crate Parameters (Always Visible) ---
        st.subheader("📦 Product & Crate")
        
        # Product Weight
        # For manage_input_state, the widget_key is the key given to the st widget,
        # and session_value_key is the key where we want to store its processed value.
        prod_weight_val = manage_input_state('prod_weight_widget', 'prod_weight_ss', 1500.0)
        st.number_input("Product Weight (lbs)", min_value=1.0, max_value=20000.0, 
                        value=prod_weight_val, # This should be the value from our session state store
                        step=10.0, format="%.1f", 
                        help="Enter exact product weight.", key='prod_weight_widget')

        # Product Width, Length, Height using input_slider_combo
        prod_width_val = input_slider_combo("Product Width (in)", 1.0, 125.0, 
                                            st.session_state.get('prod_w_value_ss_product_width_in', 90.0), # Use specific session key
                                            0.5, "%.1f", "Product dimension ACROSS skids.", key_prefix='prod_w')
        prod_length_val = input_slider_combo("Product Length (in)", 1.0, 125.0, 
                                             st.session_state.get('prod_l_value_ss_product_length_in', 90.0), 
                                             0.5, "%.1f", "Product dimension ALONG skids.", key_prefix='prod_l')
        prod_height_val = input_slider_combo("Product Actual Height (in)", 1.0, 120.0, 
                                             st.session_state.get('prod_h_value_ss_product_actual_height_in', 48.0), 
                                             0.5, "%.1f", "Actual height of the product itself.", key_prefix='prod_h')

        # --- Construction Constants (Expander) ---
        with st.expander("🛠️ Construction Details", expanded=False):
            clearance_side_val = manage_input_state('clearance_side_widget', 'clearance_side_ss', 2.0)
            st.number_input("Clearance Side (Product W/L) (in)", 0.0, 
                            value=clearance_side_val, step=0.1, format="%.2f", key='clearance_side_widget')

            default_clearance_above = config.DEFAULT_CLEARANCE_ABOVE_PRODUCT if config else 1.5
            clearance_above_val = manage_input_state('clearance_above_widget', 'clearance_above_ss', default_clearance_above)
            st.number_input("Clearance Above Product (in)", 0.0, 
                            value=clearance_above_val, step=0.1, format="%.2f", key='clearance_above_widget')

            default_panel_thick = config.DEFAULT_PANEL_THICKNESS_UI if config else 0.25
            panel_thick_val = manage_input_state('panel_thick_widget', 'panel_thick_ss', default_panel_thick)
            st.number_input("Panel Thickness (Wall/Floor/Top) (in)", 0.01, 
                            value=panel_thick_val, step=0.01, format="%.2f", 
                            help="Used for floor, top, and wall panels.", key='panel_thick_widget')
            
            default_cleat_thick = config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75
            wall_cleat_thick_val = manage_input_state('wall_cleat_thick_widget', 'wall_cleat_thick_ss', default_cleat_thick)
            st.number_input("Wall Cleat Actual Thickness (in)", 0.01, 
                            value=wall_cleat_thick_val, step=0.01, format="%.2f", 
                            help="Thickness of wall framing cleats.", key='wall_cleat_thick_widget')

            default_cleat_width = config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5
            wall_cleat_width_val = manage_input_state('wall_cleat_width_widget', 'wall_cleat_width_ss', default_cleat_width)
            st.number_input("Wall Cleat Actual Width (in)", 0.1, 
                            value=wall_cleat_width_val, step=0.1, format="%.1f", 
                            help="Width of wall framing cleats.", key='wall_cleat_width_widget')

        # --- Floorboard Options (Expander) ---
        with st.expander("🔩 Floorboard Options", expanded=False):
            all_lumber_opts = config.ALL_LUMBER_OPTIONS_UI if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"]
            default_lumber_sel = config.DEFAULT_UI_LUMBER_SELECTION_APP if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"]
            
            current_multiselect_val = manage_input_state('floor_lumber_widget', 'floor_lumber_ss', default_lumber_sel)
            st.multiselect("Available Floorboard Lumber", 
                           options=all_lumber_opts, 
                           default=current_multiselect_val, # Use value from session state store
                           key='floor_lumber_widget')
            
        # --- Top Panel Options (Expander) ---
        with st.expander("🧢 Top Panel Options", expanded=False):
            default_cap_cleat_thick = config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75
            cap_cleat_thick_val = manage_input_state('cap_cleat_thick_widget', 'cap_cleat_thick_ss', default_cap_cleat_thick)
            st.number_input("Top Panel Cleat Actual Thickness (in)", 0.1, 
                            value=cap_cleat_thick_val, step=0.01, format="%.2f", 
                            help="Actual thickness of top panel cleat.", key='cap_cleat_thick_widget')

            default_cap_cleat_width = config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5
            cap_cleat_width_val = manage_input_state('cap_cleat_width_widget', 'cap_cleat_width_ss', default_cap_cleat_width)
            st.number_input("Top Panel Cleat Actual Width (in)", 0.1, 
                            value=cap_cleat_width_val, step=0.1, format="%.1f", 
                            help="Actual width of top panel cleat.", key='cap_cleat_width_widget')

            max_top_cleat_spacing_val = manage_input_state('max_top_cleat_space_widget', 'max_top_cleat_space_ss', 24.0)
            st.number_input("Max Top Panel Cleat Spacing (C-C, in)", 1.0, 
                            value=max_top_cleat_spacing_val, step=1.0, format="%.1f", 
                            key='max_top_cleat_space_widget')
        
        st.divider()
        st.caption("AutoCrate Wizard")

    # Construct the 'inputs' dictionary from the authoritative session state values
    # Default values here should match those used in manage_input_state or input_slider_combo
    # and config module where appropriate.
    
    # For input_slider_combo, the returned value is already from session state.
    # For manage_input_state, we fetch from the session_value_key.
    
    default_clearance_above_final = config.DEFAULT_CLEARANCE_ABOVE_PRODUCT if config else 1.5
    default_panel_thick_final = config.DEFAULT_PANEL_THICKNESS_UI if config else 0.25
    default_wall_cleat_thick_final = config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75
    default_wall_cleat_width_final = config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5
    default_lumber_sel_final = config.DEFAULT_UI_LUMBER_SELECTION_APP if config else ["2x6", "2x8", "2x10", "2x12", "Use Custom Narrow Board (Fill < 5.5\")"]
    custom_narrow_text_final = config.CUSTOM_NARROW_OPTION_TEXT_UI if config else "Use Custom Narrow Board (Fill < 5.5\")"
    default_cap_cleat_thick_final = config.DEFAULT_CLEAT_NOMINAL_THICKNESS if config else 0.75
    default_cap_cleat_width_final = config.DEFAULT_CLEAT_NOMINAL_WIDTH if config else 3.5

    inputs_to_return = {
        'product_weight': st.session_state.get('prod_weight_ss', 1500.0),
        'product_width': prod_width_val, 
        'product_length': prod_length_val,
        'product_height': prod_height_val, 
        'clearance_side': st.session_state.get('clearance_side_ss', 2.0),
        'clearance_above': st.session_state.get('clearance_above_ss', default_clearance_above_final),
        'panel_thickness': st.session_state.get('panel_thick_ss', default_panel_thick_final),
        'wall_cleat_thickness': st.session_state.get('wall_cleat_thick_ss', default_wall_cleat_thick_final),
        'wall_cleat_width': st.session_state.get('wall_cleat_width_ss', default_wall_cleat_width_final),
        
        'selected_floor_nominals': tuple(sorted([opt for opt in st.session_state.get('floor_lumber_ss', default_lumber_sel_final) if opt != custom_narrow_text_final])),
        'allow_custom_narrow': custom_narrow_text_final in st.session_state.get('floor_lumber_ss', default_lumber_sel_final),
        
        'cap_cleat_thickness': st.session_state.get('cap_cleat_thick_ss', default_cap_cleat_thick_final),
        'cap_cleat_width': st.session_state.get('cap_cleat_width_ss', default_cap_cleat_width_final),
        'max_top_cleat_spacing': st.session_state.get('max_top_cleat_space_ss', 24.0),
    }
    return inputs_to_return
