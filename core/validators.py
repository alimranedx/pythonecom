import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme
from PIL import Image

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP'}


def validate_image_file(file):
    """
    Validates uploaded images to prevent:
    1. DoS attacks via oversized file uploads (max 5MB).
    2. Shell scripts / malware uploaded with spoofed extensions.
    3. SVG-based Cross-Site Scripting (XSS).
    """
    # 1. Size Validation
    if file.size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError("File size exceeds the 5 MB maximum limit.")

    # 2. Extension Whitelist Validation
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file format '{ext}'. Only JPG, PNG, and WebP images are allowed."
        )

    # 3. Deep Image Header & Content Inspection with Pillow
    try:
        # Seek to beginning in case file pointer was moved
        file.seek(0)
        img = Image.open(file)
        img.verify()

        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                f"Invalid or corrupted image format ({img.format})."
            )
        file.seek(0)
    except Exception as e:
        raise ValidationError("The uploaded file is not a valid or safe image file.")


def get_safe_upload_path(instance, filename, prefix='uploads'):
    """
    Sanitizes filenames to prevent Path Traversal attacks.
    Example: '../../../malicious.php' becomes 'prefix/a1b2c3d4.jpg'
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = '.jpg'
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(prefix, unique_name)


def get_safe_redirect_url(request, target_url, fallback_endpoint):
    """
    Prevents Open Redirect (CWE-601) attacks by validating the target host and scheme.
    """
    if target_url and url_has_allowed_host_and_scheme(url=target_url, allowed_hosts={request.get_host()}):
        return target_url
    from django.urls import reverse
    try:
        return reverse(fallback_endpoint)
    except Exception:
        return fallback_endpoint
