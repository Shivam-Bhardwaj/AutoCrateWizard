AutoCrate Wizard
AutoCrate Wizard is a logic-first engineering visualization tool that helps you validate and visualize custom crate configurations — like skid count, floor geometry, and height clearances — without needing to open CAD. Built for speed, simplicity, and cross-team sharing.

🚀 Features
🔧 Crate Configuration via Sliders – Easily adjust width, height, length, and weight

📦 2D Visuals – Top, Front, and Side views rendered live with Plotly

🧠 Logic-based Skid Placement – Calculates skid count based on dimensions and load

🔁 Runs Locally – Zero backend, no login, firewall-safe

📂 Ready to Extend – Modular Python codebase to add panels, cleats, floorboards, or exports

📁 Project Structure
AutoCrateWizard/
├── wizard_app/
│   ├── __init__.py
│   ├── core.py          # Logic rules for skid placement
│   ├── visualizer.py    # 2D Plotly renderings
│   └── app.py           # Streamlit app and user interface
├── run_app.bat          # One-click Windows launcher
├── run_app.sh           # Unix/Linux launcher
├── .gitignore
├── CHANGELOG.md
├── LICENSE              # MIT License (Open Source)
├── README.md
├── git_push_wizard.bat
└── bump_changelog.py

🛠 How to Run (Beginner-Friendly)
🪟 Windows: Double-click run_app.bat
🐧 Mac/Linux: Run bash run_app.sh

Or run it manually:

pip install streamlit plotly
streamlit run wizard_app/app.py

This opens http://localhost:8501 in your browser.

📦 Requirements
Python 3.9 or newer

Internet only required for first-time package install

🧱 What’s Next
This is version v0.1.0, built for logic and crate visual validation.

Planned features:

Floorboard rendering

Cap and wall assemblies

Export to NX or STEP metadata

3D visualizer module

🤝 Contributing
PRs welcome! Fork the repo, create a feature branch, and submit with a clear commit message.

⚖ License
This project is open-source under the MIT License. See LICENSE file for details.

Note: This tool is intended as a general-purpose crate layout utility and does not represent any proprietary tooling or client-specific systems.