import uuid
from django.db import models

class User(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('analyst', 'Analyst')]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    github_id = models.CharField(max_length=100, unique=True)
    username = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='analyst')
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username