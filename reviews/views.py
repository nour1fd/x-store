from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from .models import Review
from .serializers import ReviewSerializer

from django.shortcuts import get_object_or_404
from shop.models import Product

# Product-specific review views
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_review_list_create(request, product_id):
    # Get the product
    product = get_object_or_404(Product, id=product_id)
    
    # Handle GET request
    if request.method == 'GET':
        content_type = ContentType.objects.get_for_model(Product)
        reviews = Review.objects.filter(
            content_type=content_type,
            object_id=product_id
        )
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    # Handle POST request
    elif request.method == 'POST':
        # Check for existing review
        content_type = ContentType.objects.get_for_model(Product)
        if Review.objects.filter(
            content_type=content_type,
            object_id=product_id,
            user=request.user
        ).exists():
            return Response(
                {"error": "You already reviewed this product"},
                status=status.HTTP_409_CONFLICT
            )
        
        # Create new review
        serializer = ReviewSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(
                content_type=content_type,
                object_id=product_id
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def product_review_detail(request, product_id, review_id):
    # Get review and verify product association
    content_type = ContentType.objects.get_for_model(Product)
    review = get_object_or_404(
        Review,
        id=review_id,
        content_type=content_type,
        object_id=product_id
    )
    
    # Ownership check
    if request.method in ['PUT', 'DELETE'] and review.user != request.user:
        return Response(
            {"error": "You don't own this review"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Handle GET
    if request.method == 'GET':
        serializer = ReviewSerializer(review)
        return Response(serializer.data)
    
    # Handle PUT
    elif request.method == 'PUT':
        serializer = ReviewSerializer(
            review, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle DELETE
    elif request.method == 'DELETE':
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from django.contrib.contenttypes.models import ContentType
# from .models import Review
# from .serializers import ReviewSerializer


# @api_view(["POST"])
# @permission_classes([IsAuthenticated])
# def add_review(request, model, object_id):
#     data = request.data.copy()
#     data["content_type"] = model.lower()
#     data["object_id"] = object_id

#     serializer = ReviewSerializer(data=data,context={'request': request})
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @permission_classes([IsAuthenticated])
# @api_view(["GET"])
# def get_reviews(request, model, object_id):
#     try:
#         content_type = ContentType.objects.get(model=model.lower())
#     except ContentType.DoesNotExist:
#         return Response(
#             {"error": "Invalid model name."}, status=status.HTTP_400_BAD_REQUEST
#         )

#     reviews = Review.objects.filter(content_type=content_type, object_id=object_id)
#     serializer = ReviewSerializer(reviews, many=True)
#     return Response(serializer.data)


# @api_view(["PUT", "DELETE"])
# @permission_classes([IsAuthenticated])
# def update_delete_review(request, review_id):
#     if review.user != request.user:
#         return Response(
#             {"error": "You don't own this review"}, 
#             status=status.HTTP_403_FORBIDDEN
#         )
#     try:
#         review = Review.objects.get(id=review_id)
#     except Review.DoesNotExist:
#         return Response(
#             {"error": "Review not found."}, status=status.HTTP_404_NOT_FOUND
#         )

#     if request.method == "PUT":
#         serializer = ReviewSerializer(review, data=request.data, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     elif request.method == "DELETE":
#         review.delete()
#         return Response(
#             {"message": "Review deleted successfully"},
#             status=status.HTTP_204_NO_CONTENT,
#         )
