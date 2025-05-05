# app.py
"""
Streamlit application for the AutoCrate Wizard - Parametric Skid Layout System.

Provides a user interface for inputting product details, displays calculated
skid layout metrics, and visualizes the layout using Plotly.
"""

import streamlit as st
import plotly.graph_objects as go
# import pandas as pd # Not currently used, but listed as dependency
# import numpy as np # Not currently used, but listed as dependency
import logging
import math

# --- Setup Logging ---
# Configure logging basic settings
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Get a logger for this module
log = logging.getLogger(__name__)

# --- Import Core Logic ---
# Ensure skid_logic.py is in the same directory or Python path
try:
    from skid_logic import calculate_skid_layout
    log.info("Successfully imported calculate_skid_layout from skid_logic.")
except ImportError:
    log.error("Failed to import calculate_skid_layout from skid_logic.py.")
    st.error("Fatal Error: Could not import `skid_logic.py`. Make sure it's in the same directory as `app.py`.")
    st.stop() # Stop execution if core logic is missing

# --- Import Optional Logic (Placeholder) ---
try:
    from floorboard_logic import calculate_floorboard_layout
    log.info("Successfully imported calculate_floorboard_layout from floorboard_logic.")
except ImportError:
    log.warning("Optional `floorboard_logic.py` not found. Floorboard calculation will be disabled.")
    # Define a placeholder function if the import fails, so the app doesn't crash
    def calculate_floorboard_layout(*args, **kwargs):
        """Placeholder function when floorboard_logic.py is missing."""
        log.warning("Called placeholder calculate_floorboard_layout.")
        return {"status": "NOT FOUND", "message": "floorboard_logic.py not found or import failed."}
    # Set a flag or use the function object itself to check later
    floorboard_logic_available = False
else:
    floorboard_logic_available = True


# --- Streamlit Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="AutoCrate Wizard",
    page_icon="⚙️", # You can use emojis as icons
    menu_items={
        'Get Help': 'https://github.com/your_repo/autocrate_wizard', # Replace with your repo if you have one
        'Report a bug': "https://github.com/your_repo/autocrate_wizard/issues",
        'About': "# AutoCrate Wizard \n Calculates and visualizes shipping crate skid layouts."
    }
)

# --- Page Title and Description ---
st.title("⚙️ AutoCrate Wizard - Skid Layout System")
st.caption("Calculates skid layout based on shipping standards (up to 20,000 lbs)")
st.divider() # Adds a horizontal line

# --- Sidebar Inputs ---
st.sidebar.header("Product & Crate Parameters")

# Input: Product Weight
product_weight = st.sidebar.slider(
    "Product Weight (lbs)",
    min_value=0.0, # Allow 0 weight as per logic handling
    max_value=20000.0,
    value=4500.0, # Default value as specified
    step=10.0,
    help="Total weight of the product being shipped (0 to 20,000 lbs). Determines skid type and spacing requirements."
)

# Input: Product Width
product_width = st.sidebar.slider(
    "Product Width (inches)",
    min_value=10.0,
    max_value=125.0,
    value=90.0, # Default value as specified
    step=0.5,
    format="%.1f", # Display one decimal place
    help="Width of the product at its widest point (10.0\" to 125.0\"). Influences overall crate width and skid placement."
)

# Subheader for constants
st.sidebar.subheader("Crate Construction Constants")

# Input: Clearance per Side
clearance_side = st.sidebar.number_input(
    "Clearance per Side (inches)",
    min_value=0.0,
    value=2.0, # Default value as specified
    step=0.1,
    format="%.2f", # Display two decimal places
    help="Minimum space between product and inner crate wall/cleat on each side."
)

# Input: Panel Thickness
panel_thickness = st.sidebar.number_input(
    "Panel Thickness (inches)",
    min_value=0.0,
    value=0.25, # Default value as specified
    step=0.01,
    format="%.2f",
    help="Thickness of the side panels (e.g., plywood)."
)

