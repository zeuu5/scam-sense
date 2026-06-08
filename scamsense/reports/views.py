import json
import traceback
from decimal import Decimal
from datetime import date, datetime, time

import requests
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from .forms import Step1Form, Step2Form, Step3Form, Step4Form
from .models import ScamReport


# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_lat_lon(city_name: str):
    """Best-effort geocoding via Nominatim. Returns (lat, lon) or (None, None)."""
    if not city_name:
        return None, None
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': city_name + ', India', 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'ScamSense-India/1.0'}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception as e:
        print(f"[GEOCODE ERROR] '{city_name}': {e}")
    return None, None


def _serialize(value):
    """Make a cleaned_data value JSON-safe for session storage."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    try:
        from django.core.files.uploadedfile import UploadedFile
        if isinstance(value, UploadedFile):
            return None  # files are never stored in session
    except Exception:
        pass
    return value


def _parse_date(value):
    if not value:
        return None
    try:
        if isinstance(value, str) and len(value) == 10:
            return datetime.strptime(value, "%Y-%m-%d").date()
        return datetime.fromisoformat(value).date()
    except Exception:
        return None


def _parse_time(value):
    if not value:
        return None
    try:
        if isinstance(value, str):
            return time.fromisoformat(value)
    except Exception:
        return None
    return None


# ── VIEWS ─────────────────────────────────────────────────────────────────────

def home(request):
    query = request.GET.get('q', '').strip()
    reports = ScamReport.objects.filter(status__in=['pending', 'verified', 'escalated'])

    if query:
        reports = reports.filter(
            Q(title__icontains=query) |
            Q(location__icontains=query) |
            Q(scam_type__icontains=query) |
            Q(description__icontains=query)
        )

    # Heatmap data
    location_counts = (
        reports.values('latitude', 'longitude')
        .annotate(count=Count('id'))
    )
    heatmap_data = [
        [loc['latitude'], loc['longitude'], loc['count']]
        for loc in location_counts
        if loc['latitude'] and loc['longitude']
    ]

    latest_reports = reports.order_by('-date_reported')[:6]

    most_reported = (
        ScamReport.objects.filter(status__in=['pending','verified','escalated'])
        .values('location')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    # Summary stats for stats bar
    total_reports  = ScamReport.objects.count()
    total_loss     = ScamReport.objects.aggregate(t=Sum('amount_lost'))['t'] or 0
    critical_count = ScamReport.objects.filter(severity=4).count()

    return render(request, 'reports/home.html', {
        'heatmap_data':   json.dumps(heatmap_data),
        'latest_reports': latest_reports,
        'most_reported':  most_reported,
        'query':          query,
        'search_results': reports if query else None,
        'total_reports':  total_reports,
        'total_loss':     total_loss,
        'critical_count': critical_count,
    })


@csrf_exempt
def report_scam(request, step=1):
    """
    4-step report wizard using AJAX + session storage.
    Step 1 → Step1Form  (scam type, platform, date/time)
    Step 2 → Step2Form  (title, description, amount, bank)
    Step 3 → Step3Form  (scammer details, location, evidence, anonymous)
    Step 4 → Step4Form  (confirm → write to DB)
    """
    try:
        try:
            step = int(step)
        except Exception:
            return JsonResponse({'error': 'Invalid step'}, status=400)

        if step < 1 or step > 4:
            return JsonResponse({'error': 'Invalid step'}, status=400)

        session   = request.session
        form_data = session.get('scam_report', {})
        form_classes = [Step1Form, Step2Form, Step3Form, Step4Form]
        FormClass = form_classes[step - 1]

        if request.method == 'POST':
            form = FormClass(request.POST, request.FILES)
            if not form.is_valid():
                return JsonResponse({'errors': form.errors}, status=400)

            # Merge new data into session (skip files)
            merged = dict(form_data)
            for k, v in form.cleaned_data.items():
                sv = _serialize(v)
                if sv is not None:
                    merged[k] = sv
                elif k == 'evidence':
                    merged['_has_evidence'] = True

            session['scam_report'] = merged

            # Not the final step — just advance
            if step < 4:
                return JsonResponse({'next_step': step + 1})

            # ── FINAL STEP: write to DB ────────────────────────────────
            location = merged.get('location', '').strip()
            lat, lon = get_lat_lon(location)

            amount_lost = form.cleaned_data.get('amount_lost')
            if amount_lost is None and merged.get('amount_lost'):
                try:
                    amount_lost = Decimal(merged['amount_lost'])
                except Exception:
                    amount_lost = None

            evidence_file = form.cleaned_data.get('evidence')

            report = ScamReport.objects.create(
                # Classification
                scam_type    = merged.get('scam_type', ''),
                scam_subtype = merged.get('scam_subtype', ''),

                # Channel
                platform        = merged.get('platform', ''),
                platform_detail = merged.get('platform_detail', ''),

                # Content
                title       = merged.get('title', ''),
                description = merged.get('description', ''),

                # Dates
                incident_date = _parse_date(merged.get('incident_date')),
                incident_time = _parse_time(merged.get('incident_time')),
                date          = _parse_date(merged.get('incident_date')),  # legacy field

                # Location
                location  = location,
                pin_code  = merged.get('pin_code', ''),
                state     = merged.get('state', ''),
                latitude  = lat,
                longitude = lon,

                # Scammer details
                scammer_contact = merged.get('scammer_contact', ''),
                scammer_upi     = merged.get('scammer_upi', ''),
                scammer_account = merged.get('scammer_account', ''),
                scammer_ifsc    = merged.get('scammer_ifsc', '').upper(),
                bank_involved   = merged.get('bank_involved', ''),

                # Financial
                amount_lost = amount_lost,

                # Evidence & privacy
                evidence  = evidence_file,
                anonymous = bool(merged.get('anonymous', False)),
            )

            # Clear wizard session data
            session.pop('scam_report', None)

            return JsonResponse({
                'submitted':        True,
                'reference_number': report.reference_number,
                'message':          f'Report {report.reference_number} submitted successfully!'
            })

        # ── GET: render the current step form ─────────────────────────────
        form = FormClass()
        return render(request, 'reports/report.html', {
            'form': form,
            'step': step,
        })

    except Exception as e:
        print("ERROR in report_scam:", e)
        traceback.print_exc()
        return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=500)


def explore_scams(request):
    scams = ScamReport.objects.filter(status__in=['pending', 'verified', 'escalated'])
    query = request.GET.get('q', '').strip()
    sort  = request.GET.get('sort', '')

    if query:
        scams = scams.filter(
            Q(scam_type__icontains=query)     |
            Q(title__icontains=query)         |
            Q(location__icontains=query)      |
            Q(description__icontains=query)   |
            Q(platform__icontains=query)      |
            Q(scammer_upi__icontains=query)
        )

    if sort == 'newest':
        scams = scams.order_by('-date_reported')
    elif sort == 'oldest':
        scams = scams.order_by('incident_date')
    elif sort == 'critical':
        scams = scams.order_by('-severity', '-amount_lost')
    else:
        scams = scams.order_by('-date_reported')

    return render(request, 'reports/explore.html', {'scams': scams, 'query': query})


def scam_details_view(request, scam_id):
    scam = get_object_or_404(
        ScamReport.objects.filter(status__in=['pending', 'verified', 'escalated']),
        id=scam_id
    )
    return render(request, 'reports/scam_details.html', {'scam': scam})


def track_report(request):
    """Let users track their report using the reference number."""
    ref    = request.GET.get('ref', '').strip().upper()
    report = None
    error  = None

    if ref:
        try:
            report = ScamReport.objects.get(reference_number=ref)
        except ScamReport.DoesNotExist:
            error = f"No report found with reference number '{ref}'."

    return render(request, 'reports/track.html', {
        'report': report,
        'ref':    ref,
        'error':  error,
    })


@require_GET
def heatmap_data(request):
    location_counts = (
        ScamReport.objects
        .filter(status__in=['pending', 'verified', 'escalated'])
        .values('latitude', 'longitude')
        .annotate(count=Count('id'))
    )
    data = [
        [loc['latitude'], loc['longitude'], loc['count']]
        for loc in location_counts
        if loc['latitude'] and loc['longitude']
    ]
    return JsonResponse({'heatmap_data': data})