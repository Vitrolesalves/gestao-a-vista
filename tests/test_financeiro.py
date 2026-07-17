import os
import json
import django
from django.test import TestCase, Client
from django.urls import reverse
from Gestao_a_Vista.models import CustomUser

class FinanceiroTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create an administrator
        self.admin = CustomUser.objects.create_user(
            username="test_admin",
            password="testpassword",
            email="test_admin@example.com",
            name="Test Admin",
            role="administrador"
        )
        self.admin.page_permissions = self.admin.get_default_permissions()
        self.admin.save()

        # Create a user without permission
        self.ordinary_user = CustomUser.objects.create_user(
            username="ordinary_user",
            password="testpassword",
            email="ordinary@example.com",
            name="Ordinary User",
            role="operador"
        )
        self.ordinary_user.page_permissions = {}
        self.ordinary_user.save()

    def test_anonymous_access_redirects(self):
        # Anonymous user should be redirected to login
        response = self.client.get(reverse("gestao_a_vista:financeiro"))
        self.assertEqual(response.status_code, 302)

    def test_user_without_permission_denied(self):
        self.client.login(username="ordinary_user", password="testpassword")
        response = self.client.get(reverse("gestao_a_vista:financeiro"))
        self.assertEqual(response.status_code, 403)

    def test_admin_access_allowed(self):
        self.client.login(username="test_admin", password="testpassword")
        response = self.client.get(reverse("gestao_a_vista:financeiro"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Painel Financeiro")

    def test_api_data_endpoint(self):
        self.client.login(username="test_admin", password="testpassword")
        response = self.client.post(
            reverse("gestao_a_vista:financeiro_api_data"),
            data=json.dumps({
                "meses": [],
                "alertas": []
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify JSON keys structure
        self.assertIn("kpis", data)
        self.assertIn("closing_kpis", data)
        self.assertIn("filter_options", data)
        self.assertIn("alert_counts", data)
        self.assertIn("charts", data)
        self.assertIn("tables", data)

    def test_api_chat_endpoint(self):
        self.client.login(username="test_admin", password="testpassword")
        response = self.client.post(
            reverse("gestao_a_vista:financeiro_api_chat"),
            data=json.dumps({
                "prompt": "Qual o saldo atual da carteira?",
                "history": [],
                "answer_mode": "auto",
                "filters": {}
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)

    def test_api_email_endpoint(self):
        self.client.login(username="test_admin", password="testpassword")
        response = self.client.post(
            reverse("gestao_a_vista:financeiro_api_email"),
            data=json.dumps({
                "filters": {}
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("html", data)
