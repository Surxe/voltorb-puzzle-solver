class Contradiction(ValueError):
    """No board can satisfy the counters and revealed cells, e.g. a counter or flip result was mistyped"""
