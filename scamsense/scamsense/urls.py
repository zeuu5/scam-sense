from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from reports import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home / dashboard
    path('', views.home, name='home'),

    # Multi-step report wizard
    path('report/',            views.report_scam, name='report_scam'),
    path('report/<int:step>/', views.report_scam, name='report_scam_step'),

    # Explore all reports
    path('explore/', views.explore_scams, name='explore_scams'),

    # Individual report detail
    path('scam/<int:scam_id>/', views.scam_details_view, name='scam_details'),

    # Live heatmap data (JSON endpoint)
    path('heatmap-data/', views.heatmap_data, name='heatmap_data'),

    # Track a report by reference number e.g. /track/?ref=SS-00423
    path('track/', views.track_report, name='track_report'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)