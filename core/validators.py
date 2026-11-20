import os
import uuid
from django.core.exceptions import ValidationError
from django.utils.http import url_has_allowed_host_and_scheme
from PIL import Image

MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB maximum limit
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.jfif', '.gif', '.bmp', '.avif'}
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'BMP', 'AVIF'}


def validate_image_file(file):
    """
    Validates uploaded images to prevent:
    1. DoS attacks via oversized file uploads (max 10MB).
    2. Non-image files or SVG script injections disguised as images.
    3. Corrupted or malicious image byte streams.
    Supports JPG, JPEG, PNG, WebP, JFIF, GIF, BMP, and AVIF.
    """
    if not file:
        return

    # If it's an existing saved FieldFile with no new upload, skip re-validation
    from django.db.models.fields.files import FieldFile
    if isinstance(file, FieldFile) and not hasattr(file, 'file'):
        return

    # 1. Size Validation
    try:
        if file.size > MAX_IMAGE_SIZE_BYTES:
            raise ValidationError(
                f"File size exceeds the 10 MB limit (current: {file.size / (1024 * 1024):.1f} MB)."
            )
    except (AttributeError, ValueError):
        pass

    # 2. Extension Validation & Explicit SVG / Script File Disallowance
    file_name = getattr(file, 'name', '') or ''
    ext = os.path.splitext(file_name)[1].lower()
    disallowed_extensions = {'.svg', '.svgz', '.xml', '.html', '.htm', '.js', '.php', '.phtml', '.sh', '.py'}
    if ext in disallowed_extensions:
        raise ValidationError(
            f"File format '{ext}' is not permitted due to security policies (SVG script injection protection)."
        )
    if ext and ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file format '{ext}'. Allowed formats: JPG, JPEG, PNG, WebP, JFIF, GIF, BMP, AVIF."
        )

    # 3. Content Inspection: Prevent SVG / XML / HTML / Script Injections in byte payload
    try:
        if hasattr(file, 'seek'):
            file.seek(0)
        
        sample = file.read(4096)
        if hasattr(file, 'seek'):
            file.seek(0)

        sample_lower = sample.lower() if isinstance(sample, bytes) else str(sample).lower().encode('utf-8')
        dangerous_signatures = [
            b'<svg', b'<?xml', b'<script', b'<!doctype svg',
            b'xmlns="http://www.w3.org/2000/svg"', b"xmlns='http://www.w3.org/2000/svg'",
            b'<html', b'<!doctype html', b'javascript:', b'onload=', b'onerror=', b'onclick='
        ]
        for sig in dangerous_signatures:
            if sig in sample_lower:
                raise ValidationError("SVG script injection or active content detected in uploaded file.")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Failed to inspect uploaded file content: {str(e)}")

    # 4. Deep Image Header & Content Inspection with Pillow
    try:
        if hasattr(file, 'seek'):
            file.seek(0)

        img = Image.open(file)
        img_format = (img.format or '').upper()

        if img_format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                f"Unsupported image encoding ({img_format or 'unknown'}). Please upload a valid JPG, PNG, WebP, or GIF."
            )

        # Verify image integrity
        img.verify()

        if hasattr(file, 'seek'):
            file.seek(0)
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"The uploaded file is not a valid image file ({str(e)}).")


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
