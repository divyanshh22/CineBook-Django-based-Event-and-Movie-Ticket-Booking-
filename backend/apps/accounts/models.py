from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager so the email can be used alongside the username."""

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("The email address must be set")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """CineBook user.

    Extends Django's built-in user with a phone number, avatar and an
    email-verified flag. Username and email are both unique.
    """

    email = models.EmailField("email address", unique=True, db_index=True)
    phone_number = models.CharField(
        "phone number", max_length=15, blank=True, db_index=True
    )
    avatar = models.ImageField(
        "avatar", upload_to="avatars/", blank=True, null=True
    )
    date_of_birth = models.DateField("date of birth", blank=True, null=True)
    is_email_verified = models.BooleanField(
        "email verified", default=False
    )

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
        ]

    def __str__(self):
        return self.username

    @property
    def display_name(self) -> str:
        """A friendly name: first name or username."""
        return (self.get_full_name() or self.username) if (self.first_name or self.last_name) else self.username
