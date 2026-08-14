from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model providing ``created_at`` and ``updated_at``."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
