# wizard_app/__init__.py
# AutoCrate Wizard Package
# This file makes Python treat the directory as a package.

# You can optionally define package-level names here,
# for example, by importing key functions/classes from submodules
# to make them accessible directly from the package.
# from .app import main_function # Example

VERSION = "0.4.4"

# Ensure config is loaded if other modules in the package need it upon import.
# However, individual modules should ideally import config themselves.
try:
    from . import config
except ImportError:
    # This might happen if a submodule is run directly as a script
    # and the package structure isn't correctly recognized.
    # For direct script runs, they might need to adjust their Python path
    # or use absolute imports if the package is installed.
    pass