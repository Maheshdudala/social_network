from rest_framework.permissions import BasePermission

class IsReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'read'

class IsWrite(BasePermission):
    def has_permission(self, request, view):
        return request.user.role in ['write', 'admin']

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'admin'
