"""Root URL configuration for the CineBook project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.schemas import get_schema_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("cinemas.urls")),
    path("api/", include("bookings.urls")),
    path("api/admin/", include("admin_panel.urls")),
    path(
        "api/schema/",
        get_schema_view(
            title="CineBook API",
            description="Movie and event ticket booking platform API.",
            version="1.0.0",
        ),
        name="api-schema",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
