from django import template
from core.translations import get_translation, to_bn_number

register = template.Library()


@register.simple_tag(takes_context=True)
def tr(context, text_or_key):
    """
    Template tag: {% tr "Add to Cart" %} or {% tr "search_placeholder" %}
    Resolves the translation based on request.CURRENT_LANGUAGE in context.
    """
    lang = context.get('CURRENT_LANGUAGE', 'en')
    return get_translation(text_or_key, lang)


@register.filter(name='tr')
def tr_filter(text_or_key, lang='en'):
    """
    Template filter: {{ "Add to Cart"|tr }}
    """
    return get_translation(text_or_key, lang)


@register.filter(name='bn_num')
def bn_num_filter(number_val, is_bangla=True):
    """
    Template filter: {{ value|bn_num }}
    Converts numbers to Bengali numerals if is_bangla is True.
    """
    if is_bangla:
        return to_bn_number(number_val)
    return number_val
