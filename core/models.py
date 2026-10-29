from django.db import models


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
    site_name = models.CharField(max_length=100, default="PythonEcom", help_text="Public brand / store name")
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
    contact_email = models.EmailField(default="support@pythonecom.com", blank=True, help_text="Public support email")
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
        default="© 2026 PythonEcom. Senior Software Engineering Implementation. All rights reserved.",
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
