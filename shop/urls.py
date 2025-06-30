from django.urls import path
from . import views
from rest_framework_simplejwt.views import  TokenObtainPairView, TokenRefreshView,TokenVerifyView 
from reviews.views import add_review, get_reviews  # import from reviews app


urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    
    path("user_create", views.user_list_create, name="user_list_create"),
    path("login",  views.login_user, name="user-login"),
    path("user_detail/<int:user_id>", views.user_detail, name="user_detail"),
    
    path("category_list", views.category_list, name="category_list"),
    path("category_detail/<int:category_id>", views.category_detail, name="category_detail"),
    
    path("product_create", views.product_create, name="product_create"),
    path("product_detail/<int:product_id>", views.product_detail, name="product_detail"),

    path("cart_list_create", views.cart_list_create, name="cart_list_create"),
    path("cart_detail/<int:cart_id>", views.cart_detail, name="cart_detail"),

    path("order_create", views.order_create, name="order_create"),
    path("order_detail/<int:order_id>", views.order_detail, name="order_detail"),


    path("products/<int:object_id>/reviews/add/", add_review, name="product-review-add"),
    path("products/<int:object_id>/reviews/", get_reviews, name="product-review-list"),

    
]
