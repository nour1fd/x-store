from rest_framework import serializers
from .models import Review
from django.contrib.contenttypes.models import ContentType


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    content_type = serializers.SlugRelatedField(
        queryset=ContentType.objects.all(), slug_field="model"
    )
    object_name = serializers.SerializerMethodField()
    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        error_messages={
            "min_value": "Rating must be at least 1.",
            "max_value": "Rating cannot be more than 5.",
        },
    )

    class Meta:
        model = Review
        fields = [
            "id",
            "rating",
            "comment",
            "created_at",
            "content_type",
            "object_id",
            "object_name", "user"
        ]
        read_only_fields = ["id", "created_at"]

    def get_content_object_type(self, obj):
        return obj.content_type.model  # returns 'product', 'blogpost', etc.

    def get_object_name(self, obj):
        return str(obj.content_object)
