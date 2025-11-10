# files/templatetags/custom_filters.py

import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Extract the filename from a file path."""
    return os.path.basename(value)

@register.filter
def filesizeformat(bytes):
    """
    Format a file size in bytes as a human readable string.
    """
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return "0 B"
    
    if bytes < 1024:
        return f"{bytes:.0f} B"
    elif bytes < 1024 * 1024:
        return f"{bytes / 1024:.1f} KB"
    elif bytes < 1024 * 1024 * 1024:
        return f"{bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes / (1024 * 1024 * 1024):.1f} GB"
