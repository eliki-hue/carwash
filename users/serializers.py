from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User


# =====================================================
# CREATE USER
# =====================================================
class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
            "role",
        ]

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "Email already exists."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


# =====================================================
# UPDATE USER
# =====================================================
class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
        ]

    def validate_username(self, value):
        qs = User.objects.filter(
            username__iexact=value
        ).exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Username already exists."
            )

        return value

    def validate_email(self, value):
        if not value:
            return value

        qs = User.objects.filter(
            email__iexact=value
        ).exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError(
                "Email already exists."
            )

        return value


# =====================================================
# LOGIN
# =====================================================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )

        if not user:
            raise serializers.ValidationError(
                "Invalid username or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account has been deactivated."
            )

        attrs["user"] = user
        return attrs


# =====================================================
# USER LIST / DETAIL
# =====================================================
class UserSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "role",
            "is_active",
            "date_joined",
            "last_login",
        ]

    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username