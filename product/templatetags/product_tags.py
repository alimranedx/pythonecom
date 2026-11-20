import re
import html
from html.parser import HTMLParser
from django import template
from django.utils.html import escape, linebreaks, strip_tags
from django.utils.safestring import mark_safe
from django.utils.text import Truncator

register = template.Library()

# Tags that pose security risks; their tags AND contents are removed completely
DANGEROUS_TAGS = [
    'script', 'style', 'iframe', 'object', 'embed', 'applet',
    'noscript', 'meta', 'link', 'base', 'form', 'input', 'button',
    'textarea', 'select', 'svg', 'math', 'template', 'frame', 'frameset'
]

DANGEROUS_BLOCK_RE = re.compile(
    r'<(?:' + '|'.join(DANGEROUS_TAGS) + r')\b[^>]*>.*?</(?:' + '|'.join(DANGEROUS_TAGS) + r')>',
    re.IGNORECASE | re.DOTALL
)
DANGEROUS_TAG_RE = re.compile(
    r'<(?:' + '|'.join(DANGEROUS_TAGS) + r')\b[^>]*\/?>',
    re.IGNORECASE
)

# Standard formatting tags permitted in rich product descriptions
ALLOWED_TAGS = [
    'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'strong', 'b', 'em', 'i', 'u', 's', 'strike',
    'br', 'hr', 'span', 'div', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',
    'blockquote', 'pre', 'code', 'a', 'img', 'sub', 'sup', 'caption'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'title'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    'table': ['class', 'border', 'cellpadding', 'cellspacing', 'style'],
    'th': ['colspan', 'rowspan', 'scope', 'style', 'class'],
    'td': ['colspan', 'rowspan', 'style', 'class'],
    'span': ['class', 'style'],
    'div': ['class', 'style'],
    'p': ['class', 'style'],
    'h1': ['class', 'style'],
    'h2': ['class', 'style'],
    'h3': ['class', 'style'],
    'h4': ['class', 'style'],
    'h5': ['class', 'style'],
    'h6': ['class', 'style'],
    'ul': ['class', 'style'],
    'ol': ['class', 'style', 'type', 'start'],
    'li': ['class', 'style'],
    'blockquote': ['class', 'style'],
    'pre': ['class'],
    'code': ['class'],
    'caption': ['class', 'style'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'tel']

ALLOWED_CSS_PROPERTIES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'font-family', 'text-align', 'text-decoration', 'line-height',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border', 'border-radius', 'border-collapse', 'width', 'max-width', 'height'
]

BLOCK_TAGS_PATTERN = re.compile(
    r'<(?:p|br|div|h[1-6]|ul|ol|li|table|tr|blockquote)\b',
    re.IGNORECASE
)

# Initialize Bleach with CSS sanitizer if available
try:
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    _css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
    _bleach_available = True
except Exception:
    _css_sanitizer = None
    _bleach_available = False


