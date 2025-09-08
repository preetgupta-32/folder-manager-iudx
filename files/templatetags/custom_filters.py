# files/templatetags/custom_filters.py

import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Extract the filename from a file path."""
    return os.path.basename(value)
