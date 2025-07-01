from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.timezone import now
from datetime import timedelta
from django.db import transaction


from .models import UserProfile, Category, Product, Cart, Order, OrderItem


class UserProfileSerializer(serializers.ModelSerializer):

    profile_picture = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = UserProfile
        fields = ["phone", "address", "profile_picture"]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "profile"]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Custom user creation with profile and image handling"""
        profile_data = validated_data.pop("profile")
        profile_picture = profile_data.pop("profile_picture", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            # password=validated_data["password"],
        )
        user.set_password(password)
        user.save()
        profile = UserProfile.objects.create(user=user, **profile_data)
        if profile_picture:
            profile.profile_picture = profile_picture
            profile.save()

        return user

    def update(self, instance, validated_data):
        """Custom update logic for user & profile, including profile picture"""
        profile_data = validated_data.pop("profile", None)

        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()

        if profile_data:
            profile = instance.profile
            profile.phone = profile_data.get("phone", profile.phone)
            profile.address = profile_data.get("address", profile.address)

            if "profile_picture" in profile_data:
                profile.profile_picture = profile_data["profile_picture"]

            profile.save()

        return instance


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ["id", "created_at"]
    
    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be empty.")
        return value



class ProductSerializer(serializers.ModelSerializer):
    # category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "category",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        category_data = validated_data.pop("category")

        category= Category.objects.get_or_create(
            name=category_data["name"].lower()
        )

        product = Product.objects.create(category=category, **validated_data)
        return product

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.price = validated_data.get("price", instance.price)
        instance.stock = validated_data.get("stock", instance.stock)

        # if "category" in validated_data:
        #     instance.category = validated_data["category"]
        if "category" in validated_data:
            category_data = validated_data.pop("category")
            category, created = Category.objects.get_or_create(name=category_data["name"].lower())
            instance.category = category
            
            
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    # user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Cart
        fields = ["id", "product", "quantity", "added_at", "user"]
        read_only_fields = ["id", "added_at", "user"]


class OrderItemSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)  # Nested serializer for order items

    class Meta:
        model = Order
        fields = ["id", "total_price", "created_at", "status", "user", "items"]
        read_only_fields = ["id", "created_at", "total_price", "user"]

    def validate_status(self, value):
        allowed_transitions = {
            "Pending": ["Processing", "Cancelled"],
            "Processing": ["Shipped", "Cancelled"],
            "Shipped": ["Delivered"],
            "Delivered": [],  # No further changes allowed
            "Cancelled": [],  # Cannot update a canceled order
        }

        instance = getattr(self, "instance", None)
        if (
            instance
            and instance.status
            and value not in allowed_transitions[instance.status]
        ):
            raise serializers.ValidationError(
                f"Cannot change order status from {instance.status} to {value}."
            )

        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        # user = validated_data.get("user")

        # if not user:
        #     raise serializers.ValidationError(
        #         {"user": "User is required to create an order."}
        #     )

        with transaction.atomic():
            order = Order.objects.create(total_price=0, **validated_data)
            total_price = 0

            for item_data in items_data:
                product = item_data["product"]
                quantity = item_data["quantity"]

                if product.stock < quantity:
                    raise serializers.ValidationError(
                        f"Not enough stock for {product.name}."
                    )

                product.stock -= quantity
                product.save()

                price = product.price * quantity  # Add this
                order_item = OrderItem.objects.create(
                    order=order, product=product, quantity=quantity, price=price
                )
                total_price += order_item.price * order_item.quantity

            order.total_price = total_price
            order.save()

        return order

    def update(self, instance, validated_data):

        items_data = validated_data.pop("items", None)
        new_status = validated_data.get("status", instance.status)

        if (now() - instance.created_at) > timedelta(
            hours=24
        ) and new_status != instance.status:
            raise serializers.ValidationError(
                "Order cannot be updated after 24 hours."
            )

        if instance.status in ["Shipped", "Delivered"]:
            raise serializers.ValidationError(
                " Order cannot be updated after it has been shipped or delivered."
            )

        with transaction.atomic():
            if items_data is not None:
                existing_items = {
                    item.product.id: item for item in instance.items.all()
                }
                total_price = 0

                for item_data in items_data:
                    product = item_data["product"]
                    quantity = item_data["quantity"]

                    if product.stock < quantity:
                        raise serializers.ValidationError(
                            f" Not enough stock for {product.name}."
                        )
                    product.stock -= quantity

                    if product.id in existing_items:
                        order_item = existing_items[product.id]
                        order_item.quantity = quantity
                        order_item.price = product.price * quantity
                        order_item.save()
                    else:
                        order_item = OrderItem.objects.create(
                            order=instance,
                            product=product,
                            quantity=quantity,
                            price=product.price * quantity,
                        )

                    total_price += order_item.price

                for product_id in list(existing_items.keys()):
                    if product_id not in [item["product"].id for item in items_data]:
                        existing_items[product_id].delete()

                instance.total_price = total_price

            if new_status == "Cancelled" and instance.status != "Cancelled":
                for item in instance.items.all():
                    item.product.stock += item.quantity
                    item.product.save()

            instance.status = new_status
            instance.save()

        return instance
