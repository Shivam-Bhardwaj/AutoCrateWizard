# AutoCrate Wizard ⚙️ v0.6.0

AutoCrate Wizard is a logic-first engineering tool built with Python and Streamlit to interactively calculate and visualize parametric layouts for industrial shipping crates based on product inputs and specified construction logic inspired by industry practices and standards.

It helps engineers and designers quickly iterate on crate base (skids, floorboards), wall panels (side/back), and top panel (cap) configurations without needing to perform manual calculations or immediately resort to CAD for basic layout validation.

## 🚀 Features (v0.6.0)

-   **Parametric Inputs:** Easily adjust product weight, dimensions (W, L, H), and necessary clearances via sliders and number inputs.
-   **Construction Parameters:** Define panel thickness and actual dimensions for wall and top panel cleats.
-   **Lumber Selection:** Choose available standard lumber sizes for floorboards and allow/disallow custom narrow boards.
-   **Component Logic:** Includes calculation logic for:
    -   **Skids:** Determines type, count, and spacing based on weight rules and usable crate width.
    -   **Floorboards:** Calculates a symmetrical layout using standard/custom boards to meet gap requirements.
    -   **Wall Panels (Side/Back):** Calculates layout including simplified plywood splicing logic and placement of edge, splice, and intermediate cleats.
    -   **Top Panel (Cap):** Calculates sheathing and cleat layout based on maximum spacing rules.
-   **Overall Dimensions:** Calculates and displays overall external crate dimensions (OD Width, Length, Height).
-   **Status & Metrics:** Provides clear status feedback (OK, Warning, Error) and summary metrics for each calculated assembly.
-   **Multi-View Assembly Visualizations:** Renders interactive 2D orthographic views using Plotly:
    -   **Base Assembly:** Top (XY), Front (XZ), and Side (YZ) views showing skids and floorboards in context, including wall offsets and detailed board layout in side view.
    -   **Wall Assemblies (Side/Back):** Front (XZ) view showing plywood and cleats, and Profile (ZY) view showing thicknesses.
    * **Top Panel Assembly:** Front (XY) view showing sheathing and cleats, and Profile (YZ) view showing thicknesses.
-   **Annotations:** Visualizations include key dimensions and relevant variable names (from calculation results) to aid understanding and mapping to downstream processes (like CAD scripting).
-   **Detailed Component Tables:** Expandable sections display detailed properties (dimensions, positions) for calculated cleats and floorboards using Pandas DataFrames.
-   **Bill of Materials Table:** Generates and displays an assembly-focused Bill of Materials directly in the UI, listing major components (Skids, Floorboards, Panel Assemblies).
-   **Modular Codebase:** Organized into logical Python modules (`skid_logic.py`, etc.) and UI components (`ui_modules/`).
-   **Local & Web-Based:** Runs locally via Streamlit, requiring only Python and standard libraries.

## 🏛️ Relevant Standards (Informational)

The logic implemented in this tool is primarily based on interpretations of common wood crate construction practices and rules derived from analysis of standards like:

* **ASTM D6199:** Standard Practice for Quality of Wood Members of Containers and Pallets (Informs lumber quality, sizing, defects). [cite: 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 250]
* **ASTM D6251 / D6251M:** Standard Specification for Wood-Cleated Panelboard Shipping Boxes (Influences general panel box construction, cleating principles, panel types, styles, classes, ISPM 15 compliance). [cite: 47, 48, 49, 50, 51]
* **ASTM D6039 / D6039M:** Standard Specification for Open and Covered Wood Crates (Provides reference for general crate construction types, styles, load limits, and components like diagonals, struts, joists). [cite: 52, 53, 54, 55, 56, 57]
* **ASTM D7478 / D7478M:** Standard Specification for Heavy Duty Sheathed Wood Crates (Used as a reference for heavy-duty construction principles, Type/Class/Style definitions, load limits, and components like sills/skids). [cite: 39, 40, 41, 42, 43, 44, 45, 46]
* *(Referenced)* **ASTM D4169:** Standard Practice for Performance Testing of Shipping Containers and Systems (Used to validate performance if deviating from prescriptive standards). [cite: 68, 69, 71]

**Disclaimer:** This tool automates calculations based on *interpretations* of specific versions of these standards[cite: 76, 77, 301]. It does **not** guarantee full compliance with any official ASTM standard version for a given application[cite: 261]. Users are **solely responsible** for ensuring their final crate design meets all necessary official standard requirements, contractual obligations, and regulatory constraints through independent verification and professional judgment[cite: 261, 302, 305]. Always refer to the official ASTM documents[cite: 304].

## 📁 Project Structure (v0.6.0)

wizard_app/
├── init.py
├── app.py               # Main Streamlit application, orchestration, local BOM logic
├── config.py            # Shared constants, rules, default values
├── skid_logic.py        # Skid calculation logic
├── floorboard_logic.py  # Floorboard calculation logic
├── wall_logic.py        # Wall panel calculation logic
├── cap_logic.py         # Top panel (cap) calculation logic
├── explanations.py      # Explanation text strings for UI
├── ui_modules/          # Directory for UI component modules
│   ├── init.py
│   ├── sidebar.py       # Defines the sidebar inputs
│   ├── status.py        # Defines the status display component
│   ├── metrics.py       # Defines the summary metrics display
│   ├── visualizations.py# Visualization generation and display functions
│   └── details.py       # Defines the detailed table displays
├── .gitignore           # Standard Git ignore file
├── README.md            # This file
└── CHANGELOG.md         # Log of changes


## 🛠 How to Run

1.  **Install Python:** Ensure you have Python 3.9 or newer installed ([python.org](https://www.python.org/)).
2.  **Get Code:** Obtain the `wizard_app` directory containing all the `.py` files. Ensure the `ui_modules` subdirectory and its contents are included.
3.  **Install Libraries:** Open a terminal or command prompt, navigate to the directory *containing* the `wizard_app` folder, and run:
    ```bash
    pip install streamlit plotly pandas
    ```
4.  **Run the App:** In the same terminal, execute:
    ```bash
    streamlit run wizard_app/app.py
    ```
5.  **View:** Open the application in your web browser (usually at `http://localhost:8501` or similar). Interact with the sidebar inputs.

## 📦 Requirements

-   Python 3.9+
-   Streamlit (`pip install streamlit`)
-   Plotly (`pip install plotly`)
-   Pandas (`pip install pandas`)

## 🧱 What’s Next

This version provides a stable platform with comprehensive visualization capabilities and on-screen BOM data.

**Planned / Possible Future Features:**

-   Re-implement robust export options (e.g., stable PDF generation for BOM table, CSV export).
-   Investigate reliable and performant methods for including schematic drawings in exported reports.
-   Refine calculation logic based on further validation against specific standard clauses or engineering requirements.
-   Add more sophisticated intermediate cleat spacing logic.
-   Implement saving/loading of crate configurations.

## 🤝 Contributing

(Keep contribution guidelines as before, if applicable)

## ⚖️ License

(Keep license section as before, if applicable)

*(Disclaimer repeated for emphasis: This tool is provided as-is for visualization and logic validation. Always verify cr