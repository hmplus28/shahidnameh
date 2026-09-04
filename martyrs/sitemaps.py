from django.contrib.sitemaps import Sitemap

from .models import Martyr


class MartyrSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    protocol = None

    def items(self):
        return Martyr.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.6
    protocol = None

    def items(self):
        return ["martyrs:home", "martyrs:directory"]

    def location(self, item):
        from django.urls import reverse

        return reverse(item)


SITEMAPS = {
    "martyrs": MartyrSitemap,
    "static": StaticViewSitemap,
}
