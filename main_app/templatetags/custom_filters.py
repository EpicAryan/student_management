from django import template

register = template.Library()

@register.filter
def ordinal(value):
    """
    Converts an integer to its ordinal representation.
    Example: 1 -> '1st', 2 -> '2nd', 3 -> '3rd', 4 -> '4th'
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    # Handle special cases for 11th, 12th, 13th
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        # Handle 1st, 2nd, 3rd, and everything else
        suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
        suffix = suffixes.get(value % 10, 'th')
    
    return f"{value}{suffix}"
