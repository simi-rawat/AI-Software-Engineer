def is_valid_age(age):
    """Check if age is a valid adult age (18 to 120 inclusive)."""
    return age > 18 and age <= 120  # BUG: should be >=, excludes exactly 18
