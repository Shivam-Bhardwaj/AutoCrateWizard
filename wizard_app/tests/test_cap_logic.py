# tests/test_cap_logic.py
"""
Unit tests for the cap_logic module (Python Logic Version).
Uses pytest.
"""
import pytest
import math
# Use absolute import based on expected structure
from wizard_app import cap_logic
from wizard_app import config

# Define common inputs
CRATE_W = 60.0
CRATE_L = 80.0
PANEL_T = 0.75
CLEAT_T = 0.75
CLEAT_W = 3.5
MAX_SPACING = 24.0

def test_cap_basic():
    """Test a standard cap layout."""
    results = cap_logic.calculate_cap_layout(
        crate_overall_width=CRATE_W,
        crate_overall_length=CRATE_L,
        cap_panel_sheathing_thickness=PANEL_T,
        cap_cleat_nominal_thickness=CLEAT_T,
        cap_cleat_nominal_width=CLEAT_W,
        max_top_cleat_spacing=MAX_SPACING
    )
    assert results["status"] == "OK"
    assert results["cap_panel_width"] == CRATE_W
    assert results["cap_panel_length"] == CRATE_L
    assert results["cap_panel_thickness"] == PANEL_T

    # Longitudinal (span W=60, max_space=24, cleatW=3.5)
    # Centerline = 60 - 3.5 = 56.5. Spaces needed = ceil(56.5/24) = 3. Cleats = 3+1 = 4
    lc = results["longitudinal_cleats"]
    assert lc["count"] == 4
    assert math.isclose(lc["actual_spacing"], 56.5 / 3, abs_tol=config.FLOAT_TOLERANCE)
    assert len(lc["positions"]) == 4

    # Transverse (span L=80, max_space=24, cleatW=3.5)
    # Centerline = 80 - 3.5 = 76.5. Spaces needed = ceil(76.5/24) = 4. Cleats = 4+1 = 5
    tc = results["transverse_cleats"]
    assert tc["count"] == 5
    assert math.isclose(tc["actual_spacing"], 76.5 / 4, abs_tol=config.FLOAT_TOLERANCE)
    assert len(tc["positions"]) == 5

def test_cap_narrow():
    """Test a narrow crate where only 1 or 2 longitudinal cleats fit."""
    # Width = 6. CleatW = 3.5. Fits 1.
    results = cap_logic.calculate_cap_layout(6.0, CRATE_L, PANEL_T, CLEAT_T, CLEAT_W, MAX_SPACING)
    assert results["status"] == "OK"
    assert results["longitudinal_cleats"]["count"] == 1
    assert results["longitudinal_cleats"]["positions"] == [0.0]
    assert results["transverse_cleats"]["count"] >= 2 # Length is still large

    # Width = 7. CleatW = 3.5. Fits 2 exactly.
    results = cap_logic.calculate_cap_layout(7.0, CRATE_L, PANEL_T, CLEAT_T, CLEAT_W, MAX_SPACING)
    assert results["status"] == "OK"
    assert results["longitudinal_cleats"]["count"] == 2
    assert math.isclose(results["longitudinal_cleats"]["actual_spacing"], 7.0 - 3.5, abs_tol=config.FLOAT_TOLERANCE) # 3.5
    assert len(results["longitudinal_cleats"]["positions"]) == 2

def test_cap_short():
    """Test a short crate where transverse cleats might be limited."""
     # Length = 6. CleatW = 3.5. Fits 1. Rule forces 1.
    results = cap_logic.calculate_cap_layout(CRATE_W, 6.0, PANEL_T, CLEAT_T, CLEAT_W, MAX_SPACING)
    assert results["status"] == "WARNING" # Warning because only 1 transverse
    assert results["transverse_cleats"]["count"] == 1
    assert results["transverse_cleats"]["positions"] == [0.0]
    assert results["longitudinal_cleats"]["count"] >= 2 # Width is still large

    # Length = 7. CleatW = 3.5. Fits 2. Rule forces 2.
    results = cap_logic.calculate_cap_layout(CRATE_W, 7.0, PANEL_T, CLEAT_T, CLEAT_W, MAX_SPACING)
    assert results["status"] == "OK"
    assert results["transverse_cleats"]["count"] == 2
    assert math.isclose(results["transverse_cleats"]["actual_spacing"], 7.0 - 3.5, abs_tol=config.FLOAT_TOLERANCE) # 3.5
    assert len(results["transverse_cleats"]["positions"]) == 2

def test_cap_no_cleats():
    """Test dimensions too small for any cleats."""
    results = cap_logic.calculate_cap_layout(2.0, 3.0, PANEL_T, CLEAT_T, CLEAT_W, MAX_SPACING)
    assert results["status"] == "ERROR" # Or WARNING depending on exact logic if one fits but not others
    assert results["longitudinal_cleats"]["count"] == 0
    assert results["transverse_cleats"]["count"] == 0

# Add more tests for different spacing scenarios.
