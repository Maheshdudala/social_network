from django.urls import path
from .views import RegisterView, LoginView, UserSearchView, FriendRequestView, \
    PendingFriendRequestsView, UserActivityView, ManageFriendRequestView, ProfileView, ProfileUpdateView, \
    FriendsListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/update/', ProfileUpdateView.as_view(), name='profile-update'),
    path('profile/<int:user_id>/', ProfileView.as_view(), name='profile-view'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('friend-request/', FriendRequestView.as_view(), name='friend-request'),
    path('friend-request/<int:request_id>/manage/', ManageFriendRequestView.as_view(), name='manage-friend-request'),
    path('friends/', FriendsListView.as_view(), name='friends-list'),
    path('pending-requests/', PendingFriendRequestsView.as_view(), name='pending-requests'),
    path('activities/', UserActivityView.as_view(), name='user-activities'),  # New route for user activities
]
