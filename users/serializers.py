from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

from users.models import UserActivity, FriendRequest, Profile

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['description','sensitive_info']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'name','email', 'role']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'name', 'role']  # Include name

    def create(self, validated_data):
        # Create the user with a name
        user = User(
            email=validated_data['email'],
            name=validated_data['name'],
            role=validated_data.get('role', 'read')  # Default to 'read' role
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class FriendRequestSerializer(serializers.ModelSerializer):
    sender = UserSerializer()  # Assuming you want to include sender details

    class Meta:
        model = FriendRequest
        fields = ['id', 'sender', 'created_at', 'status']


User = get_user_model()

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        # Convert email to lowercase to ensure case-insensitive login
        email = data.get("email", "").lower()
        password = data.get("password", "")

        # Authenticate the user using email and password
        user = authenticate(username=email, password=password)

        if user is None:
            raise serializers.ValidationError(
                {"non_field_errors":"Invalid credentials"}
            )

        if not user.is_active:
            raise serializers.ValidationError(
                {"non_field_errors": "User account is disabled"}
            )

        return user
class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'activity', 'timestamp']
        read_only_fields = ['user', 'timestamp']
