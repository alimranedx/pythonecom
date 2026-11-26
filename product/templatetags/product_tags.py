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


@register.filter(name='emi_monthly')
def emi_monthly(price, months=12):
    """
    Calculates monthly payment under 0% EMI financing.
    e.g. {{ product.effective_price|emi_monthly:12 }} -> '3,450'
    """
    try:
        from decimal import Decimal
        val = Decimal(str(price))
        m = int(months)
        if m <= 0:
            m = 12
        monthly = int(round(val / Decimal(m)))
        return f"{monthly:,}"
    except Exception:
        return '0'


@register.filter(name='tech_specs_summary')
def tech_specs_summary(product):
    """
    Extracts 3-4 key technical specification tags from a product's name,
    short description, or category for tech product cards and listings.
    """
    if not product:
        return []
    
    name = getattr(product, 'name', '') or ''
    short_desc = getattr(product, 'short_description', '') or ''
    desc = getattr(product, 'description', '') or ''
    full_text = f"{name} {short_desc} {desc}"
    cat_slug = ''
    if getattr(product, 'category', None):
        cat_slug = getattr(product.category, 'slug', '').lower()
        cat_name = getattr(product.category, 'name', '').lower()
    else:
        cat_name = ''

    specs = []

    # 1. Detect Processor / Chipset
    proc_patterns = [
        (r'\b(Apple\s+M[1-4](?:\s+Pro|\s+Max|\s+Ultra)?\s+Chip)\b', r'\1'),
        (r'\b(M[1-4]\s+Chip)\b', r'\1'),
        (r'\b(Intel\s+Core\s+i[3579](?:-\w+)?)\b', r'\1'),
        (r'\b(Core\s+i[3579])\b', r'Intel \1'),
        (r'\b(AMD\s+Ryzen\s+[579](?:\s+\w+)?)\b', r'\1'),
        (r'\b(Snapdragon\s+\w+(?:\s+Gen\s+\d)?)\b', r'\1'),
        (r'\b(A1[6-8]\s+Pro|A1[5-8]\s+Bionic)\b', r'Apple \1'),
        (r'\b(Dimensity\s+\d+)\b', r'MediaTek \1'),
        (r'\b(Exynos\s+\d+)\b', r'Samsung \1'),
    ]
    for pattern, repl in proc_patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            specs.append(re.sub(pattern, repl, m.group(0), flags=re.IGNORECASE))
            break

    # 2. Detect Display / Resolution
    disp_patterns = [
        (r'\b(Ultra\s+Retina\s+XDR(?:\s+OLED)?)\b', r'\1'),
        (r'\b(Retina\s+Display)\b', r'\1'),
        (r'\b(\d{1,2}(?:\.\d)?["\']\s+(?:4K|QHD\+|OLED|IPS|Retina))\b', r'\1'),
        (r'\b(4K\s+UHD|4K\s+IPS|OLED\s+Display|120Hz\s+ProMotion|165Hz|240Hz|IPS\s+Black)\b', r'\1'),
        (r'\b(13\.3"|14\.2"|15\.6"|16\.2"|27"|32"|34")\b', r'\1 Display'),
    ]
    for pattern, repl in disp_patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            specs.append(m.group(0))
            break

    # 3. Detect RAM / Memory
    ram_patterns = [
        r'\b(8GB|16GB|24GB|32GB|64GB)\s+(?:Unified\s+Memory|RAM|DDR5|LPDDR5X)\b',
        r'\b(\d{1,2}GB)\s+RAM\b',
    ]
    for pattern in ram_patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            specs.append(m.group(0))
            break

    # 4. Detect Storage
    storage_patterns = [
        r'\b(128GB|256GB|512GB|1TB|2TB|4TB)\s+(?:NVMe|SSD|PCIe|UFS\s*4\.0)\b',
        r'\b(256GB|512GB|1TB|2TB)\s+(?:Storage|Internal)\b',
        r'\b(1TB|2TB)\s+SSD\b',
        r'\b(256GB|512GB|1TB)\b',
    ]
    for pattern in storage_patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            val = m.group(0)
            if not any(val.lower() in s.lower() for s in specs):
                specs.append(val if 'SSD' in val or 'NVMe' in val or 'GB' in val else f"{val} SSD")
                break

    # 5. Detect Connectivity / Key Hardware Feature
    extra_patterns = [
        r'\b(WiFi\s+7|Wi-Fi\s+7|WiFi\s+6E|Wi-Fi\s+6E|5G\s+Cellular)\b',
        r'\b(Thunderbolt\s+4|USB-C\s+90W|ANC|Active\s+Noise\s+Canceling)\b',
        r'\b(IP65|IP68\s+Waterproof|Hi-Res\s+Audio|Spatial\s+Audio)\b',
        r'\b(GaNFast|120W\s+Fast\s+Charging|MagSafe)\b',
    ]
    for pattern in extra_patterns:
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m and len(specs) < 4:
            specs.append(m.group(0))
            break

    # Fallback specs if product text is concise
    if len(specs) < 3:
        if 'laptop' in cat_slug or 'laptop' in cat_name:
            fallbacks = ['Intel / Apple Silicon', '16GB RAM', '512GB SSD', 'FHD / Retina Display']
        elif 'phone' in cat_slug or 'smartphone' in cat_name:
            fallbacks = ['Flagship 5G Processor', '120Hz AMOLED / OLED', 'Triple AI Camera', 'Super Fast Charge']
        elif 'monitor' in cat_slug or 'display' in cat_name:
            fallbacks = ['4K Ultra HD IPS', '100% sRGB / DCI-P3', 'USB-C 90W Hub', 'Eye Comfort Certified']
        elif 'router' in cat_slug or 'network' in cat_name:
            fallbacks = ['Wi-Fi 7 / 6E Quad-Band', '2.5G Multi-Gig WAN', 'AiMesh / Mesh Ready', 'Low-Latency Gaming']
        elif 'audio' in cat_slug or 'headphone' in cat_name or 'bud' in cat_name:
            fallbacks = ['Hybrid Active Noise Canceling', 'Hi-Res LDAC Audio', '30-Hour Battery Life', 'Bluetooth 5.3']
        elif 'storage' in cat_slug or 'ssd' in cat_name:
            fallbacks = ['USB 3.2 Gen 2x2', 'Up to 2000MB/s', 'Hardware Encryption', 'Shock & Drop Resistant']
        else:
            fallbacks = ['High-Speed Processing', 'Official BD Warranty', 'Ultra-Durable Build', 'Energy Efficient']

        for fb in fallbacks:
            if fb not in specs and len(specs) < 4:
                specs.append(fb)

    return specs[:4]


