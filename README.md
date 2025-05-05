# AutoCrate Wizard ⚙️

AutoCrate Wizard is a logic-first engineering visualization tool that helps you validate and visualize custom shipping crate skid and floorboard configurations — based on product weight and dimensions according to specified standards — without needing to open CAD. Built for speed, simplicity, and clear visualization.

## 🚀 Features

-   🔧 **Parametric Configuration** – Easily adjust product weight, width, and length using sliders.
-   📐 **Crate Constants** – Define crate construction details like side clearance, panel thickness, and cleat thickness.
-   🪵 **Lumber Selection** - Choose available floorboard lumber sizes (e.g., 2x12, 2x6).
-   🧠 **Logic-based Skid Placement** – Automatically calculates required skid type (e.g., 3x4, 4x4, 4x6), skid count, and center-to-center spacing based on product weight (up to 20,000 lbs) and calculated usable width, adhering to defined maximum spacing rules.
-   🔨 **Symmetrical Floorboard Layout** - Calculates a butt-to-butt floorboard layout symmetrically from the outside edges inwards, using selected standard lumber (>=5.5" & <=11.25"). Prioritizes filling the center gap with the widest standard board that leaves a gap <= 0.25". If that fails, allows one optional "Custom" narrow board (>=2.5" & <5.5") to fill the remaining space exactly.
-   📊 **Key Metrics Display** – Shows important calculated values in organized columns: Crate Dimensions (Width, Length), Skid Setup (Type, Width, Count), Skid Spacing (Actual, Max Allowed, Overall Span), and Floorboard Summary (Status, Total Boards, Board Length, Target Span, Center Gap, Custom Width Used, Counts, Sanity Check).
-   📦 **2D Visualizations** – Renders clear, annotated top-down views of the calculated skid and floorboard layouts using Plotly. Visualizes the center gap with distinct colors for OK vs. Warning status.
-   ✅ **Input Validation & Status** – Provides immediate feedback on the calculation status (OK, Error, Warning, Over Limit) for both skids and floorboards, along with informative messages.
-   📑 **Detailed Floorboard Table** - Displays a table listing each calculated floorboard's number, nominal size, actual width, and starting position.
-   🔁 **Runs Locally** – Requires only Python and standard libraries (Streamlit, Plotly, Pandas). Zero backend, no login, firewall-safe.
-   📂 **Modular Codebase** – Organized into `app.py` (UI), `skid_logic.py`, and `floorboard_logic.py` for easier maintenance and extension.

---

## 📁 Project Structure


AutoCrateWizard/
├── app.py               # Streamlit app: UI, metrics, Plotly visualization
├── skid_logic.py        # Core logic: Skid type, count, spacing, position calculation
├── floorboard_logic.py  # Core logic: Floorboard layout calculation
├── .gitignore           # Standard Git ignore file
├── README.md            # This file
└── CHANGELOG.md         # Log of changes


*(This flat structure is used in the current implementation.)*

---

## 🛠 How to Run

1.  **Install Python:** Ensure you have Python 3.9 or newer installed ([python.org](https://www.python.org/)).
2.  **Download Files:** Place `app.py`, `skid_logic.py`, and `floorboard_logic.py` in the same directory.
3.  **Install Libraries:** Open a terminal or command prompt **in that directory** and run:
    ```bash
    pip install streamlit plotly pandas
    ```
4.  **Run the App:** In the same terminal, execute:
    ```bash
    streamlit run app.py
    ```
5.  **View:** This command should automatically open the AutoCrate Wizard application in your default web browser (usually at `http://localhost:8501`). Interact with the sliders and inputs in the sidebar to see the results and visualization update live.

---

## 📦 Requirements

-   Python 3.9+
-   Streamlit (`pip install streamlit`)
-   Plotly (`pip install plotly`)
-   Pandas (`pip install pandas`)
-   Internet connection required only for the first-time package installation.

---

## 🧱 What’s Next

This version focuses on validating the core skid and floorboard layout logic (`skid_logic.py`, `floorboard_logic.py`) and providing clear, annotated top-down visualizations (`app.py`) based on the specified weight/dimension rules.

**Planned / Possible Future Features:**

-   Add Side/End view visualizations.
-   Incorporate logic for cap and wall assemblies.
-   Develop export options (e.g., summary text, CSV, potentially metadata for CAD).
-   Explore a 3D visualizer module (e.g., using Plotly 3D or Three.js).
-   Enhance error handling and user guidance (e.g., more specific warnings).
-   Add functionality for saving/loading configurations.
-   Refine visualization aesthetics and interactivity.

---

## 🤝 Contributing

PRs welcome! Fork the repo, create a feature branch (`git checkout -b feature/YourFeature`), commit your changes (`git commit -m 'Add some feature'`), push to the branch (`git push origin feature/YourFeature`), and open a Pull Request. Please provide clear commit messages and describe your changes.

---

## ⚖️ License

This project is intended as a demonstration and utility. If distributing, consider adding an open-source license like the MIT License. Create a `LICENSE` file with the desired license text.

*(Disclaimer: This tool is provided as-is for visualization and logic validation. Always verify crate designs against official shipping standards and perform necessary engineering checks before construction and use.)*