class _FallbackHTMLSanitizer(HTMLParser):
    """Pure Python fallback HTML sanitizer adhering to the same strict whitelist."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag_lower = tag.lower()
        if tag_lower in DANGEROUS_TAGS or tag_lower not in ALLOWED_TAGS:
            return

        cleaned_attrs = []
        allowed_for_tag = set(ALLOWED_ATTRIBUTES.get(tag_lower, []) + ALLOWED_ATTRIBUTES.get('*', []))

        for attr, val in attrs:
            attr_lower = attr.lower()
            if attr_lower.startswith('on') or attr_lower not in allowed_for_tag:
                continue

            val_str = str(val).strip()
            # Protocol check for URLs
            if attr_lower in ('href', 'src'):
                val_lower = val_str.lower().replace('\x00', '')
                colon_idx = val_lower.find(':')
                if colon_idx != -1:
                    scheme = val_lower[:colon_idx].strip()
                    if scheme not in ALLOWED_PROTOCOLS:
                        continue
                if 'javascript:' in val_lower or 'vbscript:' in val_lower or 'data:' in val_lower:
                    continue

            # Safe style check
            if attr_lower == 'style':
                val_lower = val_str.lower()
                if any(x in val_lower for x in ['javascript', 'expression', 'behavior', 'url(', '@import', '-moz-binding']):
                    continue

            cleaned_attrs.append(f'{attr_lower}="{escape(val_str)}"')

        attr_str = (' ' + ' '.join(cleaned_attrs)) if cleaned_attrs else ''
        if tag_lower in ('br', 'hr', 'img'):
            self.output.append(f'<{tag_lower}{attr_str} />')
        else:
            self.output.append(f'<{tag_lower}{attr_str}>')
            self.tag_stack.append(tag_lower)

    def handle_endtag(self, tag):
        tag_lower = tag.lower()
        if tag_lower in self.tag_stack:
            while self.tag_stack:
                popped = self.tag_stack.pop()
                self.output.append(f'</{popped}>')
                if popped == tag_lower:
                    break

    def handle_data(self, data):
        self.output.append(escape(data))

    def get_cleaned_html(self):
        while self.tag_stack:
            self.output.append(f'</{self.tag_stack.pop()}>')
        return ''.join(self.output)


def sanitize_html(content: str) -> str:
    """
    Sanitizes HTML content by removing dangerous tags, attributes, and styles,
    allowing only safe whitelisted tags and formatting.
    """
    if not content:
        return ''

    # Step 1: Aggressively strip dangerous blocks (<script>...</script>, <style>...</style>, etc.)
    cleaned = DANGEROUS_BLOCK_RE.sub('', content)
    cleaned = DANGEROUS_TAG_RE.sub('', cleaned)

    # Step 2: Whitelist sanitization
    if _bleach_available:
        sanitized = bleach.clean(
            cleaned,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            css_sanitizer=_css_sanitizer,
            strip=True,
            strip_comments=True
        )
    else:
        parser = _FallbackHTMLSanitizer()
        parser.feed(cleaned)
        sanitized = parser.get_cleaned_html()

    # Step 3: Ensure external links have rel="noopener noreferrer"
    def fix_link_rel(match):
        tag = match.group(0)
        if 'target="_blank"' in tag or "target='_blank'" in tag:
            if 'rel=' not in tag:
                return tag[:-1] + ' rel="noopener noreferrer">'
        return tag

    sanitized = re.sub(r'<a\b[^>]*>', fix_link_rel, sanitized, flags=re.IGNORECASE)

    # Step 4: If HTML has no block elements, preserve newlines as line breaks
    if not BLOCK_TAGS_PATTERN.search(sanitized) and '\n' in sanitized:
        sanitized = sanitized.replace('\r\n', '\n').replace('\n', '<br />\n')

    return sanitized


@register.filter(name='render_safe_html')
def render_safe_html(value):
    """
    Template filter: {{ product.description|render_safe_html }}
    Renders rich HTML formatting safely:
    - Allows safe formatting tags (p, h1-h6, ul, ol, li, strong, b, em, i, br, hr, span, div, table, etc.)
    - Aggressively strips dangerous tags/attributes (script, style, iframe, object, onerror, javascript:, etc.)
    - Gracefully handles both raw HTML tags and entity-escaped tags (&lt;p&gt;...&lt;/p&gt;)
    - If input is plain text (no HTML tags), converts newlines to clean linebreaks/paragraphs.
    """
    if not value:
        return ''

    text = str(value).strip()
    if not text:
        return ''

    # If text contains HTML entity codes (&lt; and &gt;), decode them first
    # so rich HTML seeded or escaped from forms is parsed properly
    unescaped_text = html.unescape(text) if ('&lt;' in text and '&gt;' in text) else text

    # Check if text contains HTML tags
    has_html_tags = bool(re.search(r'<[a-zA-Z\/][^>]*>', unescaped_text))
    if not has_html_tags:
        # Plain text: escape raw characters and format newlines
        return mark_safe(linebreaks(escape(unescaped_text)))

    # HTML content: sanitize and mark safe
    clean_html = sanitize_html(unescaped_text)
    return mark_safe(clean_html)


@register.filter(name='clean_plain_summary')
def clean_plain_summary(value, num_words=45):
    """
    Template filter: {{ product.description|clean_plain_summary:45 }}
    Strips all HTML tags and collapses whitespace BEFORE truncating to words,
    guaranteeing that summaries never leak raw or broken tags.
    """
    if not value:
        return ''

    text = str(value).strip()
    if not text:
        return ''

    # Decode entities first so tags are recognized for stripping
    if '&lt;' in text and '&gt;' in text:
        text = html.unescape(text)

    # Pre-strip dangerous blocks
    text = DANGEROUS_BLOCK_RE.sub('', text)
    text = DANGEROUS_TAG_RE.sub('', text)

    # Strip all remaining HTML tags
    plain = strip_tags(text)

    # Unescape HTML entities (e.g. &amp; -> &, &nbsp; -> ' ')
    plain = html.unescape(plain)

    # Normalize whitespace (replace multiple spaces/newlines with single space)
    plain = ' '.join(plain.split())

    # Truncate words if requested
    try:
        words_limit = int(num_words)
    except (ValueError, TypeError):
        words_limit = 45

    if words_limit > 0:
        return Truncator(plain).words(words_limit, truncate='...')
    return plain


# Convenient aliases
register.filter('safe_html', render_safe_html)
register.filter('plain_summary', clean_plain_summary)