@register.filter(name='tech_specs_table')
def tech_specs_table(product):
    """
    Returns structured technical specification table rows
    (Processor, Memory, Storage, Display, Graphics, Ports, Battery, Operating System, Warranty).
    """
    if not product:
        return []

    name = getattr(product, 'name', '') or ''
    desc = getattr(product, 'description', '') or ''
    short_desc = getattr(product, 'short_description', '') or ''
    full_text = f"{name} {short_desc} {desc}"
    cat_slug = ''
    brand_name = ''
    if getattr(product, 'category', None):
        cat_slug = getattr(product.category, 'slug', '').lower()
    if getattr(product, 'brand', None):
        brand_name = getattr(product.brand, 'name', '')

    # Helper match function
    def _find(pattern, default):
        m = re.search(pattern, full_text, re.IGNORECASE)
        return m.group(1) if m else default

    # 1. Processor
    if 'apple' in full_text.lower() and ('m4' in full_text.lower() or 'ipad' in full_text.lower() or 'macbook' in full_text.lower()):
        processor = 'Apple M4 Chip (10-core CPU, 10-core GPU, 16-core Neural Engine)'
    elif 'apple' in full_text.lower():
        processor = 'Apple Silicon / A18 Pro Bionic Chip with 6-core Neural Engine'
    elif 'intel' in full_text.lower() or 'core' in full_text.lower():
        processor = _find(r'(Intel\s+Core\s+(?:Ultra\s+)?[i\d\w-]+)', 'Intel Core i7-14700HX (20 Cores, 28 Threads, up to 5.5GHz)')
    elif 'ryzen' in full_text.lower() or 'amd' in full_text.lower():
        processor = _find(r'(AMD\s+Ryzen\s+\d(?:\s+\w+)?)', 'AMD Ryzen 7 8845HS (8 Cores, 16 Threads, up to 5.1GHz)')
    elif 'router' in full_text.lower() or 'network' in cat_slug:
        processor = '2.6GHz Quad-Band 64-bit High-Throughput Network Processor'
    elif 'monitor' in full_text.lower():
        processor = 'Integrated Color Calibration & Pixel Response Engine'
    elif 'audio' in cat_slug or 'headphone' in full_text.lower():
        processor = 'Sony V1 Integrated Noise Canceling & QN1 Audio Processor'
    elif 'ssd' in cat_slug or 'storage' in cat_slug:
        processor = 'Samsung In-House PCIe Gen4 NVMe High-Speed Controller'
    else:
        processor = f"{brand_name or 'Next-Gen'} Octa-Core High-Efficiency Processor"

    # 2. Memory / RAM
    ram = _find(r'(\d{1,2}GB\s+(?:Unified\s+Memory|DDR5|LPDDR5X|RAM))', None)
    if not ram:
        if 'apple' in full_text.lower():
            ram = '16GB Unified Memory (Unified Fast Architecture)'
        elif 'router' in full_text.lower():
            ram = '2GB DDR4 High-Speed Buffer RAM'
        elif 'monitor' in full_text.lower():
            ram = 'Auto-Detect LUT Internal Buffer'
        elif 'audio' in cat_slug or 'headphone' in full_text.lower():
            ram = 'Ultra-low latency audio processing buffer'
        elif 'ssd' in cat_slug or 'storage' in cat_slug:
            ram = '2GB LPDDR4 DRAM Cache'
        else:
            ram = '16GB DDR5 5600MHz High-Speed Memory'

    # 3. Storage
    storage = _find(r'(\d{1,3}(?:GB|TB)\s+(?:NVMe|SSD|PCIe|UFS|Storage)?)', None)
    if not storage:
        if 'router' in full_text.lower():
            storage = '256MB Flash ROM Storage'
        elif 'audio' in cat_slug:
            storage = 'Internal Firmware Storage'
        elif 'monitor' in cat_slug:
            storage = 'EDID Profile Storage'
        elif 'ssd' in full_text.lower():
            storage = '2TB PCIe Gen 4.0 NVMe High-Speed Storage'
        else:
            storage = '512GB PCIe 4.0 NVMe M.2 Solid State Drive'

    # 4. Display
    display = _find(r'(\d{1,2}(?:\.\d)?["\']\s+(?:[\w\s\+\/-]+Panel|OLED|Retina|IPS|Display))', None)
    if not display:
        if 'monitor' in full_text.lower():
            display = '27" 4K UHD (3840 x 2160) IPS Black 60Hz, 98% DCI-P3'
        elif 'macbook' in full_text.lower() or 'ipad' in full_text.lower():
            display = '13.0" Tandem OLED Ultra Retina XDR (2752x2064, 120Hz ProMotion)'
        elif 'laptop' in cat_slug:
            display = '16.0" QHD+ (2560x1600) 165Hz IPS 100% sRGB Anti-Glare'
        elif 'phone' in cat_slug:
            display = '6.7" Dynamic AMOLED 2X, 120Hz Adaptive, 2600 nits Peak'
        else:
            display = 'LED Status Indicator & OLED Info Panel'

    # 5. Graphics
    if 'apple' in full_text.lower():
        graphics = '10-core Apple GPU with Hardware-Accelerated Ray Tracing'
    elif 'rtx' in full_text.lower():
        graphics = _find(r'(NVIDIA\s+GeForce\s+RTX\s+\d{4}(?:\s+Ti)?)', 'NVIDIA GeForce RTX 4060 8GB GDDR6')
    elif 'router' in full_text.lower() or 'storage' in cat_slug:
        graphics = 'Not Applicable (Dedicated Hardware Network Processing Unit)'
    elif 'monitor' in full_text.lower():
        graphics = 'Integrated Display Controller with HDR10 & Auto KVM'
    elif 'audio' in cat_slug:
        graphics = 'Dedicated 32-bit Hi-Res Digital Audio Converter (DAC)'
    else:
        graphics = 'Intel Iris Xe / AMD Radeon Graphics 780M'

    # 6. Ports & Connectivity
    if 'router' in full_text.lower():
        ports = '1x 10Gbps WAN/LAN, 1x 2.5Gbps WAN/LAN, 4x 1Gbps LAN, 1x USB 3.2 Gen 1'
    elif 'monitor' in full_text.lower():
        ports = '1x USB-C 90W PD, 1x DisplayPort 1.4, 1x HDMI 2.0, 4x USB 3.2, 1x RJ45 LAN'
    elif 'apple' in full_text.lower():
        ports = 'Thunderbolt 4 / USB-C 40Gbps, Wi-Fi 6E (802.11ax), Bluetooth 5.3'
    elif 'ssd' in cat_slug:
        ports = 'USB 3.2 Gen 2x2 Type-C (Up to 20Gbps Transfer Speed)'
    elif 'audio' in cat_slug:
        ports = 'Bluetooth 5.3 Multipoint, 3.5mm Stereo Jack, USB-C Fast Charging'
    else:
        ports = '2x Thunderbolt 4, 2x USB 3.2 Gen 2, 1x HDMI 2.1, 1x 3.5mm Audio Jack'

    # 7. Battery & Power
    if 'monitor' in full_text.lower():
        battery = 'Built-in 100-240V AC Power Supply (Energy Star Certified)'
    elif 'router' in full_text.lower():
        battery = '12V / 5A DC External Power Adapter'
    elif 'ssd' in cat_slug:
        battery = 'Bus-Powered via USB-C (Low-Power Energy Consumption)'
    elif 'audio' in cat_slug:
        battery = 'Up to 30 Hours Playback (3 min charge = 3 hours playback)'
    elif 'apple' in full_text.lower():
        battery = '38.99 Wh Lithium-Polymer (Up to 10 hours web/video), 20W Fast Charge'
    elif 'phone' in cat_slug:
        battery = '5,000 mAh Li-ion with 45W Super Fast Charging 2.0'
    else:
        battery = '80 Wh 4-Cell Li-ion, 140W USB-C GaN Rapid Fast Charger'

    # 8. Operating System
    if 'apple' in full_text.lower() and 'ipad' in full_text.lower():
        os = 'iPadOS 17 (Free Upgrade to iPadOS 18)'
    elif 'apple' in full_text.lower():
        os = 'macOS Sonoma (Free Upgrade to macOS Sequoia)'
    elif 'router' in full_text.lower():
        os = 'ASUSWRT / OpenWrt Linux Microkernel OS'
    elif 'monitor' in full_text.lower() or 'audio' in cat_slug or 'ssd' in cat_slug:
        os = 'Universal Plug & Play (Windows, macOS, iOS, Android, Linux)'
    elif 'phone' in cat_slug:
        os = 'Android 14 with One UI 6.1 (7 Years of OS Updates)'
    else:
        os = 'Windows 11 Home 64-bit Genuine (Pre-installed with Office Home)'

    # 9. Warranty
    warranty = 'Official Bangladesh Brand Warranty (Claimable at Authorized Service Centers)'

    return [
        {'name': 'Processor / Chipset', 'value': processor, 'icon': 'bi-cpu'},
        {'name': 'Memory (RAM)', 'value': ram, 'icon': 'bi-memory'},
        {'name': 'Storage Capacity', 'value': storage, 'icon': 'bi-hdd-network'},
        {'name': 'Display & Resolution', 'value': display, 'icon': 'bi-display'},
        {'name': 'Graphics (GPU)', 'value': graphics, 'icon': 'bi-gpu-card'},
        {'name': 'Ports & Connectivity', 'value': ports, 'icon': 'bi-plug'},
        {'name': 'Battery & Power', 'value': battery, 'icon': 'bi-battery-charging'},
        {'name': 'Operating System', 'value': os, 'icon': 'bi-motherboard'},
        {'name': 'Official Warranty', 'value': warranty, 'icon': 'bi-shield-check'},
    ]


