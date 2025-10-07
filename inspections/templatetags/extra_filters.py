from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Returns dictionary[key] if it exists, otherwise an empty list.
    Used to access dict items in templates.
    """
    return dictionary.get(key, [])
