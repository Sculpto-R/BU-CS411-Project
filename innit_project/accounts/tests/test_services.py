from django.test import TestCase
from django.contrib.auth.models import User
from ..models import Profile
from ..services.scraper import fetch_events_for_preferences

class ScraperServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="t1", password="pass")
        # ensure profile exists
        self.profile = self.user.profile
        self.profile.presets = ['party', 'concert']
        self.profile.custom_preferences = ['indie']
        self.profile.save()

    def test_export_preferences(self):
        prefs = self.profile.export_preferences()
        self.assertIn('party', prefs)
        self.assertIn('concert', prefs)
        self.assertIn('indie', prefs)
        self.assertIsInstance(prefs, list)

    def test_fetch_events_placeholder(self):
        events = fetch_events_for_preferences(self.profile)
        self.assertIsInstance(events, list)
        self.assertGreaterEqual(len(events), 1)
        ev = events[0]
        self.assertIn('title', ev)
        self.assertIn('lat', ev)
        self.assertIn('lon', ev)
