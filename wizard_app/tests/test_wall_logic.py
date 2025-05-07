# tests/test_wall_logic.py
"""
Unit tests for the wall_logic module (Python Logic Version).
Uses pytest. Includes tests for splicing and intermediate cleats.
"""
import pytest
import math
# Use absolute import based on expected structure
from wizard_app import wall_logic
from wizard_app import config

# Define common inputs
CRATE_W = 60.0
CRATE_L = 100.0
PANEL_H = 72.0
PANEL_T = 0.75
CLEAT_T = 0.75
CLEAT_W = 3.5

def test_wall_panel_no_splice():
    """Test a standard panel that doesn't require splicing."""
    results = wall_logic.calculate_wall_panels(
        crate_overall_width=40.0, # < 48
        crate_overall_length=80.0, # < 96 (for side panel height)
        panel_height=80.0, # < 96
        panel_thickness=PANEL_T,
        wall_cleat_thickness=CLEAT_T,
        wall_cleat_width=CLEAT_W
    )
    assert results["status"] == "OK"
    # Side Panel (W=80, H=80) -> Needs intermediate H and V
    side_panel = results["side_panels"][0]
    assert len(side_panel["plywood_pieces"]) == 1
    assert len(side_panel["cleats"]) == 6 # 4 edge + 1 intermediate H + 1 intermediate V
    assert any(c["type"] == "intermediate_horizontal" for c in side_panel["cleats"])
    assert any(c["type"] == "intermediate_vertical" for c in side_panel["cleats"])

    # End Panel (W=40, H=80) -> Needs intermediate H only
    end_panel = results["end_panels"][0]
    assert len(end_panel["plywood_pieces"]) == 1
    assert len(end_panel["cleats"]) == 5 # 4 edge + 1 intermediate H
    assert any(c["type"] == "intermediate_horizontal" for c in end_panel["cleats"])
    assert not any(c["type"] == "intermediate_vertical" for c in end_panel["cleats"])


def test_wall_panel_vertical_splice():
    """Test a panel requiring vertical splicing."""
    results = wall_logic.calculate_wall_panels(
        crate_overall_width=60.0, # > 48 (End panel needs splice)
        crate_overall_length=80.0, # < 96
        panel_height=72.0, # < 96
        panel_thickness=PANEL_T,
        wall_cleat_thickness=CLEAT_T,
        wall_cleat_width=CLEAT_W
    )
    assert results["status"] == "OK"
    # Side Panel (W=80, H=72) -> Needs intermediate V
    side_panel = results["side_panels"][0]
    assert len(side_panel["plywood_pieces"]) == 1
    assert len(side_panel["cleats"]) == 5 # 4 edge + 1 intermediate V
    assert any(c["type"] == "intermediate_vertical" for c in side_panel["cleats"])

    # End Panel (W=60, H=72) -> Needs vertical splice + intermediate H
    end_panel = results["end_panels"][0]
    assert len(end_panel["plywood_pieces"]) == 2
    assert any(c["type"] == "splice_vertical" for c in end_panel["cleats"])
    assert any(c["type"] == "intermediate_horizontal" for c in end_panel["cleats"])
    # Check if intermediate vertical was skipped due to splice
    assert not any(c["type"] == "intermediate_vertical" for c in end_panel["cleats"])
    # Total cleats = 4 edge + 1 splice_v + 1 intermediate_h = 6
    assert len(end_panel["cleats"]) == 6


def test_wall_panel_horizontal_splice():
    """Test a panel requiring horizontal splicing."""
    results = wall_logic.calculate_wall_panels(
        crate_overall_width=40.0, # < 48
        crate_overall_length=80.0, # < 96
        panel_height=100.0, # > 96 (Both panels need splice)
        panel_thickness=PANEL_T,
        wall_cleat_thickness=CLEAT_T,
        wall_cleat_width=CLEAT_W
    )
    assert results["status"] == "OK"
    # Side Panel (W=80, H=100) -> Needs H splice + intermediate V
    side_panel = results["side_panels"][0]
    assert len(side_panel["plywood_pieces"]) == 2
    assert any(c["type"] == "splice_horizontal" for c in side_panel["cleats"])
    assert any(c["type"] == "intermediate_vertical" for c in side_panel["cleats"])
    assert not any(c["type"] == "intermediate_horizontal" for c in side_panel["cleats"])
    assert len(side_panel["cleats"]) == 6 # 4 edge + 1 splice_h + 1 intermediate_v

    # End Panel (W=40, H=100) -> Needs H splice only
    end_panel = results["end_panels"][0]
    assert len(end_panel["plywood_pieces"]) == 2
    assert any(c["type"] == "splice_horizontal" for c in end_panel["cleats"])
    assert not any(c["type"] == "intermediate_horizontal" for c in end_panel["cleats"])
    assert not any(c["type"] == "intermediate_vertical" for c in end_panel["cleats"])
    assert len(end_panel["cleats"]) == 5 # 4 edge + 1 splice_h


def test_wall_panel_both_splices():
    """Test a panel requiring both vertical and horizontal splicing."""
    results = wall_logic.calculate_wall_panels(
        crate_overall_width=60.0, # > 48
        crate_overall_length=100.0, # > 96
        panel_height=110.0, # > 96
        panel_thickness=PANEL_T,
        wall_cleat_thickness=CLEAT_T,
        wall_cleat_width=CLEAT_W
    )
    assert results["status"] == "OK"
    # Side Panel (W=100, H=110) -> Needs V+H splice
    side_panel = results["side_panels"][0]
    assert len(side_panel["plywood_pieces"]) == 4
    assert any(c["type"] == "splice_vertical" for c in side_panel["cleats"])
    assert any(c["type"] == "splice_horizontal" for c in side_panel["cleats"])
    assert not any(c["type"].startswith("intermediate") for c in side_panel["cleats"]) # Intermediates should be skipped
    # 4 edge + 1 splice_v + 2 splice_h (split by splice_v) = 7
    assert len(side_panel["cleats"]) == 7

    # End Panel (W=60, H=110) -> Needs V+H splice
    end_panel = results["end_panels"][0]
    assert len(end_panel["plywood_pieces"]) == 4
    assert any(c["type"] == "splice_vertical" for c in end_panel["cleats"])
    assert any(c["type"] == "splice_horizontal" for c in end_panel["cleats"])
    assert not any(c["type"].startswith("intermediate") for c in end_panel["cleats"])
    assert len(end_panel["cleats"]) == 7

# Add tests for edge cases near splice thresholds