# Input: Cleat Thickness
cleat_thickness = st.sidebar.number_input(
    "Cleat Thickness (inches)",
    min_value=0.0,
    value=0.75, # Default value as specified
    step=0.01,
    format="%.2f",
    help="Thickness of the structural cleats inside the panels."
)

# --- Core Logic Execution ---
log.info(f"Inputs received: Weight={product_weight}, Width={product_width}, Clearance={clearance_side}, Panel={panel_thickness}, Cleat={cleat_thickness}")
try:
    layout_results = calculate_skid_layout(
        product_weight, product_width, clearance_side, panel_thickness, cleat_thickness
    )
    log.info(f"Calculation complete. Status: {layout_results.get('status')}")
except Exception as e:
    log.error(f"An unexpected error occurred during skid calculation: {e}", exc_info=True)
    st.error(f"An unexpected error occurred during calculation: {e}")
    # Create a dummy result dictionary to prevent downstream errors
    layout_results = {
        "status": "CRITICAL ERROR",
        "message": f"Calculation failed: {e}",
        "skid_type": "N/A", "skid_width": 0, "skid_height": 0,
        "skid_count": 0, "spacing_actual": 0, "max_spacing": 0,
        "crate_width": 0, "usable_width": 0, "skid_positions": [],
    }


# --- Main Area Display ---
st.header("Skid Layout Results")

# Display Status prominently
status = layout_results.get("status", "UNKNOWN")
message = layout_results.get("message", "No message provided.")

if status == "OK":
    st.success(f"**Status:** ✅ OK - {message}")
elif status in ["ERROR", "OVER", "CRITICAL ERROR"]:
    st.error(f"**Status:** ❌ {status} - {message}")
    # Do not stop, allow showing partial results or N/A
elif status == "INIT":
     st.info(f"**Status:** ⏳ INIT - {message}")
     # Calculation didn't proceed, likely due to early exit or issue
else: # Handle any other unforeseen status (e.g., "TOO WIDE" if it were still used)
    st.warning(f"**Status:** ⚠️ {status} - {message}")

# --- Display Key Metrics ---
# Display metrics even if there's an error, showing defaults or N/A
st.subheader("Key Design Metrics")
col1, col2, col3 = st.columns(3) # Create three columns for metrics

try:
    # Safely extract values using .get() with defaults for robustness
    skid_w_metric = layout_results.get('skid_width') # Let metric handle None
    skid_count_metric = layout_results.get('skid_count')
    positions_metric = layout_results.get('skid_positions', [])
    spacing_actual_metric = layout_results.get('spacing_actual')
    max_spacing_metric = layout_results.get('max_spacing')
    crate_width_metric = layout_results.get('crate_width')
    skid_type_metric = layout_results.get('skid_type', 'N/A')

    # Calculate Overall Skid Span (distance between outer edges of outermost skids)
    overall_skid_span_metric = None # Default to None
    span_error = False
    if skid_count_metric is not None and skid_w_metric is not None and positions_metric:
        if skid_count_metric == 1:
            overall_skid_span_metric = skid_w_metric
        elif skid_count_metric > 1:
            # Ensure positions list has the expected number of elements
            if len(positions_metric) == skid_count_metric:
                 first_skid_center = positions_metric[0]
                 last_skid_center = positions_metric[-1]
                 # Span = distance between centers + width of one skid
                 # OR: Span = abs(last_outer_edge - first_outer_edge)
                 first_skid_outer_edge = first_skid_center - skid_w_metric / 2.0
                 last_skid_outer_edge = last_skid_center + skid_w_metric / 2.0
                 overall_skid_span_metric = abs(last_skid_outer_edge - first_skid_outer_edge)
            else:
                 log.warning(f"Mismatch between skid_count ({skid_count_metric}) and length of skid_positions ({len(positions_metric)}). Cannot calculate span accurately.")
                 span_error = True # Indicate error in calculation

    # Helper function to format metrics, handling None values
    def format_metric(value, unit="\"", decimals=2, default="N/A"):
        if value is None:
            return default
        try:
            # Format numerical values
            return f"{value:.{decimals}f}{unit}"
        except (TypeError, ValueError):
             # Handle non-numerical values (like skid_type) or errors
            return str(value) if value is not None else default

    # Column 1 Metrics
    with col1:
        st.metric("Crate Width", format_metric(crate_width_metric))
        st.metric("Skid Type", skid_type_metric, help="Nominal size (e.g., 3x4, 4x4, 4x6)")

    # Column 2 Metrics
    with col2:
        span_display = format_metric(overall_skid_span_metric) if not span_error else "Error"
        st.metric("Overall Skid Span", span_display, help="Distance between outer edges of the outermost skids.")
        st.metric("Skid Width", format_metric(skid_w_metric), help="Actual width dimension of one skid member.")

    # Column 3 Metrics
    with col3:
        st.metric("Skid Count", str(skid_count_metric) if skid_count_metric is not None else "N/A")
        # Only show spacing if count > 1
        spacing_display = format_metric(spacing_actual_metric) if skid_count_metric is not None and skid_count_metric > 1 else "N/A"
        st.metric("Actual Spacing", spacing_display, help="Center-to-center distance between adjacent skids (if > 1 skid).")
        st.metric("Max Allowed Spacing", format_metric(max_spacing_metric))

