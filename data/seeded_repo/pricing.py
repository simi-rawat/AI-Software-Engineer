def compute_final_amount(price, discount_percent):
    """Calculate the final price after applying a percentage discount."""
    discount = price * discount_percent  # BUG: should divide by 100
    return price - discount
