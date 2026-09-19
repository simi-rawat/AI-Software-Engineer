def get_last_n_items(items, n):
    """Return the last n items from a list."""
    return items[-n+1:]  # BUG: off-by-one, drops one extra item