except Exception as e:
    st.error(f"Error displaying metrics: {e}")
    log.error(f"Error during metric calculation/display: {e}", exc_info=True)
    # Prevent plot generation if metrics failed badly
    status = "METRIC ERROR"


# --- Visualization ---
st.divider() # Separator before the plot
st.subheader("Top-Down Skid Layout Visualization")

fig = go.Figure()
plot_generated = False
plot_error = None

# Only attempt plot if status is OK and we have necessary data
if status == "OK":
    try:
        # Extract data needed for plotting, ensuring they are not None
        skid_w_viz = layout_results.get('skid_width')
        skid_count_viz = layout_results.get('skid_count')
        positions_viz = layout_results.get('skid_positions')
        spacing_viz = layout_results.get('spacing_actual')
        max_spacing_viz = layout_results.get('max_spacing')
        # usable_width_viz = layout_results.get('usable_width') # Could be used for context lines

        # Check if essential plotting data is valid
        if skid_w_viz is not None and skid_w_viz > 0 and \
           skid_count_viz is not None and skid_count_viz > 0 and \
           positions_viz is not None and len(positions_viz) == skid_count_viz:

            # --- Plotting Constants ---
            SKID_COLOR = "#8B4513"  # Brown
            SKID_OUTLINE_COLOR = "#654321" # Darker Brown
            ANNOTATION_FONT_SIZE_SMALL = 10
            ANNOTATION_FONT_SIZE_MEDIUM = 11
            ANNOTATION_FONT_SIZE_LARGE = 13
            SPACING_ANNOTATION_COLOR = "purple" # As requested

            # Determine a reasonable visual height/scale for the plot elements
            # Make visual height proportional to width, but not excessively tall
            viz_skid_height_on_plot = max(skid_w_viz * 0.5, 5.0) # Ensure a minimum visual height
            y_center = 0
            y_skid_bottom = y_center - viz_skid_height_on_plot / 2
            y_skid_top = y_center + viz_skid_height_on_plot / 2
            # Increase vertical padding based on font sizes to avoid overlap
            y_padding_base = viz_skid_height_on_plot # Base padding related to skid visual height
            y_padding_factor = 1.2 # Increase if annotations overlap
            y_padding = y_padding_base * y_padding_factor

            # --- Plot Skids ---
            for i, pos in enumerate(positions_viz):
                x0 = pos - skid_w_viz / 2
                x1 = pos + skid_w_viz / 2

                fig.add_shape(
                    type="rect",
                    x0=x0, y0=y_skid_bottom, x1=x1, y1=y_skid_top,
                    fillcolor=SKID_COLOR,
                    line=dict(color=SKID_OUTLINE_COLOR, width=1.5),
                    name=f"Skid {i+1}" # Use 1-based index for display
                )

                # Add Skid Label Annotation (Above) - Shifted higher
                fig.add_annotation(
                    x=pos, y=y_skid_top, # Anchor near top
                    text=f"<b>Skid {i+1}</b>", # 1-based index
                    showarrow=False,
                    font=dict(color="black", size=ANNOTATION_FONT_SIZE_MEDIUM),
                    yshift=20 # Increase shift upwards
                )

                # Add Skid Position Annotation (Below) - Shifted lower
                fig.add_annotation(
                    x=pos, y=y_skid_bottom, # Anchor near bottom
                    text=f'{pos:.2f}"', # Display position with 2 decimals
                    showarrow=False,
                    font=dict(color="black", size=ANNOTATION_FONT_SIZE_SMALL),
                    yshift=-20 # Increase shift downwards
                )

            # Add single dummy trace for Skid legend entry
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode='markers',
                marker=dict(color=SKID_COLOR, size=10, symbol='square',
                            line=dict(color=SKID_OUTLINE_COLOR, width=1)),
                name='Skids' # Legend entry text
            ))

            # --- Plot Spacing Annotations (Between Skids) ---
            if skid_count_viz > 1 and spacing_viz is not None and max_spacing_viz is not None:
                # Position spacing annotation further down
                y_spacing_annotation = y_skid_bottom - y_padding * 0.6 # Relative to bottom + padding
                for i in range(skid_count_viz - 1):
                    pos1 = positions_viz[i]
                    pos2 = positions_viz[i+1]
                    mid_x = (pos1 + pos2) / 2
                    fig.add_annotation(
                        x=mid_x, y=y_spacing_annotation, # Use calculated y
                        text=f'↔ {spacing_viz:.2f}"<br>(Max: {max_spacing_viz:.2f}")', # Multi-line text
                        showarrow=False,
                        align="center",
                        font=dict(color=SPACING_ANNOTATION_COLOR, size=ANNOTATION_FONT_SIZE_SMALL),
                        yshift=-10 # Additional fine-tuning shift if needed
                    )

            # --- Calculate and Add "Overall Skid Span" Annotation (Top Center) ---
            # Use the metric calculated earlier for consistency
            overall_skid_span_viz = overall_skid_span_metric # From metrics section
            if not span_error and overall_skid_span_viz is not None and overall_skid_span_viz > 0:
                 # Position overall span annotation higher up
                 y_top_annotation = y_skid_top + y_padding * 0.8 # Relative to top + padding
                 plot_center_x = 0 # Default center
                 if positions_viz: # Calculate center based on actual skid positions
                     plot_center_x = (positions_viz[0] + positions_viz[-1]) / 2

                 fig.add_annotation(
                     x=plot_center_x,
                     y=y_top_annotation, # Use calculated y
                     text=f'<b>Overall Skid Span: {overall_skid_span_viz:.2f}"</b>',
                     showarrow=False,
                     font=dict(color="black", size=ANNOTATION_FONT_SIZE_LARGE),
                     yshift=10 # Additional fine-tuning shift
                 )

            # --- Configure Plot Layout ---
            # Calculate plot range dynamically to fit skids and annotations
            min_x_pos = positions_viz[0] - skid_w_viz / 2
            max_x_pos = positions_viz[-1] + skid_w_viz / 2
            x_range_padding = max(skid_w_viz * 1.5, (max_x_pos - min_x_pos) * 0.15) # Generous padding
            x_range = [min_x_pos - x_range_padding, max_x_pos + x_range_padding]

            # Estimate Y range needed for annotations
            # Find min/max y from annotations manually or use a fixed large padding
            y_extent = y_padding * 1.5 # Estimate based on padding used
            y_range = [y_center - y_extent, y_center + y_extent]


            fig.update_layout(
                # Axis configuration
                xaxis_title=None, # No title
                yaxis_title=None, # No title
                xaxis=dict(
                    range=x_range,
                    showline=False,       # No axis line
                    showgrid=False,       # No grid lines
                    showticklabels=False, # No tick labels
                    zeroline=False,       # No zero line
                    fixedrange=True       # Disable zoom/pan on x-axis
                ),
                yaxis=dict(
                    range=y_range,
                    showline=False,       # No axis line
                    showgrid=False,       # No grid lines
                    showticklabels=False, # No tick labels
                    zeroline=False,       # No zero line
                    fixedrange=True       # Disable zoom/pan on y-axis
                ),
                # Background colors
                plot_bgcolor='white',     # White plotting area
                paper_bgcolor='white',    # White background outside plot
                # Margins
                margin=dict(l=10, r=10, t=30, b=10), # Minimal margins, slightly more top for legend/title
                # Legend configuration
                showlegend=True,
                legend=dict(
                    orientation="h",      # Horizontal legend
                    yanchor="bottom",     # Anchor legend at its bottom
                    y=1.02,               # Position legend just above the top margin
                    xanchor="right",      # Anchor legend at its right
                    x=1                   # Position legend at the right edge
                ),
                # Height can be adjusted if needed, but autoscaling often works well
                # height = 350 # Example fixed height
                autosize=True # Let Plotly manage size with container
            )
            plot_generated = True
        else:
            # Handle cases where data is missing or invalid for plotting
            log.warning("Plotting skipped due to missing or invalid data (skid_width, skid_count, positions).")
            plot_error = "Plotting skipped due to missing/invalid calculation results."

    except Exception as e:
        plot_error = f"Error generating visualization: {e}"
        log.error(f"Error during visualization generation: {e}", exc_info=True)

