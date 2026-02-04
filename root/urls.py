"""
URL configuration for root project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# root/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os
from django.contrib.sitemaps.views import sitemap
from speedtest.sitemaps import StaticViewSitemap
from django.http import HttpResponse

def google_verify(request):
    file_path = os.path.join(settings.BASE_DIR, "google65b25acc2d882302.html")
    with open(file_path, "r") as f:
        return HttpResponse(f.read(), content_type="text/html")

def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Allow: /",
        "Sitemap: https://netspeed-world.onrender.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('speedtest.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

urlpatterns += [
    path("robots.txt", robots_txt),
]


urlpatterns += [
    path(
        "google65b25acc2d882302.html",
        google_verify
    ),
]

sitemaps = {
    'static': StaticViewSitemap,
}

urlpatterns += [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
]

# Media files (Development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom error handlers
handler404 = 'speedtest.views.custom_404'
handler500 = 'speedtest.views.custom_500'