@register.filter(name='beauty_volume')
def beauty_volume(product):
    """
    Extracts or formats beauty product volume / size indicator (e.g. '30ml', '50ml', '250ml', '50g').
    Falls back to product.unit or category name.
    """
    if not product:
        return '50ml'
    text_sources = [
        getattr(product, 'unit', '') or '',
        getattr(product, 'name', '') or '',
        getattr(product, 'short_description', '') or '',
    ]
    vol_re = re.compile(r'\b(\d+(?:\.\d+)?\s*(?:ml|mL|g|gm|fl\s*oz|oz|sheets?|pcs))\b', re.IGNORECASE)
    for text in text_sources:
        match = vol_re.search(text)
        if match:
            clean_val = match.group(1).replace(' ', '').lower()
            if 'ml' in clean_val:
                return clean_val.replace('ml', 'ml')
            return clean_val

    unit_val = getattr(product, 'unit', '').strip()
    if unit_val and unit_val.lower() not in ['1 pc', 'pc', 'piece']:
        return unit_val

    cat = getattr(product, 'category', None)
    if cat and cat.name:
        cat_lower = cat.name.lower()
        if 'serum' in cat_lower:
            return '30ml'
        elif 'cleanser' in cat_lower:
            return '150ml'
        elif 'toner' in cat_lower:
            return '250ml'
        elif 'moisturiz' in cat_lower or 'cream' in cat_lower:
            return '50ml'
        elif 'sunscreen' in cat_lower or 'sun' in cat_lower:
            return '50ml'
        elif 'fragrance' in cat_lower:
            return '100ml'
        elif 'lip' in cat_lower:
            return '10ml'
    return '50ml'


