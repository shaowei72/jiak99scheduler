"""Custom template filters for restaurant schedule display."""
from django import template
from datetime import time, datetime

register = template.Library()


@register.filter
def time_to_percent(time_value):
    """
    Convert time to percentage position on timeline (10am = 0%, 9:30pm = 100%).

    Args:
        time_value: datetime.time object

    Returns:
        Percentage as float (0-100)
    """
    if not time_value:
        return 0

    # Operating hours: 10:00 AM - 9:30 PM = 11.5 hours = 690 minutes
    start_minutes = 10 * 60  # 10:00 AM in minutes
    total_minutes = 11.5 * 60  # 690 minutes total

    # Convert time to minutes since midnight
    time_minutes = time_value.hour * 60 + time_value.minute

    # Calculate minutes since start of operating hours
    minutes_since_start = time_minutes - start_minutes

    # Convert to percentage
    if minutes_since_start < 0:
        return 0
    if minutes_since_start > total_minutes:
        return 100

    percentage = (minutes_since_start / total_minutes) * 100
    return round(percentage, 2)


@register.filter
def mult(value, arg):
    """
    Multiply the value by the argument.

    Args:
        value: Number to multiply
        arg: Multiplier

    Returns:
        Product of value * arg
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
