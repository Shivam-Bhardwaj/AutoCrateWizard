# AutoCrate Wizard ⚙️

AutoCrate Wizard is a logic-first engineering visualization tool that helps you validate and visualize custom shipping crate skid configurations — based on product weight and dimensions according to specified standards — without needing to open CAD. Built for speed, simplicity, and clear visualization.

## 🚀 Features

-   🔧 **Parametric Configuration** – Easily adjust product weight and width using sliders.
-   📐 **Crate Constants** – Define crate construction details like side clearance, panel thickness, and cleat thickness.
-   🧠 **Logic-based Skid Placement** – Automatically calculates required skid type (e.g., 3x4, 4x4, 4x6), skid count, and center-to-center spacing based on product weight (up to 20,000 lbs) and calculated usable width, adhering to defined maximum spacing rules.
-   📊 **Key Metrics Display** – Shows important calculated values like Crate Width, Skid Type, Overall Skid Span, Skid Width, Skid Count, Actual Spacing, and Max Allowed Spacing.
-   📦 **2D Skid Visualization** – Renders a clear top-down view of the calculated skid layout using Plotly, including annotations for skid numbers, centerline positions, spacing, and overall span.
-   ✅ **Input Validation & Status** – Provides immediate feedback on the calculation status (OK, Error, Over Limit) and informative messages.
-   🔁 **Runs Locally** – Requires only Python and standard libraries (Streamlit, Plotly). Zero backend, no login, firewall-safe.
-   📂 **Ready to Extend** – Modular Python codebase (`skid_logic.py`, `app.py`, placeholder `floorboard_logic.py`) allows for adding more features like floorboard calculations, side/end views, or export capabilities.

---

## 📁 Project Structure


AutoCrateWizard/
├── app.py               # Streamlit app: UI, metrics, Plotly visualization
├── skid_logic.py        # Core logic: Skid type, count, spacing, position calculation
├── floorboard_logic.py  # Placeholder for future floorboard logic
├── .gitignore           # Standard Git ignore file
└── README.md            # This file


*(This flat structure is used in the current implementation.)*

---

## 🛠 How to Run

1.  **Install Python:** Ensure you have Python 3.9 or newer installed ([python.org](https://www.python.org/)).
2.  **Download Files:** Place `app.py`, `skid_logic.py`, and `floorboard_logic.py` in the same directory.
3.  **Install Libraries:** Open a terminal or command prompt **in that directory** and run:
    ```bash
    pip install streamlit plotly
    ```
    *(Note: `pandas` and `numpy` were listed as potential dependencies in the initial request but are not currently used directly in the provided code. Install them if future features require them: `pip install pandas numpy`)*
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
-   Internet connection required only for the first-time package installation.

---

## 🧱 What’s Next (v0.2.0 Focus)

This version focuses on validating the core skid layout logic (`skid_logic.py`) and providing a clear, annotated top-down visualization (`app.py`) based on the specified weight/dimension rules.

**Planned / Possible Future Features:**

-   Implement `floorboard_logic.py` for calculation and visualization.
-   Add Side/End view visualizations.
-   Incorporate logic for cap and wall assemblies.
-   Develop export options (e.g., summary text, CSV, potentially metadata for CAD).
-   Explore a 3D visualizer module (e.g., using Plotly 3D).
-   Enhance error handling and user guidance.
-   Add functionality for saving/loading configurations.

---

## 🤝 Contributing

PRs welcome! Fork the repo, create a feature branch (`git checkout -b feature/YourFeature`), commit your changes (`git commit -m 'Add some feature'`), push to the branch (`git push origin feature/YourFeature`), and open a Pull Request. Please provide clear commit messages and describe your changes.

---

## ⚖️ License

This project is intended as a demonstration and utility. If distributing, consider adding an open-source license like the MIT License. Create a `LICENSE` file with the desired license text.

*(Disclaimer: This tool is provided as-is for visualization and logic validation. Always verify crate designs against official shipping standards and perform necessary engineering checks before construction and use.)*
