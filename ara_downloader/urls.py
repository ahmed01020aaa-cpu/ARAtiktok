from django.urls import path
from django.views.generic import RedirectView
from downloader import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/fetch", views.fetch_info, name="fetch_info"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.svg", permanent=False)),
]
