from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = "daily"

    def items(self):
        return ["index", "fetch_info"]

    def location(self, item):
        # نخلي الروابط https بدل http
        return "https://aratiktok.up.railway.app" + reverse(item)
