from django.db import models
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SiteSetting(TimeStampedModel):
    """
    Singleton model representing dynamic store branding,
    top header announcements, contact information, and footer configurations.
    Managed via Back-Office Admin Panel with RBAC security.
    """
    # 1. Brand Identity (Header & Footer)
    site_name = models.CharField(max_length=100, default="Easy Purchase", help_text="Public brand / store name")
    site_tagline = models.CharField(max_length=200, default="Modern E-Commerce Marketplace", blank=True, help_text="Short slogan or tagline")
    brand_logo = models.ImageField(upload_to="branding/", blank=True, null=True, help_text="Brand logo image (replaces default icon/text)")
    brand_favicon = models.ImageField(upload_to="branding/", blank=True, null=True, help_text="Browser tab favicon")

    # 2. Top Header & Announcement Bar
    announcement_enabled = models.BooleanField(default=True, help_text="Show or hide top announcement bar")
    announcement_text_en = models.CharField(max_length=255, default="Free Express Shipping on orders over ৳500!", blank=True, help_text="Announcement message in English")
    announcement_text_bn = models.CharField(max_length=255, default="৳৫০০ এর বেশি অর্ডারে ফ্রি এক্সপ্রেস ডেলিভারি!", blank=True, help_text="Announcement message in Bangla")
    customer_care_text_en = models.CharField(max_length=100, default="24/7 Customer Care", blank=True, help_text="Customer care text in English")
    customer_care_text_bn = models.CharField(max_length=100, default="২৪/৭ কাস্টমার কেয়ার", blank=True, help_text="Customer care text in Bangla")
    contact_phone = models.CharField(max_length=50, default="+880 1700-000000", help_text="Public contact & support telephone")
    contact_email = models.EmailField(default="support@easypuchase.com", blank=True, help_text="Public support email")
    contact_address = models.CharField(max_length=255, default="Dhaka, Bangladesh", blank=True, help_text="Physical store or office address")

    # 3. Footer & Brand Information
    about_text_en = models.TextField(
        default="Enterprise-ready multi-category e-commerce platform built on Django, featuring role-based back-office security and high-converting storefront design.",
        blank=True,
        help_text="About the company description in English"
    )
    about_text_bn = models.TextField(
        default="উন্নত প্রযুক্তিতে তৈরি বাংলাদেশের নির্ভরযোগ্য ই-কমার্স মার্কেটপ্লেস। গ্রাহক সন্তুষ্টি ও নিরাপদ শপিং আমাদের অঙ্গীকার।",
        blank=True,
        help_text="About the company description in Bangla"
    )

    # 4. Social Media Links
    social_facebook = models.URLField(blank=True, default="https://facebook.com", help_text="Facebook Page URL")
    social_twitter = models.URLField(blank=True, default="https://twitter.com", help_text="Twitter / X profile URL")
    social_instagram = models.URLField(blank=True, default="https://instagram.com", help_text="Instagram profile URL")
    social_github = models.URLField(blank=True, default="https://github.com", help_text="GitHub organization or repo URL")
    social_linkedin = models.URLField(blank=True, default="", help_text="LinkedIn page URL")

    # 5. Newsletter & Payments
    newsletter_title_en = models.CharField(max_length=100, default="Newsletter", blank=True)
    newsletter_title_bn = models.CharField(max_length=100, default="নিউজলেটার", blank=True)
    newsletter_text_en = models.CharField(max_length=255, default="Subscribe to get special discounts and exclusive product launches.", blank=True)
    newsletter_text_bn = models.CharField(max_length=255, default="বিশেষ মূল্যছাড় ও নতুন পণ্যের আপডেট পেতে ইমেইল সাবস্ক্রাইব করুন।", blank=True)
    accepted_payments_text = models.CharField(max_length=255, default="Cash on Delivery, Credit / Debit Card, bKash / Nagad", blank=True)

    # 6. Copyright & Sub-Footer Notices
    copyright_text = models.CharField(
        max_length=255,
        default="© 2026 Easy Purchase. All rights reserved.",
        blank=True
    )
    subfooter_notice = models.CharField(
        max_length=255,
        default="Engineered with Clean Layered Architecture & RBAC Security",
        blank=True
    )

    class Meta:
        verbose_name = "Store & Brand Settings"
        verbose_name_plural = "Store & Brand Settings"

    def __str__(self):
        return f"Site Configuration ({self.site_name})"

    @classmethod
    def get_settings(cls):
        """
        Retrieves the singleton settings record, automatically creating
        an initial record with production defaults if none exists.
        """
        instance = cls.objects.first()
        if not instance:
            instance = cls.objects.create()
        if instance.site_name in ['ShopBusket Ecommerce', 'PythonEcom', 'ShopBusket', '']:
            instance.site_name = 'Easy Purchase'
            instance.contact_email = 'support@easypuchase.com'
            instance.copyright_text = '© 2026 Easy Purchase. All rights reserved.'
            instance.save(update_fields=['site_name', 'contact_email', 'copyright_text'])
        return instance

    def get_announcement_text(self, is_bangla=False):
        if is_bangla and self.announcement_text_bn:
            return self.announcement_text_bn
        return self.announcement_text_en or ""

    def get_customer_care_text(self, is_bangla=False):
        if is_bangla and self.customer_care_text_bn:
            return self.customer_care_text_bn
        return self.customer_care_text_en or ""

    def get_about_text(self, is_bangla=False):
        if is_bangla and self.about_text_bn:
            return self.about_text_bn
        return self.about_text_en or ""

    def get_newsletter_title(self, is_bangla=False):
        if is_bangla and self.newsletter_title_bn:
            return self.newsletter_title_bn
        return self.newsletter_title_en or ""

    def get_newsletter_text(self, is_bangla=False):
        if is_bangla and self.newsletter_text_bn:
            return self.newsletter_text_bn
        return self.newsletter_text_en or ""


