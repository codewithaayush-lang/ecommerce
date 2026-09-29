"""Serializers for registration and user representation.

Django's built-in User model is used unchanged. Email uniqueness is enforced
here rather than by a custom user model, so the stock auth model is untouched.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation. Never includes password data."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Creates a user from username, email and a validated password."""

    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
        trim_whitespace=False,
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_email(self, value):
        """The built-in User model does not enforce unique emails."""
        email = User.objects.filter(email__iexact=value).first()
        if email is not None:
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_password(self, value):
        """Apply Django's configured AUTH_PASSWORD_VALIDATORS."""
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