@register.filter(name='beauty_routine_step')
def beauty_routine_step(product):
    """
    Determines skincare routine step (1 Cleanse, 2 Tone, 3 Treat/Serum, 4 Moisturize, 5 Protect).
    """
    if not product:
        return {'step': 3, 'title': 'Step 3: Treat & Serum', 'short': 'Serum', 'icon': 'bi-droplet-half'}
    cat_name = getattr(getattr(product, 'category', None), 'name', '').lower()
    prod_name = getattr(product, 'name', '').lower()
    combined = f"{cat_name} {prod_name}"

    if any(k in combined for k in ['cleanse', 'cleanser', 'foaming', 'wash', 'micellar', 'cleansing oil']):
        return {'step': 1, 'title': 'Step 1: Cleanse', 'short': 'Cleanse', 'icon': 'bi-water'}
    elif any(k in combined for k in ['toner', 'essence', 'prep', 'pad', 'mist', 'aha/bha', 'relief calming toner']):
        return {'step': 2, 'title': 'Step 2: Tone & Prep', 'short': 'Tone', 'icon': 'bi-flower1'}
    elif any(k in combined for k in ['serum', 'ampoule', 'concentrate', 'booster', 'retinol', 'niacinamide', 'vitamin c']):
        return {'step': 3, 'title': 'Step 3: Treat & Serum', 'short': 'Serum', 'icon': 'bi-droplet-half'}
    elif any(k in combined for k in ['moisturiz', 'cream', 'barrier', 'lotion', 'balm', 'gel cream', 'cerapeptide']):
        return {'step': 4, 'title': 'Step 4: Moisturize & Lock', 'short': 'Moisturize', 'icon': 'bi-cloud'}
    elif any(k in combined for k in ['sunscreen', 'sun', 'spf', 'uv', 'shield', 'relief sun', 'lip', 'parfum', 'fragrance', 'powder', 'foundation']):
        return {'step': 5, 'title': 'Step 5: Protect & Glow', 'short': 'Protect', 'icon': 'bi-sun'}
    return {'step': 3, 'title': 'Step 3: Treat & Serum', 'short': 'Serum', 'icon': 'bi-droplet-half'}


