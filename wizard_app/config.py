# wizard_app/config.py
"""
Configuration file for AutoCrate Wizard.
Contains shared constants, rules, and default values.
Incorporates styling constants for visualizations.
Version 0.6.0
MODIFIED: Added DECAL_RULES
"""
import math

# --- General Constants ---
FLOAT_TOLERANCE: float = 1e-6
VERSION = "0.6.0" # Major version update reflecting new visualizations and structure

# --- Skid Logic Constants ---
SKID_DIMENSIONS: dict = { "3x4": (2.5, 3.5), "4x4": (3.5, 3.5), "4x6": (5.5, 3.5) }
WEIGHT_RULES: list = [ (500,"3x4",30.0), (4500,"4x4",30.0), (6000,"4x6",41.0), (12000,"4x6",28.0), (20000,"4x6",24.0) ]
MIN_SKID_HEIGHT: float = 3.5
SKID_LENGTH_ASSUMPTION: str = "crate_overall_length"

# --- Floorboard Logic Constants ---
ALL_STANDARD_FLOORBOARDS: dict = { "2x12": 11.25, "2x10": 9.25, "2x8": 7.25, "2x6": 5.5 }
STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS: float = 1.5
MIN_CUSTOM_NARROW_WIDTH: float = 2.50
MAX_CUSTOM_NARROW_WIDTH: float = 5.50
EFFECTIVE_MAX_CUSTOM_WIDTH = MAX_CUSTOM_NARROW_WIDTH - (FLOAT_TOLERANCE * 10)
MIN_STANDARD_BOARD_WIDTH: float = 5.50
MAX_STANDARD_BOARD_WIDTH: float = 11.25
MAX_CENTER_GAP: float = 0.25

# --- Cap & Wall Logic Constants ---
DEFAULT_CLEAT_NOMINAL_THICKNESS: float = 0.75
DEFAULT_CLEAT_NOMINAL_WIDTH: float = 3.5
WALL_PLYWOOD_THICKNESS_MIN: float = 0.25
DEFAULT_WALL_PLYWOOD_THICKNESS: float = 0.25
INTERMEDIATE_CLEAT_THRESHOLD: float = 48.0 # This seems to be a general threshold
MAX_INTERMEDIATE_CLEAT_SPACING = 24.0 # Specific max spacing for intermediate cleats
PLYWOOD_STD_WIDTH = 48.0
PLYWOOD_STD_HEIGHT = 96.0

# --- App Constants ---
DEFAULT_CLEARANCE_ABOVE_PRODUCT: float = 1.5
DEFAULT_PANEL_THICKNESS_UI: float = 0.25

# UI Default Floorboard Selection
DEFAULT_STANDARD_LUMBER_NOMINALS_UI: list = [ k for k, v in ALL_STANDARD_FLOORBOARDS.items() if (v >= MIN_STANDARD_BOARD_WIDTH - FLOAT_TOLERANCE and v <= MAX_STANDARD_BOARD_WIDTH + FLOAT_TOLERANCE) ]
CUSTOM_NARROW_OPTION_TEXT_UI: str = "Use Custom Narrow Board (Fill < 5.5\")"
ALL_LUMBER_OPTIONS_UI: list = sorted(list(ALL_STANDARD_FLOORBOARDS.keys())) + [CUSTOM_NARROW_OPTION_TEXT_UI]
DEFAULT_UI_LUMBER_SELECTION_APP: list = DEFAULT_STANDARD_LUMBER_NOMINALS_UI + [CUSTOM_NARROW_OPTION_TEXT_UI]

