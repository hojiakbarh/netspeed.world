from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = "https"

    def items(self):
        return [
            "home",
            "network_issues",
            "about",
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        priorities = {
            "home": 1.0,
            "network_issues": 0.6,
            "about": 0.5,
        }
        return priorities.get(item, 0.5)

    def changefreq(self, item):
        freqs = {
            "home": "daily",
            "network_issues": "monthly",
            "about": "monthly",
        }
        return freqs.get(item, "monthly")
