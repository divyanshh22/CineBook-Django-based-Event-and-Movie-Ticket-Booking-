from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "phone_number", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "is_email_verified", "date_joined")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    ordering = ("-date_joined",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("CineBook profile", {"fields": ("phone_number", "avatar", "date_of_birth", "is_email_verified")}),
    )
