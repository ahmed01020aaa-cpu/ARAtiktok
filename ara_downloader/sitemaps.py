from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        # هنا بتحط أسماء الـ urls اللي عايزها تظهر في السايت ماب
        return ["index"]

    def location(self, item):
        # بيرجع المسار بتاع الـ url
        return reverse(item)
