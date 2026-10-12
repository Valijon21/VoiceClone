"""Custom User model for VoiceClone identity and RBAC."""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Primary user identity with UUID identifier, email verification, and usage tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="Email Address")
    is_verified = models.BooleanField(
        default=False, help_text="Email ownership verification status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username} <{self.email}>"
