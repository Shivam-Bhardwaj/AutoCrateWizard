# tests/test_floorboard_logic.py
"""
Unit tests for the floorboard_logic module (Python Logic Version).
Uses pytest.
"""
import pytest
import math
# Use absolute import based on expected structure
from wizard_app import floorboard_logic
from wizard_app import config

# Mock skid results for testing floorboards
MOCK_SKID_OK_MULTI = {
    "skid_type": "4x4", "skid_width": 3.5, "skid_height": 3.5,
    "skid_count": 3, "spacing_actual": 30.0, "max_spacing": 30.0,
    "crate_width": 70.0, # Example
    "usable_width": 64.0, # Example
    "skid_positions": [-30.0, 0.0, 30.0], # Example positions for 3 skids
    "status": "OK", "message": "Mock OK"
}
# Overall span for MOCK_SKID_OK_MULTI: abs( (30 + 3.5/2) - (-30 - 3.5/2) ) = abs(31.75 - (-31.75)) = 63.5
MOCK_SKID_OK_SINGLE = {
    "skid_type": "3x4", "skid_width": 2.5, "skid_height": 3.5,
    "skid_count": 1, "spacing_actual": 0.0, "max_spacing": 30.0,
    "crate_width": 10.0, "usable_width": 4.0, "skid_positions": [0.0],
    "status": "OK", "message": "Mock OK Single"
}
# Overall span for MOCK_SKID_OK_SINGLE: 2.5

DEFAULT_PROD_LEN = 60.0
DEFAULT_CLR_SIDE = 2.0
DEFAULT_AVAIL_NOM = ["2x6", "2x8", "2x10", "2x12"]

def test_floorboard_basic():
    """Test standard placement without custom board."""
    # Target span = 60 + 2*2 = 64
    # Expect pairs of 2x12 (11.25), 2x10 (9.25), 2x8 (7.25), 2x6 (5.5)
    # Total width = 2 * (11.25 + 9.25 + 7.25 + 5.5) = 2 * 33.25 = 66.5 > 64
    # Should place pairs of 12, 10, 8 -> 2*(11.25+9.25+7.25) = 2*27.75 = 55.5
    # Remaining = 64 - 55.5 = 8.5. Should not fit 2x6 pair (11).
    # Gap should be 8.5, which is > 0.25, but custom not allowed here.
    results = floorboard_logic.calculate_floorboard_layout(
        skid_layout_data=MOCK_SKID_OK_MULTI,
        product_length=DEFAULT_PROD_LEN,
        clearance_side=DEFAULT_CLR_SIDE,
        available_nominal_sizes=DEFAULT_AVAIL_NOM,
        allow_custom_narrow_board=False # No custom
    )
    assert results["status"] == "WARNING" # Gap too large
    assert results["narrow_board_used"] is False
    assert results["custom_board_width"] is None
    assert math.isclose(results["center_gap"], 8.5, abs_tol=config.FLOAT_TOLERANCE)
    assert len(results["floorboards"]) == 6 # 3 pairs
    assert results["board_counts"] == {"2x12": 2, "2x10": 2, "2x8": 2}
    assert math.isclose(results["floorboard_length_across_skids"], 63.5) # From mock skid data

def test_floorboard_needs_custom():
    """Test when a custom board is needed and allowed."""
    # Same as basic, target span = 64. Remaining gap = 8.5
    # Custom allowed, gap > 0.25. Need custom width = 8.5 - 0.25 = 8.25
    results = floorboard_logic.calculate_floorboard_layout(
        skid_layout_data=MOCK_SKID_OK_MULTI,
        product_length=DEFAULT_PROD_LEN,
        clearance_side=DEFAULT_CLR_SIDE,
        available_nominal_sizes=DEFAULT_AVAIL_NOM,
        allow_custom_narrow_board=True # Allow custom
    )
    assert results["status"] == "OK" # Gap should be acceptable now
    assert results["narrow_board_used"] is True
    assert math.isclose(results["custom_board_width"], 8.25, abs_tol=config.FLOAT_TOLERANCE)
    assert math.isclose(results["center_gap"], 0.25, abs_tol=config.FLOAT_TOLERANCE)
    assert len(results["floorboards"]) == 7 # 3 pairs + 1 custom
    assert results["board_counts"] == {"2x12": 2, "2x10": 2, "2x8": 2, "Custom": 1}

def test_floorboard_small_gap_no_custom_needed():
    """Test when remaining gap is small, custom allowed but not needed."""
    # Make target span slightly larger than total width of 3 pairs (55.5)
    # Target span = 55.5 + 0.1 = 55.6
    prod_len = 55.6 - 2 * DEFAULT_CLR_SIDE # 51.6
    results = floorboard_logic.calculate_floorboard_layout(
        skid_layout_data=MOCK_SKID_OK_MULTI,
        product_length=prod_len,
        clearance_side=DEFAULT_CLR_SIDE,
        available_nominal_sizes=DEFAULT_AVAIL_NOM,
        allow_custom_narrow_board=True # Allow custom
    )
    assert results["status"] == "OK"
    assert results["narrow_board_used"] is False # Custom not needed
    assert results["custom_board_width"] is None
    assert math.isclose(results["center_gap"], 0.1, abs_tol=config.FLOAT_TOLERANCE)
    assert len(results["floorboards"]) == 6 # 3 pairs
    assert results["board_counts"] == {"2x12": 2, "2x10": 2, "2x8": 2}

def test_floorboard_no_standard_only_custom():
    """Test when no standard boards selected, only custom allowed."""
    # Target span = 64. No standard boards.
    # Should place one custom board of width = 64 - 0.25 = 63.75?
    # Let's check the logic - it places pairs first. No pairs.
    # Remaining span = 64. Custom needed. Width = 64 - 0.25 = 63.75
    results = floorboard_logic.calculate_floorboard_layout(
        skid_layout_data=MOCK_SKID_OK_MULTI,
        product_length=DEFAULT_PROD_LEN,
        clearance_side=DEFAULT_CLR_SIDE,
        available_nominal_sizes=[], # NO standard boards
        allow_custom_narrow_board=True # Allow custom
    )
    assert results["status"] == "OK"
    assert results["narrow_board_used"] is True
    assert math.isclose(results["custom_board_width"], 63.75, abs_tol=config.FLOAT_TOLERANCE)
    assert math.isclose(results["center_gap"], 0.25, abs_tol=config.FLOAT_TOLERANCE)
    assert len(results["floorboards"]) == 1
    assert results["board_counts"] == {"Custom": 1}

def test_floorboard_error_no_boards_allowed():
    """Test error when no standard selected AND custom not allowed."""
    results = floorboard_logic.calculate_floorboard_layout(
        skid_layout_data=MOCK_SKID_OK_MULTI,
        product_length=DEFAULT_PROD_LEN,
        clearance_side=DEFAULT_CLR_SIDE,
        available_nominal_sizes=[], # NO standard boards
        allow_custom_narrow_board=False # NO custom
    )
    assert results["status"] == "ERROR"
    assert "No standard lumber selected AND custom board not allowed" in results["message"]

# Add tests for single skid base, different combinations of available lumber.