@register.filter(name='beauty_skin_compatibility')
def beauty_skin_compatibility(product):
    """
    Returns skin compatibility recommendation badge text.
    """
    if not product:
        return 'All Skin Types • Sensitive Skin Tested'
    name = getattr(product, 'name', '').lower()
    desc = getattr(product, 'description', '').lower()
    combined = f"{name} {desc}"

    if 'sensitive' in combined or 'calm' in combined or 'soothing' in combined or 'heartleaf' in combined or 'cica' in combined:
        return 'Sensitive & Reactive Skin Tested • Non-Comedogenic'
    elif 'acne' in combined or 'salicylic' in combined or 'bha' in combined or 'pore' in combined or 'oil' in combined:
        return 'Oily, Blemish-Prone & Combination Skin'
    elif 'dry' in combined or 'hydrat' in combined or 'ceramide' in combined or 'barrier' in combined:
        return 'Dry, Dehydrated & Normal Skin'
    return 'All Skin Types • Dermatologist Formulated'


@register.filter(name='beauty_active_ingredients')
def beauty_active_ingredients(product):
    """
    Returns structured list of active ingredients for product detail tables.
    """
    if not product:
        name = ''
        desc = ''
    else:
        name = getattr(product, 'name', '').lower()
        desc = getattr(product, 'description', '').lower()
    combined = f"{name} {desc}"

    ingredients = []

    if 'niacinamide' in combined:
        ingredients.append({
            'name': 'Niacinamide (Vitamin B3) 10%',
            'role': 'Pore Refining & Tone Correction',
            'benefit': 'Visibly minimizes enlarged pores, evens skin tone, and regulates excess sebum.'
        })
    if 'hyaluronic' in combined or 'hydrat' in combined:
        ingredients.append({
            'name': 'Multi-Molecular Hyaluronic Acid',
            'role': 'Deep Hydration & Skin Plumping',
            'benefit': 'Penetrates multiple epidermal layers to deliver 48-hour continuous moisture.'
        })
    if 'ceramide' in combined or 'cerave' in combined or 'barrier' in combined or 'cerapeptide' in combined:
        ingredients.append({
            'name': 'Triple Essential Ceramides (1, 3, 6-II)',
            'role': 'Lipid Barrier Restoration',
            'benefit': 'Restores the natural protective barrier and locks in vital hydration against irritants.'
        })
    if 'heartleaf' in combined or 'centella' in combined or 'cica' in combined or 'anua' in combined or 'sooth' in combined:
        ingredients.append({
            'name': 'Heartleaf Extract (Houttuynia Cordata 77%) & Cica',
            'role': 'Immediate Calming & Anti-Redness',
            'benefit': 'Provides fast relief for irritated skin, reduces micro-inflammation, and calms sensitivity.'
        })
    if 'rice' in combined or 'probiotic' in combined or 'joseon' in combined or 'spf' in combined or 'sun' in combined:
        ingredients.append({
            'name': 'Fermented Rice Extract & Grain Probiotics (30%)',
            'role': 'Antioxidant Defense & Nourishment',
            'benefit': 'Rich in vitamins B, C, and E to reinforce elasticity and provide a dewy, glass-skin finish.'
        })
    if 'salicylic' in combined or 'bha' in combined or 'aha' in combined:
        ingredients.append({
            'name': 'Salicylic Acid (BHA 2%) + Betaine',
            'role': 'Gentle Chemical Exfoliation',
            'benefit': 'Clears deep pore impurities, dissolves blackheads, and prevents future breakout formation.'
        })
    if 'snail' in combined or 'mucin' in combined or 'cosrx' in combined:
        ingredients.append({
            'name': 'Snail Secretion Filtrate 96%',
            'role': 'Intensive Repair & Skin Renewal',
            'benefit': 'Accelerates cellular turnover, smooths rough texture, and strengthens moisture retention.'
        })

    # Default fallback luxury actives if specific keywords weren't matched
    if len(ingredients) < 3:
        fallbacks = [
            {
                'name': 'Centella Asiatica (Cica) & Madecassoside',
                'role': 'Skin Soothing & Barrier Repair',
                'benefit': 'Botanical bioactive complex that speeds recovery and soothes redness.'
            },
            {
                'name': 'Hyaluronic Acid Multi-Complex',
                'role': 'Intense Cellular Hydration',
                'benefit': 'Binds moisture to the skin surface for a luminous, bouncy complexion.'
            },
            {
                'name': 'Plant-Derived Squalane & Vitamin E',
                'role': 'Antioxidant & Lipid Replenishment',
                'benefit': 'Protects against environmental stressors and softens dry skin.'
            },
            {
                'name': 'Multi-Peptide Matrixyl 3000 Complex',
                'role': 'Collagen Support & Firming',
                'benefit': 'Promotes natural collagen synthesis and minimizes fine dehydration lines.'
            }
        ]
        for item in fallbacks:
            if not any(i['name'] == item['name'] for i in ingredients):
                ingredients.append(item)
            if len(ingredients) >= 4:
                break

    return ingredients


# ==============================================================================
# ORGANIC FOOD & DAILY GROCERY THEME TEMPLATE FILTERS
# ==============================================================================

