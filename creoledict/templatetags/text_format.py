import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def italicize_asterisks(text):
    """
    Converts **word** into <em>word</em>.
    """
    if not text:
        return ''
    # Replace *something* with <em>something</em>
    formatted = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return mark_safe(formatted)
