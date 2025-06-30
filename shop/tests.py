from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user(self):
        data = {
            "username": "john",
            "email": "john@example.com",
            "password": "test1234",
            "profile": {
                "phone": "1234567890",
                "address": "123 Street"
            }
        }
        response = self.client.post("/user_create", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["username"], "john")
   
   
    def test_get_user_details(self):
        user = User.objects.create_user(username="testuser", password="secret")
        self.client.force_authenticate(user=user)

        response = self.client.get(f"/user_detail/{user.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], "testuser")
 
    def test_create_product(self):
        user = User.objects.create_user(username="admin", password="admin123", is_staff=True)
        self.client.force_authenticate(user=user)

        category_data = {"name": "electronics"}
        product_data = {
            "name": "Laptop",
            "description": "Fast laptop",
            "price": 999.99,
            "stock": 10,
            "category": category_data
        }

        response = self.client.post("/product_create", product_data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "Laptop")
