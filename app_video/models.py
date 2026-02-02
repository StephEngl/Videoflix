from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Video(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail_url = models.URLField(max_length=500)
    category = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Videos"
        ordering = ['id']

    def __str__(self):
        return self.title