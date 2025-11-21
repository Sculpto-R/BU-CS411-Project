from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Profile
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


class AccountsFlowTests(TestCase):
    def setUp(self):
        # create user for login/edit tests
        self.user = User.objects.create_user(
            username="existing",
            email="exist@example.com",
            password="testpass123"
        )

    def test_full_registration_flow_creates_user_and_profile(self):
        client = self.client

        # Step 1: initialize session (GET)
        r1 = client.get(reverse('accounts:register_step1'))
        self.assertEqual(r1.status_code, 200)
        logger.info("Step 1 status: %s", r1.status_code)

        # Step 2: post account details
        r2 = client.post(reverse('accounts:register_step2'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'newuser@example.com',
            'password1': 'StrongPass!123',
            'password2': 'StrongPass!123',
        }, follow=True)
        logger.info("Step 2 status: %s, session: %s", r2.status_code, dict(client.session))
        self.assertIn(r2.status_code, (200, 302))

        # Step 3: post dob (18+)
        # use a DOB 20 years ago
        dob = date.today() - timedelta(days=365*20)
        r3 = client.post(reverse('accounts:register_step3'), {
            'date_of_birth': dob.isoformat()
        }, follow=True)
        logger.info("Step 3 status: %s, session: %s", r3.status_code, dict(client.session))
        self.assertIn(r3.status_code, (200, 302))

        # Step 4: preferences (choose one preset and one custom)
        r4 = client.post(reverse('accounts:register_step4'), {
            'presets': ['party'],
            'custom_preferences': 'hangout, coffee'
        }, follow=True)
        logger.info("Step 4 status: %s, session: %s", r4.status_code, dict(client.session))

        # After final step user should be created and be logged in
        self.assertEqual(User.objects.filter(username='newuser').exists(), True)
        new_user = User.objects.get(username='newuser')
        profile = Profile.objects.get(user=new_user)
        logger.info("Profile after registration: age_verified=%s, dob=%s, presets=%s, custom=%s", 
                    profile.age_verified, profile.date_of_birth, profile.presets, profile.custom_preferences)
        self.assertEqual(profile.age_verified, True)
        # check presets and custom preferences saved (depending on model type; we expect list-like)
        # If stored as list:
        if isinstance(profile.presets, (list, tuple)):
            self.assertIn('party', profile.presets)
        else:
            # fallback: if stored as string
            self.assertIn('party', str(profile.presets))

        # custom preferences
        if isinstance(profile.custom_preferences, (list, tuple)):
            self.assertIn('hangout', profile.custom_preferences)
        else:
            self.assertIn('hangout', str(profile.custom_preferences))

    def test_login_and_logout(self):
        client = self.client
        login_url = reverse('accounts:login')
        r = client.post(login_url, {'username': 'existing', 'password': 'testpass123'}, follow=True)
        self.assertTrue(r.context['user'].is_authenticated)

        # logout (POST)
        logout_url = reverse('accounts:logout')
        r_out = client.post(logout_url, follow=True)
        # client should be logged out
        self.assertFalse(r_out.context['user'].is_authenticated)

    def test_edit_account_updates_user_fields(self):
        client = self.client
        client.login(username='existing', password='testpass123')

        edit_url = reverse('accounts:edit_account')
        resp = client.post(edit_url, {
            'first_name': 'Changed',
            'last_name': 'Name',
            'email': 'changed@example.com',
            # include profile fields required by form
            'date_of_birth': (date.today() - timedelta(days=365*25)).isoformat(),
            'presets': [],
            'custom_preferences': ''
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        u = User.objects.get(username='existing')
        self.assertEqual(u.first_name, 'Changed')
        self.assertEqual(u.email, 'changed@example.com')

    def test_edit_preferences_saves_presets_and_custom(self):
        client = self.client
        client.login(username='existing', password='testpass123')

        edit_prefs_url = reverse('accounts:edit_preferences')
        resp = client.post(edit_prefs_url, {
            'presets': ['concert', 'club'],
            'custom_preferences': 'hangout, boardgames'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        # check that presets and custom saved
        if isinstance(profile.presets, (list, tuple)):
            self.assertIn('concert', profile.presets)
            self.assertIn('club', profile.presets)
        else:
            self.assertIn('concert', str(profile.presets))

        if isinstance(profile.custom_preferences, (list, tuple)):
            self.assertIn('hangout', profile.custom_preferences)
        else:
            self.assertIn('hangout', str(profile.custom_preferences))

    def test_password_change_view(self):
        client = self.client
        client.login(username='existing', password='testpass123')
        url = reverse('accounts:password_change')
        resp = client.post(url, {
            'old_password': 'testpass123',
            'new_password1': 'NewStrongPass!234',
            'new_password2': 'NewStrongPass!234',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        # attempt login with new password
        client.logout()
        logged_in = client.login(username='existing', password='NewStrongPass!234')
        self.assertTrue(logged_in)
