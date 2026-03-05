from rest_framework.permissions import BasePermission
from apps.users.models import User


class IsPartner(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Roles.PARTNER


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Roles.CLIENT


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == User.Roles.ADMIN


class IsKYCParticipant(BasePermission):
    """
    Partner sees only his KYC
    Client sees only his KYC
    Admin sees all
    """

    def has_object_permission(self, request, view, obj):
        if request.user.role == User.Roles.ADMIN:
            return True

        if request.user.role == User.Roles.PARTNER:
            return obj.partner == request.user

        if request.user.role == User.Roles.CLIENT:
            return obj.client == request.user

        return False
