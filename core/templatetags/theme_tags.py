from django import template
from django.template.loader import get_template, TemplateDoesNotExist

register = template.Library()


@register.filter(name='template_exists')
def template_exists(template_name):
    """
    Checks whether a template with the given relative path exists in the configured template loaders.
    Usage:
        {% if CURRENT_THEME_DATA.template_mapping.header|template_exists %}
    """
    if not template_name:
        return False
    try:
        get_template(template_name)
        return True
    except (TemplateDoesNotExist, Exception):
        return False


@register.simple_tag(takes_context=True)
def render_theme_header(context):
    """
    Renders the theme's custom header if defined in template_mapping and present on disk,
    otherwise renders the standard 'includes/header.html'.
    """
    theme_data = context.get('CURRENT_THEME_DATA') or {}
    template_mapping = theme_data.get('template_mapping') or {}
    custom_header = template_mapping.get('header')

    if custom_header:
        try:
            tmpl = get_template(custom_header)
            return tmpl.render(context.flatten())
        except TemplateDoesNotExist:
            pass

    default_tmpl = get_template('includes/header.html')
    return default_tmpl.render(context.flatten())


@register.simple_tag(takes_context=True)
def render_theme_footer(context):
    """
    Renders the theme's custom footer if defined in template_mapping and present on disk,
    otherwise renders the standard 'includes/footer.html'.
    """
    theme_data = context.get('CURRENT_THEME_DATA') or {}
    template_mapping = theme_data.get('template_mapping') or {}
    custom_footer = template_mapping.get('footer')

    if custom_footer:
        try:
            tmpl = get_template(custom_footer)
            return tmpl.render(context.flatten())
        except TemplateDoesNotExist:
            pass

    default_tmpl = get_template('includes/footer.html')
    return default_tmpl.render(context.flatten())
