from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.decorators.http import require_GET
from django.contrib.sitemaps.views import sitemap
from speedtest.sitemaps import StaticViewSitemap
import os


# --- Google site verification ---
def google_verify(request):
    file_path = os.path.join(settings.BASE_DIR, "google65b25acc2d882302.html")
    with open(file_path, "r") as f:
        return HttpResponse(f.read(), content_type="text/html")


# --- robots.txt ---
def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Allow: /",
        "Sitemap: https://netspeed-world.onrender.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


# --- Sitemap (HEAD + GET safe for Googlebot) ---
sitemaps = {
    "static": StaticViewSitemap,
}


@require_GET
def sitemap_view(request):
    return sitemap(request, sitemaps=sitemaps)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("speedtest.urls")),
    path("ckeditor/", include("ckeditor_uploader.urls")),

    # SEO files
    path("robots.txt", robots_txt),
    path("sitemap.xml", sitemap_view),
    path("google65b25acc2d882302.html", google_verify),
]


# --- Static & Media (development only) ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# --- Custom error pages ---
handler404 = "speedtest.views.custom_404"
handler500 = "speedtest.views.custom_500"
