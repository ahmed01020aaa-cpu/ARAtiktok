from django.urls import path
from django.views.generic import RedirectView
from downloader import views
from  downloader.views import google_verification

urlpatterns = [
    # باقي المسارات...

    path(
        "google55e2cfdb79c0b019.html",
        google_verification,
        name="google_verification",
    ),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("api/fetch", views.fetch_info, name="fetch_info"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=False)),



    path(
        "google55e2cfdb79c0b019.html",
        google_verification,
        name="google_verification",
    ),
]
