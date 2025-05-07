# Changelog

All notable changes to this project will be documented in this file.

## [0.4.3] - 2025-05-07

### Added
- **Cap Assembly Visualization Enhancements (`app.py`):**
    - Implemented multiple views for the cap assembly using `st.tabs`:
        - Retained the existing "Top View".
        - Added a "Front View" (orthographic view along cap width) showing panel and cleat profiles.
        - Added a "Side View" (orthographic view along cap length) showing panel and cleat profiles.
    - Created a helper function `create_cap_ortho_view` in `app.py` to generate the front and side views.
- **Product Actual Height Input (`app.py`):**
    - Added a slider input for "Product Actual Height" in the sidebar.
    - Added an input for "Clearance Above Product (to Cap)".
- **Overall Crate Height Calculation & Display (`app.py`):**
    - Implemented calculation for `crate_overall_height_external` considering skid height, floorboard thickness, product height, clearances, cap panel, and cap cleat thickness.
    - Added "Overall Height (OD)" to the "Crate Overall" summary metrics.

### Changed
- Updated version number to 0.4.3 in `app.py` and documentation.
- Renamed "Clearance per Side" input to "Clearance Side (Product W/L)" for clarity in `app.py`.
- Renamed "Cleat Thickness" input to "Framing Cleat Thickness (Side/End Walls)" for clarity in `app.py`.
- Updated footer text in `app.py` to: "AutoCrate Wizard v0.4.3\nFor inquiries, contact Shivam Bhardwaj."
- Minor refinements to tolerance usage in visualization sections of `app.py`.
- Updated `README.md` to reflect new features and input changes.

## [0.4.2] - 2025-05-07

### Fixed
- **`app.py`:** Fixed `NameError: name 'FLOAT_TOLERANCE' is not defined` in the `format_metric` function by defining `FLOAT_TOLERANCE` at the global scope of `app.py`.

## [0.4.0] - 2025-05-06

### Added
- **Cap Assembly Logic (`cap_logic.py`):**
    - Created new `cap_logic.py` module for all top cap calculations.
    - Implemented `calculate_cap_layout` function.
- **Integration of Cap Logic into `app.py`**.
- **Cap-Specific UI Inputs (Sidebar in `app.py`)**.
- **Display Cap Results (Main Area in `app.py`)**.
- **Cap Visualization (Main Area in `app.py` - initial top-down view)**.
- **Cap Details Table (Main Area in `app.py`)**.

## v0.3.19 - 2025-05-05
### Fixed
- Corrected import statements in `app.py` to use absolute imports (`from module import ...`) instead of relative imports (`from .module import ...`) to resolve `ImportError` when running `app.py` directly.

### Changed
- Updated version number across all files to 0.3.19.
- Improved visualization font colors in `app.py` for better contrast on skid and floorboard elements.
- Added `FLOAT_TOLERANCE` to `skid_logic.py` and used it in floating-point comparisons for increased robustness.

## [0.3.5] - 2025-05-05
### Changed
- **Refined Floorboard Logic:** Removed "2x4" from standard lumber definitions in `floorboard_logic.py`. Narrow boards (< 5.5") are now only placed as a single "Custom" center board.
- **Explicit Custom Board Option:** Added a "Use Custom Narrow Board" checkbox option to the lumber multiselect in `app.py`. The `calculate_floorboard_layout` function now takes an `allow_custom_narrow_board` boolean flag. The custom board is only considered for center fill if this flag is True and the span is appropriate (2.5" <= span < 5.5").
- Updated UI text and defaults in `app.py` to reflect the new custom board option.
- Updated example test cases in `floorboard_logic.py`.

## [0.3.4] - 2025-05-05
### Changed
- **Prioritized Gap Minimization in Floorboards:** Modified `floorboard_logic.py` center-fill logic. It now prioritizes using a "Custom" narrow board (if span allows and slot is free) to achieve a zero gap *before* attempting to place a standard board that might leave a small gap.
- **Updated Visualization Colors:** Changed floorboard plot colors in `app.py` (Standard: Light Brown, Custom: Dark Brown, Gap: Light Blue).
- Updated example test case expectations in `floorboard_logic.py` to match the new logic.

## [0.3.2] - 2025-05-05
### Added
- Implemented `floorboard_logic.py` for symmetrical floorboard layout calculation based on available standard lumber and center-fill rules.
- Added floorboard visualization (top-down) with gap highlighting to `app.py`.
- Added floorboard summary metrics (Status, Total Boards, Board Length, Target Span, Center Gap, Custom Width Used, Counts, Sanity Check) in a dedicated column in `app.py`.
- Added floorboard details table (Board #, Nominal Size, Width, Position) using Pandas DataFrame in `app.py`.
- Included lumber selection multiselect (`available_lumber`) in the sidebar of `app.py`.
- Implemented logic to handle one optional "Custom" narrow board for center fill in `floorboard_logic.py`.
- Added `product_length` slider input to `app.py`.
### Changed
- Refined UI layout in `app.py` to use 4 columns for summary metrics.
- Updated `README.md` to reflect floorboard features and dependencies.
- Updated dependencies to include `pandas`.
- Updated app version in UI footer to v0.3.2.
- Ensured calculations update automatically on input change.
- Updated `calculate_overall_skid_span` usage and potential fallback in `app.py`.
- Refined comments and logging in all Python files.

## [0.2.1] - 2025-05-04
### Fixed
- Corrected the skid positioning logic in `skid_logic.py` to ensure the overall physical span of the skids (outer edge to outer edge) fits precisely within the calculated `usable_width` by adjusting the `centerline_span` calculation. Added verification checks to `if __name__ == "__main__":` block.

## [0.2.0] - 2025-05-04
### Changed
- Refactored UI: Removed debugging elements, simplified visualization aesthetics.
- Updated Metrics: Replaced "Calc. Usable Width" metric with "Overall Skid Span".
- Standardized Inputs: Adjusted slider steps.
- Generalized Code: Removed specific standard references from comments/UI text where appropriate.
- Updated README to reflect current features.
- Added/Renamed .gitignore.

## [0.1.0] - 2025-05-04
### Added
- Initial release of AutoCrate Wizard.
- Streamlit app (`app.py`) with basic inputs.
- Initial skid recommendation logic (`skid_logic.py`).
- Placeholder `floorboard_logic.py`.
- Basic Plotly 2D visualization.
