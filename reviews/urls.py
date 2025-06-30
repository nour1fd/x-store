# from django.urls import path
# from .views import get_reviews, add_review, update_delete_review

# urlpatterns = [
#     path("<str:model>/<int:object_id>/add/", add_review),  # Add review
#     path("reviews/<str:model>/<int:object_id>/", get_reviews, name="review-list"),  # Get all reviews
#     path("<int:review_id>/", update_delete_review),  # Update review
# ]
from django.urls import path
from .views import product_review_list_create, product_review_detail

urlpatterns = [
    # Product-specific reviews
    path(
        "products/<int:product_id>/reviews/",
        product_review_list_create,
        name="product-review-list",
    ),
    path(
        "products/<int:product_id>/reviews/<int:review_id>/",
        product_review_detail,
        name="product-review-detail",
    ),
]