class SystemErrorLog(TimeStampedModel):
    """
    Captures system-wide exceptions, unhandled 500 errors, and runtime failures
    to notify administrators and facilitate rapid debugging.
    """
    error_type = models.CharField(max_length=255, db_index=True)
    message = models.TextField()
    traceback = models.TextField()
    path = models.CharField(max_length=500, db_index=True)
    method = models.CharField(max_length=10, default='GET')
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='system_errors')
    user_agent = models.CharField(max_length=500, blank=True)
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_errors')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "System Error Log"
        verbose_name_plural = "System Error Logs"

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else 'New'}] {self.error_type} on {self.path}"

    @classmethod
    def log_exception(cls, request, exception):
        """
        Safely records an unhandled exception to both the database and logger.
        Guaranteed never to raise secondary exceptions.
        """
        import sys
        import traceback
        import logging

        tb_text = traceback.format_exc()
        if not tb_text or tb_text.strip() == 'NoneType: None':
            exc_type, exc_val, exc_tb = sys.exc_info()
            if exc_tb:
                tb_text = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            else:
                tb_text = str(exception)

        path = getattr(request, 'path_info', '') or getattr(request, 'path', 'Unknown')
        method = getattr(request, 'method', 'GET')
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None

        meta = getattr(request, 'META', {})
        x_forwarded = meta.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = meta.get('REMOTE_ADDR')

        user_agent = str(meta.get('HTTP_USER_AGENT', ''))[:500]
        err_type = exception.__class__.__name__
        err_msg = str(exception)

        # 1. Log to Python standard logging
        logger = logging.getLogger('django.request')
        logger.error(
            f"System Exception: {err_type} on {method} {path} | User: {user} | IP: {ip}\n{tb_text}"
        )

        # 2. Persist to database for Admin alert & tracking
        try:
            return cls.objects.create(
                error_type=err_type[:255],
                message=err_msg,
                traceback=tb_text,
                path=path[:500],
                method=method[:10],
                ip_address=ip if ip and len(ip) <= 45 else None,
                user=user,
                user_agent=user_agent,
                is_resolved=False
            )
        except Exception as db_err:
            logger.error(f"Failed to record SystemErrorLog to database: {db_err}")
            return None
