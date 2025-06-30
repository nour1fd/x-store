from rest_framework.permissions import BasePermission
class IsUserSelf(BasePermission):    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsAdminOrReadOnly(BasePermission):    
    def has_permission(self, request, view):
        if request.method in ["GET"]:
            return True  # Allow GET requests for all users
        return request.user.is_staff  # Allow only admin users to modify
