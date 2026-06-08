import uuid
from django.db import models


def generate_reference():
    """Generate a unique reference like SS-2025-MH-00423 (simplified version)."""
    import random, string
    suffix = ''.join(random.choices(string.digits, k=5))
    return f"SS-{suffix}"


class ScamReport(models.Model):

    # ── SCAM TYPE (Level 1) ───────────────────────────────────────────────
    SCAM_TYPES = [
        ('phishing',    'Phishing'),
        ('fraud_call',  'Fraud Call / Vishing'),
        ('fake_shop',   'Fake Online Shop'),
        ('upi_fraud',   'UPI / Banking Fraud'),
        ('investment',  'Investment / Crypto Scam'),
        ('job_scam',    'Job Offer Scam'),
        ('ransomware',  'Ransomware / Malware'),
        ('sextortion',  'Sextortion / Blackmail'),
        ('other',       'Other'),
    ]

    # ── SCAM SUB-CATEGORY (Level 2) ───────────────────────────────────────
    SCAM_SUBTYPES = [
        # Phishing
        ('kyc_update',      'KYC / Aadhaar Update'),
        ('bank_verify',     'Bank Account Verification'),
        ('irctc_refund',    'IRCTC / Travel Refund'),
        ('upi_link',        'Fake UPI Payment Link'),
        ('electricity',     'Electricity Bill Scam'),
        ('delivery',        'Fake Delivery / Courier'),
        # Fraud Call
        ('impersonation',   'Government / Officer Impersonation'),
        ('tech_support',    'Fake Tech Support'),
        ('lottery',         'Lottery / Prize Scam'),
        ('loan_offer',      'Fake Loan Offer'),
        # Fake Shop
        ('fake_product',    'Fake Product Listing'),
        ('non_delivery',    'Payment Taken, No Delivery'),
        ('discount_fraud',  'Fake Discount / Coupon'),
        # UPI / Banking
        ('screen_share',    'Screen Share / Remote Access'),
        ('qr_scam',         'QR Code Fraud'),
        ('emi_fraud',       'EMI / Loan App Fraud'),
        # Investment
        ('stock_tip',       'Fake Stock Tips'),
        ('crypto_fraud',    'Crypto / NFT Fraud'),
        ('ponzi',           'Ponzi / MLM Scheme'),
        # Other
        ('other',           'Other / Not Listed'),
    ]

    # ── PLATFORM / CHANNEL ────────────────────────────────────────────────
    PLATFORM_CHOICES = [
        ('whatsapp',    'WhatsApp'),
        ('phone_call',  'Phone Call'),
        ('sms',         'SMS'),
        ('email',       'Email'),
        ('telegram',    'Telegram'),
        ('instagram',   'Instagram'),
        ('facebook',    'Facebook'),
        ('youtube',     'YouTube'),
        ('website',     'Fake Website'),
        ('truecaller',  'Truecaller / Unknown Number'),
        ('other',       'Other'),
    ]

    # ── SEVERITY ──────────────────────────────────────────────────────────
    SEVERITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]

    # ── STATUS ────────────────────────────────────────────────────────────
    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('verified',  'Verified'),
        ('rejected',  'Rejected'),
        ('escalated', 'Escalated to Authorities'),
    ]

    # ── CORE FIELDS ───────────────────────────────────────────────────────
    reference_number = models.CharField(
        max_length=20,unique=True, blank=True,
        help_text="Auto-generated unique reference, e.g. SS-00423"
    )
    title = models.CharField(
        max_length=200,
        help_text="Brief title / platform name"
    )

    # Scam classification
    scam_type    = models.CharField(max_length=50, choices=SCAM_TYPES)
    scam_subtype = models.CharField(
        max_length=50, choices=SCAM_SUBTYPES,
        blank=True, default='',
        help_text="More specific sub-category of the scam"
    )

    # Communication channel
    platform = models.CharField(
        max_length=50, choices=PLATFORM_CHOICES,
        blank=True, default='',
        help_text="Channel used by scammer to contact victim"
    )
    platform_detail = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Free text: specific app, website URL, email domain etc."
    )

    # What happened
    description = models.TextField(help_text="Full description of the incident")

    # ── LOCATION ──────────────────────────────────────────────────────────
    location  = models.CharField(max_length=255, help_text="City or place")
    pin_code  = models.CharField(
        max_length=6, blank=True, default='',
        help_text="6-digit Indian PIN code"
    )
    state     = models.CharField(max_length=100, blank=True, default='')
    latitude  = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # ── SCAMMER DETAILS ───────────────────────────────────────────────────
    scammer_contact = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Phone, email, or username of scammer"
    )
    scammer_upi     = models.CharField(
        max_length=255, blank=True, default='',
        help_text="Scammer's UPI ID (e.g. name@okaxis)"
    )
    scammer_account = models.CharField(
        max_length=50, blank=True, default='',
        help_text="Bank account number if known"
    )
    scammer_ifsc    = models.CharField(
        max_length=11, blank=True, default='',
        help_text="IFSC code of scammer's bank"
    )
    bank_involved   = models.CharField(
        max_length=100, blank=True, default='',
        help_text="Bank name targeted or used in the fraud"
    )

    # ── FINANCIAL ─────────────────────────────────────────────────────────
    amount_lost = models.DecimalField(
        max_digits=12, decimal_places=2,
        null=True, blank=True,
        help_text="Total amount lost in INR"
    )

    # ── DATES ─────────────────────────────────────────────────────────────
    incident_date     = models.DateField(
        null=True, blank=True,
        help_text="Date when the scam occurred"
    )
    incident_time     = models.TimeField(
        null=True, blank=True,
        help_text="Approximate time when the scam occurred"
    )
    date_reported     = models.DateTimeField(
        auto_now_add=True,
        help_text="When this report was submitted"
    )

    # ── EVIDENCE ──────────────────────────────────────────────────────────
    evidence = models.FileField(
        upload_to='evidence/', null=True, blank=True,
        help_text="Screenshot, recording, or document"
    )

    # ── REPORTER SETTINGS ─────────────────────────────────────────────────
    anonymous = models.BooleanField(
        default=False,
        help_text="Hide reporter identity from public view"
    )

    # ── ADMIN / MODERATION ────────────────────────────────────────────────
    severity = models.IntegerField(
        choices=SEVERITY_CHOICES, default=2,
        help_text="Severity level set by system or admin"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default='pending',
        help_text="Moderation status"
    )
    admin_note = models.TextField(
        blank=True, default='',
        help_text="Internal note from admin (not shown publicly)"
    )

    # Keep old 'date' field as alias so existing queries don't break
    # We'll use incident_date going forward
    date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date_reported']
        indexes = [
            models.Index(fields=['scam_type']),
            models.Index(fields=['platform']),
            models.Index(fields=['location']),
            models.Index(fields=['status']),
            models.Index(fields=['-date_reported']),
            models.Index(fields=['reference_number']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate reference number on first save
        if not self.reference_number:
            import random, string
            while True:
                suffix = ''.join(random.choices(string.digits, k=5))
                ref = f"SS-{suffix}"
                if not ScamReport.objects.filter(reference_number=ref).exists():
                    self.reference_number = ref
                    break

        # Auto-calculate severity based on amount lost
        if self.severity == 2:  # only if still at default
            if self.amount_lost:
                amt = float(self.amount_lost)
                if amt >= 100000:
                    self.severity = 4  # Critical (≥1L)
                elif amt >= 10000:
                    self.severity = 3  # High (≥10k)
                elif amt >= 1000:
                    self.severity = 2  # Medium (≥1k)
                else:
                    self.severity = 1  # Low

        # Keep legacy 'date' field in sync with incident_date
        if self.incident_date and not self.date:
            self.date = self.incident_date

        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.reference_number}] {self.title} — {self.location}"

    def get_severity_label(self):
        return dict(self.SEVERITY_CHOICES).get(self.severity, 'Unknown')

    def get_severity_color(self):
        return {1: 'green', 2: 'amber', 3: 'orange', 4: 'red'}.get(self.severity, 'gray')

    @property
    def is_critical(self):
        return self.severity >= 4