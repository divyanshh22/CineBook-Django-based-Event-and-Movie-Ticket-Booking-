from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class AuthFlowTests(APITestCase):
    """End-to-end tests for the session + CSRF based auth flow."""

    def setUp(self):
        self.client = APIClient()
        self.password = "Str0ng!Pass123"

    def create_user(self, **kwargs):
        defaults = {
            "username": "testuser",
            "email": "test@example.com",
            "password": self.password,
        }
        defaults.update(kwargs)
        return User.objects.create_user(**defaults)

    def register_payload(self, **overrides):
        payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": self.password,
            "password_confirm": self.password,
            "first_name": "New",
            "last_name": "User",
        }
        payload.update(overrides)
        return payload

    # ------------------------------------------------------------------ #
    # Registration
    # ------------------------------------------------------------------ #
    def test_register_creates_user_and_logs_in(self):
        response = self.client.post("/api/auth/register/", self.register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password(self.password))
        # Session should be established
        session = self.client.get("/api/auth/session/")
        self.assertTrue(session.data["authenticated"])

    def test_register_rejects_mismatched_passwords(self):
        payload = self.register_payload(password_confirm="Different123!")
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_rejects_duplicate_username(self):
        self.create_user()
        payload = self.register_payload(username="testuser", email="other@example.com")
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_duplicate_email(self):
        self.create_user(username="someone", email="new@example.com")
        response = self.client.post("/api/auth/register/", self.register_payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------ #
    # Login / logout / session
    # ------------------------------------------------------------------ #
    def test_login_with_username(self):
        self.create_user()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.get("/api/auth/session/")
        self.assertTrue(session.data["authenticated"])
        self.assertEqual(session.data["user"]["username"], "testuser")

    def test_login_with_email(self):
        self.create_user()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "test@example.com", "password": self.password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_with_wrong_password(self):
        self.create_user()
        response = self.client.post(
            "/api/auth/login/",
            {"username": "testuser", "password": "WrongPass123!"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_destroys_session(self):
        self.create_user()
        self.client.login(username="testuser", password=self.password)
        response = self.client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session = self.client.get("/api/auth/session/")
        self.assertFalse(session.data["authenticated"])

    def test_session_returns_null_user_when_anonymous(self):
        session = self.client.get("/api/auth/session/")
        self.assertFalse(session.data["authenticated"])
        self.assertIsNone(session.data["user"])

    # ------------------------------------------------------------------ #
    # Profile
    # ------------------------------------------------------------------ #
    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_returns_profile_when_authenticated(self):
        user = self.create_user()
        self.client.login(username=user.username, password=self.password)
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_me_patch_updates_profile(self):
        user = self.create_user()
        self.client.login(username=user.username, password=self.password)
        response = self.client.patch(
            "/api/auth/me/",
            {"phone_number": "+91 9999999999", "first_name": "Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.phone_number, "+91 9999999999")
        self.assertEqual(user.first_name, "Updated")

    # ------------------------------------------------------------------ #
    # Password change
    # ------------------------------------------------------------------ #
    def test_password_change(self):
        user = self.create_user()
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(
            "/api/auth/password/change/",
            {
                "old_password": self.password,
                "new_password": "NewStr0ng!Pass456",
                "new_password_confirm": "NewStr0ng!Pass456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStr0ng!Pass456"))

    def test_password_change_rejects_wrong_old_password(self):
        user = self.create_user()
        self.client.login(username=user.username, password=self.password)
        response = self.client.post(
            "/api/auth/password/change/",
            {
                "old_password": "TotallyWrong123!",
                "new_password": "NewStr0ng!Pass456",
                "new_password_confirm": "NewStr0ng!Pass456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------ #
    # Password reset
    # ------------------------------------------------------------------ #
    def test_password_reset_full_flow(self):
        user = self.create_user()
        request_response = self.client.post(
            "/api/auth/password/reset/", {"email": user.email}, format="json"
        )
        self.assertEqual(request_response.status_code, status.HTTP_200_OK)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uidb64": uidb64,
                "token": token,
                "new_password": "ResetPass!789",
                "new_password_confirm": "ResetPass!789",
            },
            format="json",
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("ResetPass!789"))

    def test_password_reset_confirm_rejects_bad_token(self):
        user = self.create_user()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uidb64": uidb64,
                "token": "bad-token",
                "new_password": "ResetPass!789",
                "new_password_confirm": "ResetPass!789",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_rejects_unknown_user(self):
        response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uidb64": urlsafe_base64_encode(force_bytes(99999)),
                "token": "whatever",
                "new_password": "ResetPass!789",
                "new_password_confirm": "ResetPass!789",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CsrfEnforcementTests(APITestCase):
    """CSRF is enforced for session-authenticated unsafe requests."""

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)

    def test_unsafe_request_without_csrf_token_is_rejected(self):
        User.objects.create_user(username="csrfuser", email="csrf@example.com", password="Str0ng!Pass123")
        self.csrf_client.force_login(User.objects.get(username="csrfuser"))
        response = self.csrf_client.post("/api/auth/logout/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unsafe_request_with_csrf_token_succeeds(self):
        User.objects.create_user(username="csrfuser", email="csrf@example.com", password="Str0ng!Pass123")
        self.csrf_client.force_login(User.objects.get(username="csrfuser"))
        # Fetch the CSRF token cookie first
        self.csrf_client.get("/api/auth/csrf/")
        csrf_token = self.csrf_client.cookies.get("csrftoken").value
        response = self.csrf_client.post(
            "/api/auth/logout/", HTTP_X_CSRFTOKEN=csrf_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
