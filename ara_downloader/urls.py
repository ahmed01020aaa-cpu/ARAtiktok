from django.urls import path
from django.views.generic import RedirectView
from django.contrib.sitemaps.views import sitemap

from downloader import views
from downloader.views import google_verification
from .sitemaps import StaticViewSitemap

sitemaps = {
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("", views.index, name="index"),
    path("api/fetch", views.fetch_info, name="fetch_info"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=False)),

    # السايت ماب
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    # الروبوتس
    path("robots.txt", views.robots_txt),

    path("google55e2cfdb79c0b019.html", google_verification, name="google_verification"),
]
