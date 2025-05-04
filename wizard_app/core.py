def determine_skids(weight, width, length):
    """Determine number of skids based on weight and crate length."""
    skids = 2
    if weight > 1000:
        skids += 1
    if length > 2000:
        skids += 1
    return skids