class GroceryNutritionData(list):
    """
    List of nutritional facts and purity standards that can also be directly rendered
    as an HTML table via mark_safe when referenced as {{ product|grocery_nutrition_table }}.
    """
    def __init__(self, items, html_table=""):
        super().__init__(items)
        self.html_table = html_table

    def __html__(self):
        return mark_safe(self.html_table)

    def __str__(self):
        return self.html_table


@register.filter(name='grocery_package_size')
def grocery_package_size(product):
    """
    Returns net weight, volume, or package size tag (e.g. 1 Kg, 500 gm, 1 Litre, 250 gm, 5 Kg).
    """
    if not product:
        return '1 Kg'
    name = getattr(product, 'name', '') or ''
    desc = getattr(product, 'description', '') or ''
    combined = f"{name} {desc}".lower()

    # Regex search for explicit weights/volumes
    match = re.search(r'\b(5\s*(?:kg|kilo|litres?|l))\b', combined)
    if match:
        val = match.group(1).lower()
        return '5 Litre' if 'l' in val and 'k' not in val else '5 Kg'

    match = re.search(r'\b(2\s*(?:kg|kilo|litres?|l))\b', combined)
    if match:
        val = match.group(1).lower()
        return '2 Litre' if 'l' in val and 'k' not in val else '2 Kg'

    match = re.search(r'\b(1\s*(?:litres?|liter|ltr|l))\b', combined)
    if match:
        return '1 Litre'

    match = re.search(r'\b(1\s*(?:kg|kilo))\b', combined)
    if match:
        return '1 Kg'

    match = re.search(r'\b(500\s*(?:gm|g|grams?|ml))\b', combined)
    if match:
        val = match.group(1).lower()
        return '500 ml' if 'ml' in val else '500 gm'

    match = re.search(r'\b(250\s*(?:gm|g|grams?|ml))\b', combined)
    if match:
        val = match.group(1).lower()
        return '250 ml' if 'ml' in val else '250 gm'

    match = re.search(r'\b(100\s*(?:gm|g|grams?|ml))\b', combined)
    if match:
        val = match.group(1).lower()
        return '100 ml' if 'ml' in val else '100 gm'

    cat_name = getattr(getattr(product, 'category', None), 'name', '').lower()
    cat_combined = f"{cat_name} {combined}"
    if 'oil' in cat_combined or 'ghee' in cat_combined:
        return '1 Litre'
    elif 'honey' in cat_combined or 'sweetener' in cat_combined:
        return '500 gm'
    elif 'spice' in cat_combined or 'masala' in cat_combined or 'turmeric' in cat_combined or 'chilli' in cat_combined:
        return '250 gm'
    elif 'rice' in cat_combined or 'flour' in cat_combined or 'atta' in cat_combined or 'daal' in cat_combined or 'lentil' in cat_combined:
        return '1 Kg'
    elif 'nut' in cat_combined or 'seed' in cat_combined or 'chia' in cat_combined:
        return '250 gm'
    elif 'tea' in cat_combined or 'coffee' in cat_combined:
        return '200 gm'
    elif 'fruit' in cat_combined or 'vegetable' in cat_combined or 'produce' in cat_combined:
        return '1 Kg'

    return '1 Kg'


@register.filter(name='grocery_unit_price')
def grocery_unit_price(product):
    """
    Returns unit price breakdown string e.g. (৳280/Kg) or (৳650/Litre).
    """
    if not product:
        return '(৳0/Kg)'
    try:
        price = float(product.effective_price)
    except Exception:
        price = 0.0

    pkg = grocery_package_size(product)
    pkg_lower = pkg.lower()

    if '5 kg' in pkg_lower:
        unit_price = round(price / 5)
        return f"(৳{unit_price}/Kg)"
    elif '2 kg' in pkg_lower:
        unit_price = round(price / 2)
        return f"(৳{unit_price}/Kg)"
    elif '1 kg' in pkg_lower:
        unit_price = round(price)
        return f"(৳{unit_price}/Kg)"
    elif '500 gm' in pkg_lower or '500g' in pkg_lower:
        unit_price = round(price * 2)
        return f"(৳{unit_price}/Kg)"
    elif '250 gm' in pkg_lower or '250g' in pkg_lower:
        unit_price = round(price * 4)
        return f"(৳{unit_price}/Kg)"
    elif '100 gm' in pkg_lower or '100g' in pkg_lower:
        unit_price = round(price * 10)
        return f"(৳{unit_price}/Kg)"
    elif '5 litre' in pkg_lower or '5 l' in pkg_lower:
        unit_price = round(price / 5)
        return f"(৳{unit_price}/Litre)"
    elif '2 litre' in pkg_lower or '2 l' in pkg_lower:
        unit_price = round(price / 2)
        return f"(৳{unit_price}/Litre)"
    elif '1 litre' in pkg_lower or '1 l' in pkg_lower:
        unit_price = round(price)
        return f"(৳{unit_price}/Litre)"
    elif '500 ml' in pkg_lower:
        unit_price = round(price * 2)
        return f"(৳{unit_price}/Litre)"
    elif '250 ml' in pkg_lower:
        unit_price = round(price * 4)
        return f"(৳{unit_price}/Litre)"
    else:
        return f"(৳{round(price)}/Kg)"


