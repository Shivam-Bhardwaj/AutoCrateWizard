# tests/test_skid_logic.py
"""
Unit tests for the skid_logic module (Python Logic Version).
Uses pytest.
"""
import pytest
import math
# Use absolute import based on expected structure
from wizard_app import skid_logic
from wizard_app import config

# Define some common inputs
DEFAULT_CLEARANCE = 2.0
DEFAULT_PANEL_THK = 0.75
DEFAULT_CLEAT_THK = 0.75

def test_skid_basic_case():
    """Test a standard scenario."""
    # Inputs based on a previous successful run or known good case
    weight = 1500
    prod_w = 60
    results = skid_logic.calculate_skid_layout(
        product_weight=weight,
        product_width=prod_w,
        clearance_side=DEFAULT_CLEARANCE,
        panel_thickness=DEFAULT_PANEL_THK,
        cleat_thickness=DEFAULT_CLEAT_THK
    )
    assert results["status"] == "OK"
    assert results["skid_type"] == "4x4" # Based on weight rules
    assert results["skid_count"] >= 2 # Expect at least 2 for reasonable width
    assert results["spacing_actual"] <= results["max_spacing"] + config.FLOAT_TOLERANCE
    assert len(results["skid_positions"]) == results["skid_count"]
    # Check symmetry (sum of positions should be close to zero)
    assert math.isclose(sum(results["skid_positions"]), 0.0, abs_tol=config.FLOAT_TOLERANCE * results["skid_count"])

def test_skid_low_weight():
    """Test the lowest weight category."""
    results = skid_logic.calculate_skid_layout(400, 30, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "OK"
    assert results["skid_type"] == "3x4"
    assert results["max_spacing"] == 30.0

def test_skid_high_weight():
    """Test a higher weight category."""
    results = skid_logic.calculate_skid_layout(15000, 80, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "OK"
    assert results["skid_type"] == "4x6"
    assert results["max_spacing"] == 24.0

def test_skid_overweight():
    """Test exceeding the maximum weight."""
    results = skid_logic.calculate_skid_layout(25000, 80, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "OVER"

def test_skid_too_narrow():
    """Test when usable width is too small for even one skid."""
    # Choose a product width so small that usable width is less than skid width
    # A 4x4 skid is 3.5" wide. Usable = ProdW + 2*Clr - 2*(PanelT+CleatT)
    # Usable = ProdW + 4 - 2*(0.75+0.75) = ProdW + 4 - 3 = ProdW + 1
    # If ProdW = 2, Usable = 3. Need < 3.5 for error.
    results = skid_logic.calculate_skid_layout(1000, 2, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "ERROR"
    assert "too narrow" in results["message"]

def test_skid_fits_one():
    """Test when usable width only allows one skid."""
    # Usable = ProdW + 1. Need >= 3.5 but < 7.0
    # If ProdW = 5, Usable = 6.
    results = skid_logic.calculate_skid_layout(1000, 5, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "OK"
    assert results["skid_count"] == 1
    assert results["spacing_actual"] == 0.0
    assert results["skid_positions"] == [0.0]

def test_skid_fits_two_tight():
    """Test when usable width just barely fits two skids."""
    # Usable = ProdW + 1. Need >= 7.0
    # If ProdW = 6, Usable = 7.0
    results = skid_logic.calculate_skid_layout(1000, 6, DEFAULT_CLEARANCE, DEFAULT_PANEL_THK, DEFAULT_CLEAT_THK)
    assert results["status"] == "OK"
    assert results["skid_count"] == 2
    # Centerline span = Usable - SkidW = 7.0 - 3.5 = 3.5
    # Spacing = 3.5 / (2-1) = 3.5
    assert math.isclose(results["spacing_actual"], 3.5, abs_tol=config.FLOAT_TOLERANCE)
    assert len(results["skid_positions"]) == 2
    assert math.isclose(results["skid_positions"][0], -1.75, abs_tol=config.FLOAT_TOLERANCE)
    assert math.isclose(results["skid_positions"][1], 1.75, abs_tol=config.FLOAT_TOLERANCE)

# Add more tests for different weight/width combinations, zero clearances etc.

