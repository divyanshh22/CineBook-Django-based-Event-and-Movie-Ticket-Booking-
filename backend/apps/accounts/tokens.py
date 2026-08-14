"""Password-reset token helpers built on Django's token generator."""

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


def get_reset_token(user) -> tuple[str, str]:
    """Return ``(uidb64, token)`` for a password-reset email link."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token


def build_reset_link(user, reset_base_url: str) -> str:
    """Build the full frontend URL for a password reset.

    ``reset_base_url`` typically comes from an env var, e.g.
    ``http://localhost:5173/reset-password``.
    """
    uidb64, token = get_reset_token(user)
    separator = "&" if "?" in reset_base_url else "?"
    return f"{reset_base_url}{separator}uid={uidb64}&token={token}"
