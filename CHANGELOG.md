# Changelog

All notable changes to this project will be documented in this file.

## [0.6.3] - 2025-05-08 

### Fixed
- Calculation Summary: Removed custom HTML styling from metric labels in `wizard_app/ui_modules/metrics.py` to resolve an issue where HTML tags were visible and incorrectly formatted. Metric labels are now displayed as plain text for improved readability, with group titles rendered in bold. 

### Added

- **Regenerate Crate Button:** Added a primary "Regenerate Crate" button to the top of the sidebar (`wizard_app/ui_modules/sidebar.py`). 

### Changed
- **Calculation Trigger:** Core layout calculations (Skid, Floor, Wall, Cap) and display updates in the main app (`wizard_app/app.py`) are now primarily triggered only by the "Regenerate Crate" button press or on the initial application load. - **Sidebar Layout:** Optimized sidebar UI (`wizard_app/ui_modules/sidebar.py`) by grouping less frequently used options ("Construction Details", "Floorboard Options", "Top Panel Options") into collapsible `st.expander` sections. - **Session State Handling:** Refined session state management for sidebar inputs (`wizard_app/ui_modules/sidebar.py`) using explicit widget keys and session state value keys for increased robustness, especially for `st.number_input` and `st.multiselect`. - **Plotly Chart Interaction:** Disabled default zoom and pan functionality on all Plotly schematic views (`wizard_app/ui_modules/visualizations.py`) by setting `fixedrange=True` for axes. ### Fixed
- **Input Synchronization:** Improved synchronization logic within the `input_slider_combo` helper function (`wizard_app/ui_modules/sidebar.py`) to ensure slider and number input values remain consistent using session state. ```


## [0.6.0] - 2025-05-07

### Added

-   **Base Assembly Visualization (`visualizations.py`, `app.py`):** Implemented multi-view (Top XY, Front XZ, Side YZ) orthographic display for the combined Skid and Floorboard assembly, showing components in context using side-by-side columns. [cite: 1]
-   **Detailed Floorboard Side View:** The Base Assembly Side View now renders individual floorboard profiles and the center gap, illustrating the layout along the crate length.
-   **Wall Assembly Visualization (`visualizations.py`, `app.py`):** Implemented multi-view (Front XZ, Profile ZY) display for Side and Back wall panel assemblies.
-   **Top Panel Assembly Visualization (`visualizations.py`, `app.py`):** Implemented multi-view (Front XY, Profile YZ) display for the Top Panel (Cap) assembly.
-   **Variable Annotations:** Added key Python variable names (from results dictionaries) alongside dimension values in schematic annotations to aid mapping logic to visuals.
-   **Local BOM Table (`app.py`):** Integrated BOM data compilation directly into `app.py` based on assembly structure (reflecting production drawing examples) and displayed results using `st.dataframe`. [cite: 8, 30, 166]
-   **ASTM Standard Context (`README.md`):** Added section outlining relevant ASTM standards (D6199, D6251, D6039, D7478) that inform the design logic, based on research document. [cite: 1]

### Changed

-   **Code Structure:** Solidified refactoring into UI modules (`ui_modules/`). BOM logic now local to `app.py` (removing `bom_utils.py`).
-   **Visualization Functionality (`visualizations.py`):** Separated Plotly figure *creation* logic into internal helper functions (`_create_..._fig`) from figure *display* logic (`display_...`).
-   **Axis/Font Styling (`visualizations.py`, `config.py`):** Visualizations now show coordinate axes (X, Y, Z labels based on view) with zero lines but no grid lines. Standardized font sizes and ensured dark font colors for better readability.
-   **Floorboard Visualization Logic (`visualizations.py`):** Corrected X-axis alignment to match skid span and Y-axis positioning to include wall offsets in the Base Assembly Top View.
-   **Skid Visualization Logic (`visualizations.py`):** Replaced standalone skid view with integrated Base Assembly views (Front XZ shows skid profiles).
-   **Version:** Updated version to 0.6.0 in `config.py`.

### Removed

-   **PDF Generation (`app.py`):** Removed all PDF generation functionality (including image export via Kaleido and FPDF2 usage, buttons, session state) due to performance/stability issues. BOM is now displayed as a table only.
-   **`bom_utils.py`:** File deleted as logic moved into `app.py`.

### Fixed

-   Resolved various `ImportError`, `NameError`, `AttributeError`, and `IndentationError` issues related to module loading, session state, and code structure encountered during previous development iterations.
-   Corrected data handling in `details.py` to prevent `pyarrow` errors when displaying tables with missing numeric values.

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
