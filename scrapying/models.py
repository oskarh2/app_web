import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MaxLengthValidator

class PageTracking(models.Model):
    # Status choices
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
    
    # Type choices
    class Type(models.TextChoices):
        CC = 'CC', 'CC'
        OTHER = 'OT', 'Other'
    
    # Kind choices
    class Kind(models.TextChoices):
        OP = 'OP', 'OP'
        OTHER = 'OT', 'Other'
    
    # Fields
    page = models.CharField(max_length=20, validators=[MinLengthValidator(1)])
    tracking_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=5, choices=Type.choices, default=Type.CC)
    kind = models.CharField(max_length=2, choices=Kind.choices, default=Kind.OP)
    steps = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_id = models.IntegerField(null=True, blank=True)  # Foreign key to usuarios(perfil_id)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'page_tracking'
        ordering = ['-created_at']
        verbose_name = 'Page Tracking'
        verbose_name_plural = 'Page Trackings'
        indexes = [
            models.Index(fields=['page']),
            models.Index(fields=['status']),
            models.Index(fields=['user_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.page} - {self.tracking_id} - {self.status}"
    
    def save(self, *args, **kwargs):
        # Auto-update updated_at on save
        self.updated_at = models.DateTimeField(auto_now=True)
        super().save(*args, **kwargs)
