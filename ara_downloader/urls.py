from django.urls import path
from django.views.generic import RedirectView
from django.contrib.sitemaps import views as sitemap_views
from django.http import HttpResponse

from downloader import views
from downloader.views import google_verification
from .sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}

# View مخصص للـ sitemap.xml
def sitemap_xml(request):
    response = sitemap_views.sitemap(request, {"sitemaps": sitemaps})
    response["Content-Type"] = "application/xml"
    # هنا بنغير الهيدر عشان يسمح بالفهرسة
    response["X-Robots-Tag"] = "all"
    return response

urlpatterns = [
    path("", views.index, name="index"),
    path("api/fetch", views.fetch_info, name="fetch_info"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=False)),

    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),  # استخدمنا الـ view الجديد هنا

    path("robots.txt", views.robots_txt),

    path(
        "google55e2cfdb79c0b019.html",
        google_verification,
        name="google_verification",
    ),
]
