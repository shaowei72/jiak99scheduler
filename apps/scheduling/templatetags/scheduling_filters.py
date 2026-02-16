from django import template

register = template.Library()


@register.filter(name='display_name')
def display_name(user):
    """
    Display user's full name if available, otherwise username.
    
    Args:
        user: Django User object
    
    Returns:
        str: Full name (first + last) or username if names are empty
    """
    if not user:
        return ''
    
    full_name = user.get_full_name()
    if full_name and full_name.strip():
        return full_name
    
    return user.username
