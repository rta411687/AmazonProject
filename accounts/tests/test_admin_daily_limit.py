from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from commission.models import CommissionSetting


class AdminDailyLimitTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # create an admin and a regular user
        self.admin = User.objects.create_user(username='admin1', password='pass', role='admin')
        self.user = User.objects.create_user(username='user1', password='pass', role='user')
        self.client = Client()
        self.client.force_login(self.admin)

    def test_admin_can_set_daily_limit(self):
        url = reverse('accounts:admin_dashboard')
        data = {
            'action': 'set_daily_limit',
            'user_id': str(self.user.id),
            'daily_limit': '40',
        }
        response = self.client.post(url, data, follow=True)

        # Ensure CommissionSetting created and value set
        cs = CommissionSetting.objects.filter(user=self.user).first()
        self.assertIsNotNone(cs, "CommissionSetting should be created for the user")
        self.assertEqual(cs.daily_task_limit, 40)
