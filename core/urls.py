"""URL configuration for Videoflix project.

Main URL routing for the video streaming platform, including
authentication, video management, admin interface, and API documentation.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Background task monitoring
    path('django-rq/', include('django_rq.urls')),
    
    # API endpoints
    path('api/', include('app_auth.api.urls')),
    path('api/', include('app_video.api.urls')),

    # API documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
] 

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)