# --- Decal Logic (Task 3) ---
# For dimensions and text, using placeholders. Visualizations will interpret these.
# Panel height for Fragile/Handling dimension choice. Overall crate height for CoG vertical location.
DECAL_RULES = {
    "fragile": {
        "id": "fragile",
        "text_content": "FRAGILE", # Text to display or identifier for a symbol
        "dimensions_panel_h_small_thresh": 73.0, # Panel height threshold
        "dimensions_small": {"width": 8.00, "height": 2.31},
        "dimensions_large": {"width": 12.00, "height": 3.50},
        "angle": 10,
        "horizontal_placement": "center_panel_width",
        "vertical_placement": "center_upper_half_panel_height", # Center of the upper half
        "apply_to_panels": ["side", "end"], # Apply to side and end panels
        "count_per_panel": 1 # One per specified panel face
    },
    "handling_horizontal": {
        "id": "handling_horizontal",
        "text_content": "↑☂<y_bin_338>↑", # Placeholder for handling symbols
        "dimensions_panel_h_small_thresh": 37.0, # Panel height threshold
        "dimensions_small": {"width": 3.00, "height": 8.25}, # Note: image shows WxH, but symbols are vertical
        "dimensions_large": {"width": 4.00, "height": 11.00},# Assuming these are overall bounding box of symbols
        "angle": 0,
        "horizontal_placement": "upper_right_corner_panel_width", # Relative to panel
        "vertical_placement": "upper_right_corner_panel_height", # Relative to panel
        "apply_to_panels": ["side", "end"],
        "count_per_panel": 1,
        "notes": "Takes priority over vertical if space permits between cleats. Locate on upper right corner."
    },
    "cog": {
        "id": "cog",
        "text_content": "⊕", # Placeholder for CoG symbol
        "dimensions": {"width": 3.00, "height": 3.00},
        "angle": 0,
        "horizontal_placement": "center_panel_width", # Typically centered on panel width
        # Vertical placement depends on OVERALL CRATE HEIGHT, applied to panel's vertical axis
        "vertical_placement_rules_crate_height": [
            {"max_crate_h": 37.0, "method": "mid_panel_height_relative_to_crate_mid"},
            {"min_crate_h": 37.0, "max_crate_h": 73.0, "offset_from_crate_mid": 4.0},
            {"min_crate_h": 73.0, "max_crate_h": 120.0, "offset_from_crate_mid": 8.0},
            {"min_crate_h": 120.0, "offset_from_crate_mid": 12.0}
        ],
        "apply_to_panels": ["side", "end"], # Applied to each specified panel face
        "count_per_panel": 1,
        "notes": "Apply CoG at center of balance. If stencil lands partially on a cleat it is okay to add material."
    }
}
# Default styling for decals if not specified in rule (can be overridden in rule)
DEFAULT_DECAL_BACKGROUND_COLOR = 'rgba(255, 255, 224, 0.7)' # Light yellow, semi-transparent
DEFAULT_DECAL_TEXT_COLOR = 'rgba(0, 0, 0, 1)'       # Black
DEFAULT_DECAL_FONT_SIZE = 12
DEFAULT_DECAL_BORDER_COLOR = 'rgba(128, 128, 128, 0.7)' # Grey border
DEFAULT_DECAL_BORDER_WIDTH = 1


# --- Visualization Colors & Styles ---
PRODUCT_BOX_COLOR_VIZ: str = "rgba(0, 128, 0, 0.2)"; PRODUCT_BOX_OUTLINE_VIZ: str = "rgba(0, 100, 0, 0.6)"
WALL_PANEL_COLOR_VIZ: str = "#F5F5DC"; WALL_CLEAT_COLOR_VIZ: str = "#A0522D"
CAP_PANEL_COLOR_VIZ: str = "#E0E0E0"; CAP_CLEAT_COLOR_VIZ: str = "#A0522D"
SKID_COLOR_VIZ: str = "#8B4513"; SKID_OUTLINE_COLOR_VIZ: str = "#654321"
FLOORBOARD_STD_COLOR_VIZ: str = "#D2B48C"; FLOORBOARD_CUSTOM_COLOR_VIZ: str = "#B0C4DE"; FLOORBOARD_OUTLINE_COLOR_VIZ: str = "#4682B4"
GAP_COLOR_VIZ: str = "rgba(173, 216, 230, 0.5)"; SPACER_COLOR_VIZ: str = "rgba(211, 211, 211, 0.6)"
OUTLINE_COLOR: str = "#333333"; CLEAT_FONT_COLOR: str = "#FFFFFF"; COMPONENT_FONT_COLOR_DARK: str = "#000000"; DIM_ANNOT_COLOR: str = "#000000"
AXIS_ZERO_LINE_COLOR: str = "#AAAAAA"; GRID_COLOR: str = "#E5E5E5"; LEGEND_FONT_COLOR: str = "#000000"
TITLE_FONT_SIZE: int = 14; AXIS_LABEL_FONT_SIZE: int = 12; TICK_LABEL_FONT_SIZE: int = 10
ANNOT_FONT_SIZE_NORMAL: int = 10; ANNOT_FONT_SIZE_SMALL: int = 8; LEGEND_FONT_SIZE: int = 11
ANNOT_BGCOLOR_LIGHT: str = "rgba(255, 255, 255, 0.7)"; ANNOT_BGCOLOR_DARK: str = "rgba(0, 0, 0, 0.5)"