@register.filter(name='grocery_nutrition_table')
def grocery_nutrition_table(product):
    """
    Returns structured nutritional facts and purity standard metrics for grocery products.
    Can be iterated over or rendered directly as an HTML table.
    """
    name = getattr(product, 'name', '') or ''
    desc = getattr(product, 'description', '') or ''
    cat_name = getattr(getattr(product, 'category', None), 'name', '') or ''
    combined = f"{cat_name} {name} {desc}".lower()

    if 'oil' in combined or 'mustard' in combined:
        facts = [
            {'parameter': 'Energy / Calories', 'value': '884 kcal', 'daily_val': '44%'},
            {'parameter': 'Total Fat (Cold Pressed)', 'value': '100 g', 'daily_val': '128%'},
            {'parameter': 'Monounsaturated Fatty Acids (MUFA)', 'value': '60 g', 'daily_val': '—'},
            {'parameter': 'Polyunsaturated Fatty Acids (Omega-3 & 6)', 'value': '21 g', 'daily_val': '—'},
            {'parameter': 'Saturated Fat', 'value': '11 g', 'daily_val': '55%'},
            {'parameter': 'Carbohydrates & Sugars', 'value': '0 g', 'daily_val': '0%'},
            {'parameter': 'Protein', 'value': '0 g', 'daily_val': '0%'},
            {'parameter': 'Vitamin E (Natural Alpha-Tocopherol)', 'value': '34 mg', 'daily_val': '226%'},
        ]
        standards = [
            {'standard': 'Extraction Method', 'detail': 'Traditional Wood-Ghani Cold-Pressed (< 38°C)'},
            {'standard': 'Adulteration Screening', 'detail': '100% Free from Argemone Oil & Mineral Spirits (Lab Verified)'},
            {'standard': 'Purity Level', 'detail': '100% Virgin Single-Origin Yellow Mustard Seed'},
            {'standard': 'Preservatives & Additives', 'detail': 'Zero Hexane, Artificial Preservatives or Synthetic Color'},
        ]
    elif 'honey' in combined:
        facts = [
            {'parameter': 'Energy / Calories', 'value': '304 kcal', 'daily_val': '15%'},
            {'parameter': 'Total Carbohydrates', 'value': '82.4 g', 'daily_val': '30%'},
            {'parameter': 'Natural Fructose & Glucose', 'value': '78.2 g', 'daily_val': '—'},
            {'parameter': 'Dietary Fiber', 'value': '0.2 g', 'daily_val': '1%'},
            {'parameter': 'Protein', 'value': '0.3 g', 'daily_val': '1%'},
            {'parameter': 'Total Fat', 'value': '0 g', 'daily_val': '0%'},
            {'parameter': 'Antioxidants (Flavonoids & Phenols)', 'value': 'High Natural Spectrum', 'daily_val': '—'},
            {'parameter': 'Moisture Level', 'value': '< 19.5% (High Density Raw Honey)', 'daily_val': 'Compliant'},
        ]
        standards = [
            {'standard': 'Procurement Source', 'detail': 'Direct from Sundarbans / Mustard Wildflower Hive Beekeepers'},
            {'standard': 'Processing', 'detail': 'Unheated, Unpasteurized & Coarse Cotton Filtered'},
            {'standard': 'Purity Verification', 'detail': 'Zero Added Sugar Syrup, C4 Invert Sugar or Corn Starch'},
            {'standard': 'Shelf Life', 'detail': 'Indefinite (Keeps naturally fresh at room temperature)'},
        ]
    elif 'ghee' in combined or 'butter' in combined:
        facts = [
            {'parameter': 'Energy / Calories', 'value': '897 kcal', 'daily_val': '45%'},
            {'parameter': 'Total Milk Fat (Bilona Churned)', 'value': '99.5 g', 'daily_val': '127%'},
            {'parameter': 'Conjugated Linoleic Acid (CLA)', 'value': '4.5 g', 'daily_val': '—'},
            {'parameter': 'Short-Chain Butyric Acid', 'value': '3.8 g', 'daily_val': '—'},
            {'parameter': 'Saturated Fat', 'value': '62 g', 'daily_val': '—'},
            {'parameter': 'Protein & Lactose', 'value': '0.1 g (Virtually Lactose-Free)', 'daily_val': '0%'},
            {'parameter': 'Vitamin A & D', 'value': '3,200 IU / 100g', 'daily_val': '64%'},
        ]
        standards = [
            {'standard': 'Traditional Preparation', 'detail': 'Traditional Bilona Curd-Churning Method from Grass-Fed Cow Milk'},
            {'standard': 'Purity Standard', 'detail': '100% Pure Deshi Cow Milk Fat with Zero Dalda or Palm Stearin'},
            {'standard': 'Aroma & Texture', 'detail': 'Naturally Granular (Danedar) with Rich Golden Amber Hue'},
            {'standard': 'Lab Certification', 'detail': 'Certified Adulteration-Free by BSTI & ISO 22000 Standards'},
        ]
    elif 'rice' in combined or 'daal' in combined or 'lentil' in combined or 'grain' in combined:
        facts = [
            {'parameter': 'Energy / Calories', 'value': '356 kcal', 'daily_val': '18%'},
            {'parameter': 'Total Carbohydrates', 'value': '77.8 g', 'daily_val': '28%'},
            {'parameter': 'Protein', 'value': '8.2 g', 'daily_val': '16%'},
            {'parameter': 'Dietary Fiber', 'value': '3.4 g', 'daily_val': '12%'},
            {'parameter': 'Total Fat', 'value': '0.7 g', 'daily_val': '1%'},
            {'parameter': 'Iron & Minerals', 'value': '2.1 mg', 'daily_val': '12%'},
            {'parameter': 'Sodium', 'value': '5 mg', 'daily_val': '<1%'},
        ]
        standards = [
            {'standard': 'Milling & Polishing', 'detail': 'Unpolished & Single-Milled to Retain Nutrient-Rich Bran Layer'},
            {'standard': 'Chemical Processing', 'detail': '100% Free from Chemical Coating, Urea Bleaching or Artificial Aromas'},
            {'standard': 'Grain Sorting', 'detail': 'Triple Laser-Color Sorted for Clean, Uniform Premium Kernels'},
            {'standard': 'Storage Condition', 'detail': 'Hygienically Packed in Moisture-Barrier Resealable Food-Grade Bags'},
        ]
    else:
        facts = [
            {'parameter': 'Energy / Calories', 'value': '340 kcal', 'daily_val': '17%'},
            {'parameter': 'Total Carbohydrates', 'value': '65 g', 'daily_val': '24%'},
            {'parameter': 'Dietary Fiber', 'value': '12 g', 'daily_val': '43%'},
            {'parameter': 'Protein', 'value': '9.5 g', 'daily_val': '19%'},
            {'parameter': 'Total Fat', 'value': '3.2 g', 'daily_val': '4%'},
            {'parameter': 'Antioxidants & Curcuminoids', 'value': 'High Active Potency', 'daily_val': '—'},
            {'parameter': 'Sodium', 'value': '18 mg', 'daily_val': '1%'},
        ]
        standards = [
            {'standard': 'Purity Guarantee', 'detail': '100% Certified Organic & Chemical Fertilizer Free'},
            {'standard': 'Adulteration Testing', 'detail': 'Zero Added Lead Chromate, Artificial Colors or Synthetic Fillers'},
            {'standard': 'Procurement Origin', 'detail': 'Locally Procured directly from Contract Organic Farmers'},
            {'standard': 'Packaging Integrity', 'detail': 'Food-Grade Airtight Sealed to Preserve Freshness & Essential Oils'},
        ]

    # Build responsive HTML table (theme-aware light & dark mode classes)
    html_lines = [
        '<div class="grocery-nutrition-wrapper border rounded-3 p-3 shadow-xs">',
        '  <div class="row g-4">',
        '    <div class="col-md-7">',
        '      <div class="d-flex align-items-center justify-content-between mb-2">',
        '        <h6 class="fw-bold mb-0"><i class="bi bi-heart-pulse text-success me-1.5"></i>Nutritional Facts</h6>',
        '        <span class="badge bg-success-subtle text-success border border-success-subtle" style="font-size: 0.72rem;">Per 100g Serving</span>',
        '      </div>',
        '      <div class="table-responsive">',
        '        <table class="table table-sm table-striped align-middle mb-0" style="font-size: 0.82rem;">',
        '          <thead>',
        '            <tr>',
        '              <th class="py-1.5">Nutrient Component</th>',
        '              <th class="py-1.5 text-end">Amount</th>',
        '              <th class="py-1.5 text-end">% Daily Value*</th>',
        '            </tr>',
        '          </thead>',
        '          <tbody>',
    ]
    for row in facts:
        html_lines.append(
            f'            <tr>'
            f'<td class="py-1.5 fw-medium">{escape(row["parameter"])}</td>'
            f'<td class="py-1.5 text-end text-success fw-semibold">{escape(row["value"])}</td>'
            f'<td class="py-1.5 text-end opacity-75 small">{escape(row["daily_val"])}</td>'
            f'</tr>'
        )
    html_lines.extend([
        '          </tbody>',
        '        </table>',
        '      </div>',
        '      <div class="mt-2 opacity-75" style="font-size: 0.7rem;">*Percent Daily Values are based on a 2,000 calorie balanced organic diet.</div>',
        '    </div>',
        '    <div class="col-md-5">',
        '      <h6 class="fw-bold mb-2"><i class="bi bi-shield-check text-primary me-1.5"></i>Purity & Standard Verification</h6>',
        '      <div class="d-flex flex-column gap-2">',
    ])
    for std in standards:
        html_lines.append(
            f'        <div class="p-2.5 rounded-2 border grocery-std-card" style="font-size: 0.8rem;">'
            f'<div class="fw-bold mb-0.5"><i class="bi bi-check-circle-fill text-success me-1"></i>{escape(std["standard"])}</div>'
            f'<div class="opacity-75 small">{escape(std["detail"])}</div>'
            f'</div>'
        )
    html_lines.extend([
        '      </div>',
        '    </div>',
        '  </div>',
        '</div>'
    ])

    html_table = '\n'.join(html_lines)
    return GroceryNutritionData(facts, html_table)



