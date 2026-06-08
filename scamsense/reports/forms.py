from django import forms
from reports.models import ScamReport

# ── Shared Indian Banks list ──────────────────────────────────────────────────
INDIAN_BANKS = [
    ('', 'Select bank (optional)'),
    ('sbi',     'State Bank of India'),
    ('hdfc',    'HDFC Bank'),
    ('icici',   'ICICI Bank'),
    ('axis',    'Axis Bank'),
    ('kotak',   'Kotak Mahindra Bank'),
    ('pnb',     'Punjab National Bank'),
    ('bob',     'Bank of Baroda'),
    ('canara',  'Canara Bank'),
    ('union',   'Union Bank of India'),
    ('indusind','IndusInd Bank'),
    ('idfc',    'IDFC First Bank'),
    ('yes',     'Yes Bank'),
    ('paytm',   'Paytm Payments Bank'),
    ('airtel',  'Airtel Payments Bank'),
    ('post',    'India Post Payments Bank'),
    ('other',   'Other / Not Listed'),
]

# ── Shared widget style strings ───────────────────────────────────────────────
# These match the dark theme in your report.html template
_INPUT = (
    "width:100%;background:#0d1520;border:1px solid rgba(30,58,95,0.55);"
    "border-radius:10px;padding:10px 14px;font-size:13.5px;color:#e2e8f0;"
    "font-family:inherit;outline:none;transition:border-color .15s;"
)
_SELECT   = _INPUT + "appearance:none;cursor:pointer;"
_TEXTAREA = _INPUT + "resize:vertical;min-height:100px;"
_CHECK    = "width:16px;height:16px;accent-color:#22d3ee;cursor:pointer;"


# ── STEP 1 — What kind of scam & when? ───────────────────────────────────────
class Step1Form(forms.Form):

    scam_type = forms.ChoiceField(
        choices=[('', 'Select scam type...')] + ScamReport.SCAM_TYPES,
        label="Scam Type",
        widget=forms.Select(attrs={"style": _SELECT})
    )

    scam_subtype = forms.ChoiceField(
        choices=[('', 'Select sub-category (optional)...')] + ScamReport.SCAM_SUBTYPES,
        label="Sub-Category",
        required=False,
        widget=forms.Select(attrs={"style": _SELECT})
    )

    platform = forms.ChoiceField(
        choices=[('', 'Select platform / channel...')] + ScamReport.PLATFORM_CHOICES,
        label="Platform / Channel Used by Scammer",
        widget=forms.Select(attrs={"style": _SELECT})
    )

    platform_detail = forms.CharField(
        max_length=255,
        label="Platform Detail (optional)",
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "e.g. specific website URL, app name, email domain..."
        })
    )

    incident_date = forms.DateField(
        label="Date of Incident",
        widget=forms.DateInput(attrs={"type": "date", "style": _INPUT})
    )

    incident_time = forms.TimeField(
        label="Approximate Time of Incident (optional)",
        required=False,
        widget=forms.TimeInput(attrs={"type": "time", "style": _INPUT})
    )


# ── STEP 2 — What happened & financial details ────────────────────────────────
class Step2Form(forms.Form):

    title = forms.CharField(
        max_length=200,
        label="Brief Title",
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "e.g. Fake IRCTC refund link via WhatsApp"
        })
    )

    description = forms.CharField(
        label="Full Description",
        widget=forms.Textarea(attrs={
            "style": _TEXTAREA,
            "placeholder": "Describe exactly what happened — the more detail the better..."
        })
    )

    amount_lost = forms.DecimalField(
        required=False,
        max_digits=12,
        decimal_places=2,
        label="Amount Lost (₹)",
        widget=forms.NumberInput(attrs={
            "style": _INPUT,
            "placeholder": "0 if no financial loss"
        })
    )

    bank_involved = forms.ChoiceField(
        choices=INDIAN_BANKS,
        label="Bank Involved (if any)",
        required=False,
        widget=forms.Select(attrs={"style": _SELECT})
    )


# ── STEP 3 — Scammer details, location & evidence ────────────────────────────
class Step3Form(forms.Form):

    scammer_contact = forms.CharField(
        label="Scammer's Phone / Email / Username",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "+91 XXXXX XXXXX  or  scammer@mail.com"
        })
    )

    scammer_upi = forms.CharField(
        label="Scammer's UPI ID (if known)",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "e.g. name@okaxis  or  9876543210@ybl"
        })
    )

    scammer_account = forms.CharField(
        label="Scammer's Bank Account Number (if known)",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "Account number"
        })
    )

    scammer_ifsc = forms.CharField(
        label="Scammer's Bank IFSC Code (if known)",
        max_length=11,
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "e.g. SBIN0001234"
        })
    )

    location = forms.CharField(
        max_length=255,
        label="Your Location (City)",
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "e.g. Mumbai, Bengaluru, Hyderabad..."
        })
    )

    pin_code = forms.CharField(
        max_length=6,
        label="Your PIN Code (optional)",
        required=False,
        widget=forms.TextInput(attrs={
            "style": _INPUT,
            "placeholder": "6-digit PIN code"
        })
    )

    evidence = forms.FileField(
        required=False,
        label="Upload Evidence (screenshot, recording, document)",
        widget=forms.ClearableFileInput(attrs={"style": _INPUT})
    )

    anonymous = forms.BooleanField(
        required=False,
        label="Submit this report anonymously",
        widget=forms.CheckboxInput(attrs={"style": _CHECK})
    )

    # ── Validation ────────────────────────────────────────────────────────

    def clean_pin_code(self):
        pin = self.cleaned_data.get('pin_code', '').strip()
        if pin and (not pin.isdigit() or len(pin) != 6):
            raise forms.ValidationError("PIN code must be exactly 6 digits.")
        return pin

    def clean_scammer_upi(self):
        upi = self.cleaned_data.get('scammer_upi', '').strip()
        if upi and '@' not in upi:
            raise forms.ValidationError("UPI ID must contain '@' (e.g. name@okaxis).")
        return upi

    def clean_scammer_ifsc(self):
        ifsc = self.cleaned_data.get('scammer_ifsc', '').strip().upper()
        if ifsc and len(ifsc) != 11:
            raise forms.ValidationError("IFSC code must be exactly 11 characters.")
        return ifsc

    def clean_evidence(self):
        f = self.cleaned_data.get('evidence')
        if f:
            allowed = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf', 'video/mp4']
            if hasattr(f, 'content_type') and f.content_type not in allowed:
                raise forms.ValidationError("Only JPG, PNG, WEBP, PDF, or MP4 files are allowed.")
            if f.size > 15 * 1024 * 1024:
                raise forms.ValidationError("File too large. Maximum size is 15 MB.")
        return f


# ── STEP 4 — Review & confirm ─────────────────────────────────────────────────
class Step4Form(forms.Form):

    confirm = forms.BooleanField(
        required=True,
        label="I confirm the information provided is accurate to the best of my knowledge.",
        widget=forms.CheckboxInput(attrs={"style": _CHECK})
    )