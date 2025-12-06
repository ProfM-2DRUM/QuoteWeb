from django.db import models
from django.utils import timezone

class Quote(models.Model):
    text = models.TextField(max_length=1000, help_text='The quote text')
    author = models.CharField(max_length=200, help_text='The author of the quote')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'"{self.text[:50]}..." - {self.author}'
