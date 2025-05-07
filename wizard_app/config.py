# wizard_app/config.py
"""
Configuration file for AutoCrate Wizard.
Contains shared constants, rules, and default values.
Incorporates styling constants for visualizations and BOM.
"""
import math

# --- General Constants ---
FLOAT_TOLERANCE: float = 1e-6
VERSION = "0.5.0" # App version updated to reflect significant changes

# --- Skid Logic Constants ---
SKID_DIMENSIONS: dict = { "3x4": (2.5, 3.5), "4x4": (3.5, 3.5), "4x6": (5.5, 3.5) }
WEIGHT_RULES: list = [ (500,"3x4",30.0), (4500,"4x4",30.0), (6000,"4x6",41.0), (12000,"4x6",28.0), (20000,"4x6",24.0) ]
MIN_SKID_HEIGHT: float = 3.5
SKID_LENGTH_ASSUMPTION: str = "crate_overall_length" # Or specify if different logic needed

# --- Floorboard Logic Constants ---
ALL_STANDARD_FLOORBOARDS: dict = { "2x12": 11.25, "2x10": 9.25, "2x8": 7.25, "2x6": 5.5 }
STANDARD_FLOORBOARD_LUMBER_ACTUAL_THICKNESS: float = 1.5 # Added here for BOM use
MIN_CUSTOM_NARROW_WIDTH: float = 2.50
MAX_CUSTOM_NARROW_WIDTH: float = 5.50
EFFECTIVE_MAX_CUSTOM_WIDTH = MAX_CUSTOM_NARROW_WIDTH - (FLOAT_TOLERANCE * 10)
MIN_STANDARD_BOARD_WIDTH: float = 5.50
MAX_STANDARD_BOARD_WIDTH: float = 11.25
MAX_CENTER_GAP: float = 0.25

# --- Cap & Wall Logic Constants ---
DEFAULT_CLEAT_NOMINAL_THICKNESS: float = 0.75 # Actual thickness used in calcs now
DEFAULT_CLEAT_NOMINAL_WIDTH: float = 3.5     # Actual width used in calcs now
WALL_PLYWOOD_THICKNESS_MIN: float = 0.25
DEFAULT_WALL_PLYWOOD_THICKNESS: float = 0.25 # Default fallback if input invalid
INTERMEDIATE_CLEAT_THRESHOLD: float = 48.0 # Add simplified intermediate if span > this
MAX_INTERMEDIATE_CLEAT_SPACING = 24.0 # Target spacing if implementing more complex logic

# Standard Plywood dimensions for splicing checks
PLYWOOD_STD_WIDTH = 48.0
PLYWOOD_STD_HEIGHT = 96.0

# --- App Constants ---
DEFAULT_CLEARANCE_ABOVE_PRODUCT: float = 1.5 # *** RESTORED CONSTANT ***
DEFAULT_PANEL_THICKNESS_UI: float = 0.25 # Default UI value for panel thickness

# UI Default Floorboard Selection
DEFAULT_STANDARD_LUMBER_NOMINALS_UI: list = [ k for k, v in ALL_STANDARD_FLOORBOARDS.items() if (v >= MIN_STANDARD_BOARD_WIDTH - FLOAT_TOLERANCE and v <= MAX_STANDARD_BOARD_WIDTH + FLOAT_TOLERANCE) ]
CUSTOM_NARROW_OPTION_TEXT_UI: str = "Use Custom Narrow Board (Fill < 5.5\")"
ALL_LUMBER_OPTIONS_UI: list = sorted(list(ALL_STANDARD_FLOORBOARDS.keys())) + [CUSTOM_NARROW_OPTION_TEXT_UI]
DEFAULT_UI_LUMBER_SELECTION_APP: list = DEFAULT_STANDARD_LUMBER_NOMINALS_UI + [CUSTOM_NARROW_OPTION_TEXT_UI]

# --- Visualization Colors & Styles ---
# Component Colors
PRODUCT_BOX_COLOR_VIZ: str = "rgba(0, 128, 0, 0.2)"
PRODUCT_BOX_OUTLINE_VIZ: str = "rgba(0, 100, 0, 0.6)"
WALL_PANEL_COLOR_VIZ: str = "#F5F5DC" # Beige
WALL_CLEAT_COLOR_VIZ: str = "#A0522D" # Sienna
CAP_PANEL_COLOR_VIZ: str = "#E0E0E0" # Light Gray
CAP_CLEAT_COLOR_VIZ: str = "#A0522D" # Sienna
SKID_COLOR_VIZ: str = "#8B4513" # SaddleBrown
SKID_OUTLINE_COLOR_VIZ: str = "#654321" # Darker Brown
FLOORBOARD_STD_COLOR_VIZ: str = "#D2B48C" # Tan (Light Brown)
FLOORBOARD_CUSTOM_COLOR_VIZ: str = "#B0C4DE" # LightSteelBlue
FLOORBOARD_OUTLINE_COLOR_VIZ: str = "#4682B4" # SteelBlue
GAP_COLOR_VIZ: str = "rgba(173, 216, 230, 0.5)" # Light Blue
SPACER_COLOR_VIZ: str = "rgba(211, 211, 211, 0.6)" # Light gray for spacers

# Text & Line Colors
OUTLINE_COLOR: str = "#333333" # Dark Gray for general outlines
CLEAT_FONT_COLOR: str = "#FFFFFF" # White for contrast ON sienna cleats
COMPONENT_FONT_COLOR_DARK: str = "#000000" # Black for text on light components
DIM_ANNOT_COLOR: str = "#000000" # Black for dimension annotations
AXIS_ZERO_LINE_COLOR: str = "#AAAAAA" # Medium Gray for axis zero lines
GRID_COLOR: str = "#E5E5E5" # Light Gray for background grid
LEGEND_FONT_COLOR: str = "#000000" # Black for legend text

# Font Sizes (Standardized)
TITLE_FONT_SIZE: int = 14
AXIS_LABEL_FONT_SIZE: int = 12
TICK_LABEL_FONT_SIZE: int = 10
ANNOT_FONT_SIZE_NORMAL: int = 10 # For dimensions, etc.
ANNOT_FONT_SIZE_SMALL: int = 8   # For labels on smaller components
LEGEND_FONT_SIZE: int = 11

# Annotation Background (for contrast)
ANNOT_BGCOLOR_LIGHT: str = "rgba(255, 255, 255, 0.7)" # Semi-transparent white
ANNOT_BGCOLOR_DARK: str = "rgba(0, 0, 0, 0.5)" # Semi-transparent black