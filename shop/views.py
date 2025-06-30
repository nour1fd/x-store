from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)

from rest_framework import generics, mixins
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import AnonRateThrottle

from rest_framework.decorators import api_view, permission_classes, throttle_classes


from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from .permissions import IsAdminOrReadOnly, IsUserSelf
from .filter import ProductFilter
from .models import Category, Product, Cart, Order
from .serializer import (
    UserSerializer,
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
    OrderSerializer,
)


# Create your views here.


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def user_list_create(request):
    if request.method == "GET":
        authentication_classes([JWTAuthentication])
        permission_classes([IsAuthenticated])

        users = User.objects.select_related("profile").all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    elif request.method == "POST":

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate JWT tokens for the newly created user
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            return Response(
                {
                    "message": "Data received successfully",
                    "data": serializer.data,
                    "access_token": access_token,
                    "refresh_token": str(refresh),
                },
                status=201,
            )
        return Response(serializer.errors, status=400)
    return Response({"message": "Invalid request"}, status=400)


class LoginThrottle(AnonRateThrottle):
    rate = "5/min"


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login_user(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Both username and password are required"}, status=400
        )

    try:
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login successful",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                }
            )
        return Response({"error": "Invalid username or password"}, status=400)

    except Exception as e:
        return Response(
            {"error": "Authentication failed"},
            status=500
        )

@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsUserSelf])
def user_detail(request, user_id):
    try:
        user = get_object_or_404(User, id=user_id)

        # if request.user != user:
        #     return Response(
        #         {"error": "You are not allowed to update this profile."}, status=403
        #     )

        if request.method == "GET":
            serializer = UserSerializer(user)
            return Response(serializer.data)

        elif request.method == "PUT":
            serializer = UserSerializer(instance=user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "User updated successfully", "data": serializer.data},
                    status=200,
                )
            return Response(serializer.errors, status=400)

        elif request.method == "DELETE":
            user.delete()
            return Response(
                {"message": "User deleted successfully"},
                status=200,
            )
        return Response({"message": "Invalid request"}, status=400)
    except:
        print('An exception occurred')

@api_view(["GET", "POST"])
@permission_classes([IsAdminOrReadOnly])
def category_list(request):
    if request.method == "GET":
        categorys = Category.objects.all()
        serializer = CategorySerializer(categorys, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Data received successfully",
                    "data": serializer.data,
                },
                status=201,
            )
        return Response(serializer.errors, status=400)
    return Response({"message": "Invalid request"}, status=400)

# class CategoryView(
#     mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView
# ):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

#     def get(self, request, *args, **kwargs):
#         return self.list(request, *args, **kwargs)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAdminOrReadOnly])

def category_detail(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == "GET":
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = CategorySerializer(instance=category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category updated successfully", "data": serializer.data},
                status=200,
            )
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        category.delete()
        return Response(
            {"message": "Category deleted successfully"},
            status=204,
        )

# class CategoryDetailView(
#     mixins.RetrieveModelMixin,
#     mixins.UpdateModelMixin,
#     mixins.DestroyModelMixin,
#     generics.GenericAPIView,
# ):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer

#     def get(self, request, *args, **kwargs):
#         return self.retrieve(request, *args, **kwargs)

#     def put(self, request, *args, **kwargs):
#         return self.update(request, *args, **kwargs)

#     def delete(self, request, *args, **kwargs):
#         return self.destroy(request, *args, **kwargs)


# class CategoryDetailView(RetrieveUpdateDestroyAPIView):
#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#     permission_classes = [IsAdminOrReadOnly]

@api_view(["GET", "POST"])
@permission_classes([IsAdminOrReadOnly])
def product_create(request):
    if request.method == "GET":
        products = Product.objects.select_related("category")

        filterset = ProductFilter(request.GET, queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs

        search_query = request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        paginator = PageNumberPagination()
        paginator.page_size = 5
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = ProductSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)

    elif request.method == "POST":
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Data received successfully",
                    "data": serializer.data,
                },
                status=201,
            )
        return Response(serializer.errors, status=400)

    return Response({"message": "Invalid request"}, status=400)


@api_view(["GET", "DELETE", "PUT"])
@permission_classes([IsAdminOrReadOnly])
def product_detail(request, product_id):
    if request.method == "GET":
        product = Product.objects.select_related('category').get(id=product_id)
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    elif request.method == "PUT":
        if not product_id:
            return Response({"error": "product ID is required for update"}, status=400)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = ProductSerializer(
            instance=product, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "product updated successfully", "data": serializer.data},
                status=201,
            )
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        product = Product.objects.get(id=product_id)
        product.delete()
        return Response(
            {"message": "product deleted successfully"},
            status=200,
        )

    return Response(serializer.errors, status=400)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def cart_list_create(request):
    if request.method == "GET":
        carts = Cart.objects.select_related("user", "product").filter(user=request.user)
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)
    elif request.method == "POST":
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {
                    "message": "Data received successfully",
                    "data": serializer.data,
                },
                status=201,
            )

        return Response(serializer.errors, status=400)


@api_view(["GET", "DELETE", "PUT"])
@permission_classes([IsAuthenticated, IsUserSelf])
def cart_detail(request, cart_id):
    cart = get_object_or_404(Cart, id=cart_id)

    if cart.user != request.user:
        return Response(
            {"error": "You do not have permission to access this order"}, status=403
        )

    if request.method == "GET":
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = CartSerializer(instance=cart, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Cart updated successfully", "data": serializer.data},
                status=200,
            )
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        cart.delete()
        return Response(
            {"message": "Cart deleted successfully"},
            status=200,
        )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def order_create(request):
    if request.method == "GET":
        orders = Order.objects.filter(user=request.user).prefetch_related("items")
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        # new one
        cart_items = Cart.objects.filter(user=request.user)
        serializer = OrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"message": "Order created successfully", "data": serializer.data},
                status=201,
            )
        return Response(serializer.errors, status=400)

    return Response({"message": "Invalid request"}, status=400)


@api_view(["GET", "DELETE", "PUT"])
@permission_classes([IsAuthenticated, IsUserSelf])
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "GET":
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Order updated successfully", "data": serializer.data},
                status=200,
            )
        return Response(serializer.errors, status=400)

    elif request.method == "DELETE":
        order.delete()
        return Response({"message": "Order deleted successfully"}, status=200)
