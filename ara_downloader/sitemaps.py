from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        # أسماء الـ urls اللي عايزها تظهر في السايت ماب
        return ["index", "fetch_info"]

    def location(self, item):
        return reverse(item)
