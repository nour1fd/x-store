from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews') 
    rating = models.PositiveIntegerField()  # Example: 1 to 5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic Relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)  # Reference model type
    object_id = models.PositiveIntegerField()  # Reference model ID
    content_object = GenericForeignKey("content_type", "object_id")  # The actual object

    def __str__(self):
        return f"{self.id} - {self.rating}"
