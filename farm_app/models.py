from django.db import models
from django.contrib.auth.models import User

class Crop(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('analyzed', 'Analyzed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crops')
    name = models.CharField(max_length=200)
    summary = models.TextField()
    image = models.ImageField(upload_to='crops/')
    s3_image_url = models.URLField(blank=True, null=True)
    analyzed_result = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    analyzed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"