# --- Display Plot or Status Message ---
if plot_generated:
    st.plotly_chart(fig, use_container_width=True)
elif plot_error:
    st.warning(f"⚠️ Could not generate visualization: {plot_error}")
elif status not in ["OK", "ERROR", "OVER", "CRITICAL ERROR", "METRIC ERROR", "INIT"]:
     # If status is some other warning, but not OK
    st.info(f"Visualization not applicable for status '{status}'.")
elif status in ["ERROR", "OVER", "CRITICAL ERROR", "METRIC ERROR"]:
    st.warning("Visualization cannot be generated due to calculation errors or invalid inputs.")
else: # Catch-all for other states like INIT
    st.info("Enter parameters and calculate to see the visualization.")


# --- Placeholder for Future Modules ---
st.divider()
st.subheader("Future Modules (Placeholder)")

# Check if the optional floorboard logic was successfully imported
if floorboard_logic_available:
    st.caption("Calculate floorboard layout based on skid results.")
    # Only show button if skid calculation was successful
    if status == "OK":
        # Use session state to keep track of the length input across reruns
        if 'crate_length' not in st.session_state:
            st.session_state.crate_length = 120.0 # Default length

        # Input for crate length needed by floorboard logic
        # Use a unique key to avoid conflicts if the widget is conditionally rendered
        crate_length_input = st.number_input(
            "Enter Crate Length (for Floorboard Calc)",
            min_value=1.0,
            value=st.session_state.crate_length,
            step=1.0,
            key="floorboard_length_input", # Unique key for this widget
            help="Specify the length of the crate base for floorboard calculation."
        )
        st.session_state.crate_length = crate_length_input # Update session state

        # Button to trigger the placeholder calculation
        if st.button("Calculate Floorboard Layout", key="floorboard_button"):
            log.info("Calling floorboard calculation...")
            try:
                # Pass the results dictionary and the length
                floor_results = calculate_floorboard_layout(layout_results, crate_length=st.session_state.crate_length)
                st.write("Floorboard Calculation Results (Placeholder):")
                st.json(floor_results) # Display the placeholder results as JSON
            except Exception as e:
                 log.error(f"Error calling floorboard logic: {e}", exc_info=True)
                 st.error(f"Error during floorboard calculation: {e}")
    else:
        st.info("Skid layout must be calculated successfully (Status: OK) to enable floorboard module.")
else:
    st.caption("Floorboard module (`floorboard_logic.py`) was not found or failed to load.")


# --- Footer or Additional Info ---
st.sidebar.divider()
st.sidebar.info("AutoCrate Wizard v0.2.0\n\n"
                "This tool provides a preliminary skid layout based on input parameters. "
                "Always verify designs against official standards and engineering requirements.")
