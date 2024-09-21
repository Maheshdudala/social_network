from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserActivitySerializer,
    FriendRequestSerializer,
    ProfileSerializer,
    UserSerializer
)
from .models import User, Profile, BlockedUser, FriendRequest, UserActivity


# Utility function to log activity
def log_activity(user, activity):
    UserActivity.objects.create(user=user, activity=activity)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            log_activity(serializer.instance, "User registered.")
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data
        refresh = RefreshToken.for_user(user)

        # Log the login activity
        log_activity(user, "User logged in.")

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class UserSearchPagination(PageNumberPagination):
    page_size = 10


@method_decorator(cache_page(60 * 1), name='dispatch')  # Cache for 15 minutes
class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination  # Paginate results, 10 per page

    def get_queryset(self):
        query = self.request.query_params.get('q', '')

        if query:
            # Search by email or name using case-insensitive matching
            return User.objects.filter(
                Q(email__icontains=query) |
                Q(name__icontains=query)
            ).distinct()
        return User.objects.none()  # Empty queryset if no query provided

@method_decorator(cache_page(60 * 5), name='get')  # Cache for 5 minutes
class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Fetch users who have accepted the friend request
        friend_requests = FriendRequest.objects.filter(
            (Q(sender=user) | Q(receiver=user)), status='accepted'
        )

        # Use a set to avoid duplicates
        friends = set()
        for request in friend_requests:
            if request.sender == user:
                friends.add(request.receiver)
            else:
                friends.add(request.sender)

        return friends


class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]  # Ensure only logged-in users can update
    serializer_class = ProfileSerializer

    def get_object(self):
        # Fetch the profile for the currently authenticated user
        return self.request.user.profile  # Assuming a OneToOne relationship between User and Profile

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        log_activity(request.user, "Profile updated.")
        return response


class ProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        profile_user_id = kwargs.get('user_id')  # Ensure this matches your URL pattern
        profile_user = get_object_or_404(User, id=profile_user_id)
        profile = get_object_or_404(Profile, user=profile_user)

        # Check if the requester is blocked by the profile owner
        if BlockedUser.objects.filter(blocker=profile_user, blocked=request.user).exists():
            return Response({"error": "You are blocked from viewing this profile."}, status=403)

        # Check if they are friends
        are_friends = FriendRequest.objects.filter(
            (Q(sender=profile_user, receiver=request.user) |
             Q(sender=request.user, receiver=profile_user)),
            status='accepted'
        ).exists()

        if not are_friends:
            # Log the profile view attempt
            log_activity(request.user, f"Attempted to view profile of {profile_user.name}.")

            # Notify profile_user about the view attempt
            log_activity(profile_user, f"{request.user.name} attempted to view your profile.")

            return Response({
                "user": profile_user.name,
                "description": profile.description,
                "message": "Sensitive information is hidden until friend request is accepted."
            }, status=200)

        # If they are friends, log and notify the profile view
        log_activity(request.user, f"Viewed profile of {profile_user.name}.")

        # Notify profile_user that their profile was viewed
        log_activity(profile_user, f"{request.user.name} viewed your profile.")

        return Response({
            "user": profile_user.name,
            "description": profile.description,
            "sensitive_info": profile.sensitive_info
        }, status=200)


class PendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return FriendRequest.objects.filter(receiver=user, status='pending')


class UserActivityView(generics.ListAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)


class FriendRequestThrottle(UserRateThrottle):
    rate = '3/min'


class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [FriendRequestThrottle]

    COOLDOWN_PERIOD = 24  # Cooldown period in hours

    @transaction.atomic  # Ensures that this block is executed atomically
    def post(self, request):
        sender = request.user
        receiver_id = request.data.get('user_id')

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the sender is blocked by the receiver
        if BlockedUser.objects.filter(blocker=receiver, blocked=sender).exists():
            return Response({"error": "You are blocked by this user."}, status=status.HTTP_403_FORBIDDEN)

        # Check if the receiver is blocked by the sender
        if BlockedUser.objects.filter(blocker=sender, blocked=receiver).exists():
            return Response({"error": "You have blocked this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a friend request has already been rejected and if the cooldown is still active
        rejected_request = FriendRequest.objects.filter(sender=sender, receiver=receiver, status='rejected').first()
        if rejected_request:
            cooldown_expires_at = rejected_request.updated_at + timedelta(hours=self.COOLDOWN_PERIOD)

            if timezone.now() < cooldown_expires_at:
                # Cooldown still in effect
                return Response({
                    "info": f"Friend request rejected. Cooldown period active until {cooldown_expires_at}."
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Cooldown period is over, user can send a new request
                rejected_request.delete()  # Optionally, delete the rejected request to allow a new one

        # Check if a friend request from the receiver to the sender is pending
        if FriendRequest.objects.filter(sender=receiver, receiver=sender, status='pending').exists():
            return Response({"error": "Friend request from this user is pending approval."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Optionally, check if they are already friends (status='accepted')
        if FriendRequest.objects.filter(
                Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender),
                status='accepted').exists():
            return Response({"error": "You are already friends with this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the new friend request
        friend_request = FriendRequest(sender=sender, receiver=receiver)
        friend_request.save()

        # Log the friend request
        log_activity(sender, f"Sent a friend request to {receiver.name}")
        log_activity(receiver, f"Received a friend request from {sender.name}")


        return Response({"message": "Friend request sent."}, status=status.HTTP_201_CREATED)


class ManageFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        request_id = self.kwargs.get('request_id')
        action = request.data.get('action')  # 'accept', 'reject', 'block', or 'unblock'

        # Check if the action is either block or unblock
        if action in ['block', 'unblock']:
            return self.handle_blocking_unblocking(request, action)

        # For 'accept' and 'reject' actions
        friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)

        if action == 'accept':
            return self.accept_request(friend_request)

        elif action == 'reject':
            return self.reject_request(friend_request)

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    def handle_blocking_unblocking(self, request, action):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'User ID required for this action'}, status=status.HTTP_400_BAD_REQUEST)

        target_user = get_object_or_404(User, id=user_id)
        user = request.user

        if action == 'block':
            BlockedUser.objects.get_or_create(blocker=user, blocked=target_user)
            log_activity(user, f"Blocked {target_user.name}")
            log_activity(target_user, f"You were Blocked by  {user.name}")
            return Response({'message': f'{target_user.name} has been blocked.'}, status=status.HTTP_200_OK)

        elif action == 'unblock':
            BlockedUser.objects.filter(blocker=user, blocked=target_user).delete()
            log_activity(user, f"Unblocked {target_user.name}")
            log_activity(target_user, f"Unblocked by {user.name}")
            return Response({'message': f'{target_user.name} has been unblocked.'}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    def accept_request(self, friend_request):
        friend_request.status = 'accepted'
        friend_request.save()

        log_activity(friend_request.receiver, f"Accepted friend request from {friend_request.sender.name}")
        log_activity(friend_request.sender, f"Friend request accepted by {friend_request.receiver.name}")

        return Response({"message": "Friend request accepted."}, status=status.HTTP_200_OK)

    def reject_request(self, friend_request):
        friend_request.status = 'rejected'
        friend_request.save()

        log_activity(friend_request.receiver, f"Rejected friend request from {friend_request.sender.name}")
        log_activity(friend_request.sender, f"Friend request rejected by {friend_request.receiver.name}")

        return Response({"message": "Friend request rejected."}, status=status.HTTP_200_OK)
