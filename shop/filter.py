import django_filters  # Ensure this line is present
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Order

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    category = django_filters.CharFilter(field_name="category__name", lookup_expr="iexact")  # Case-insensitive category filter
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")  # Partial match search

    class Meta:
        model = Product
        fields = ["min_price", "max_price", "category", "name"]


class OrderFilter(django_filters.FilterSet):
    status = django_filters.ChoiceFilter(choices=Order.STATUS_CHOICES)
    created_at = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Order
        fields = ["status", "created_at"]
